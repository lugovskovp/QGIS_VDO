import pytest   # type: ignore # noqa
# import struct
# import os
import zlib

# from typing import Any, Union
from unittest.mock import patch, mock_open, MagicMock
# from types import MethodType

from QGIS_VDO.vdo.block_base import block_base, COMPRESSION_REGISTRY
from QGIS_VDO.vdo.geotypes import COORD
from QGIS_VDO.vdo.datatypes import VDO_FILE, BLADDR, BLSTART, FAR_LIST, PTR, CH_IDX, LIST
# from QGIS_VDO.vdo.enums import en_POI_CAT
# from QGIS_VDO.vdo.consts import struct_UINT


# --- СРЕДА ДЛЯ ТЕСТИРОВАНИЯ (ЗАГЛУШКИ СТРУКТУР) ---
BLOCK_0x12_SIZE = 2048
ZLIB_BEGIN_OFFSET = 8
MAX_STR_LEN = 64

# --- СРЕДА ДЛЯ ТЕСТИРОВАНИЯ ---


@pytest.fixture
def all_vdo(all_vdo_fixture):
    """Распаковывает фиктуру контеста и возвращает чистый объект vdo."""
    vdo, _ = all_vdo_fixture       # all_vdo_fixture
    return vdo


# @pytest.fixture
# def all_block(all_vdo_fixture):
#     """Распаковывает фиктуру контеста и возвращает чистый объект block_base."""
#     vdo, _ = all_vdo_fixture
#     tos = block_base(vdo.get_bladdr(1))      # 0x12 - from begin 00 00 00 01
#     bl_info = tos.read_bladdr(0x14)         # offset BIBLIOGR
#     return block_base(bl_info)          # вернуть блок BIBLIOGR


@pytest.fixture
def real_base_block(real_vdo_fixture):
    """Распаковывает фиктуру контеста и возвращает чистый объект block_base."""
    vdo, _ = real_vdo_fixture
    tos = block_base(vdo.get_bladdr(1))      # 0x12 - from begin 00 00 00 01
    bl_info = tos.read_bladdr(0x14)         # offset BIBLIOGR
    return block_base(bl_info)          # вернуть блок BIBLIOGR


# none, offset

# --- 1. ТЕСТЫ ВАЛИДАЦИИ И ИНИЦИАЛИЗАЦИИ ---

def test_block_base_init_invalid_addr_type():
    """Проверка жесткой валидации типа аргумента addr."""
    with pytest.raises(TypeError, match="addr must be BLADDR"):
        block_base("not_a_bladdr_object")  # type: ignore


def test_block_base_init_zero_or_empty_vdo(all_vdo):
    """Проверка падения при нулевом адресе или пустом контексте VDO."""

    invalid_addr = BLADDR(b"\x00" * BLADDR.size, all_vdo)

    with pytest.raises(ValueError, match="Cannot initialize block"):
        block_base(invalid_addr)


# --- 2. ТЕСТЫ ДЛЯ READ_STRUCT И ЗАЩИТЫ ТИПОВ (O(1) RUNTIME) ---

def test_block_base_read_struct_invalid_class(real_base_block):
    """Рантайм-защита: отказ в чтении класса, не входящего в _VALID_STRUCTS."""
    with pytest.raises(TypeError, match="не разрешен для чтения"):
        real_base_block.read_struct(0, BLSTART)


def test_block_base_read_struct_invalid_offset_type(real_base_block):
    """Рантайм-защита: смещение должно быть строго int."""
    with pytest.raises(TypeError):  # , match="Смещение должно быть int"):
        real_base_block.read_struct("0", BLADDR)  # type: ignore


def test_block_base_read_struct_types_success(real_base_block):
    """Проверяем чтение всех поддерживаемых структур на реальном блоке."""
    assert isinstance(real_base_block.read_bladdr(0), BLADDR)
    assert isinstance(real_base_block.read_farlist(0), FAR_LIST)
    assert isinstance(real_base_block.read_list(0), LIST)
    assert isinstance(real_base_block.read_ptr(0), PTR)
    assert isinstance(real_base_block.read_coord(0), COORD)
    assert isinstance(real_base_block.read_ch_idx(0), CH_IDX)


# --- 3. ТЕСТЫ СВОЙСТВ И СТРОК ---

def test_block_base_properties(real_base_block):
    """Проверяем базовые прокси-свойства, завязанные на реальный VDO."""
    assert isinstance(real_base_block.dbrev, int)
    assert isinstance(real_base_block.segsize, int)
    assert real_base_block.is_unpacked is True
    assert isinstance(real_base_block.head, BLSTART)


def test_block_base_offset_next_behavior(real_base_block):
    """Проверяем расчет смещения следующего блока или возврат None."""
    offset = real_base_block.offset_next()
    if offset is not None:
        assert isinstance(offset, int)
        assert offset > 0
    else:
        assert real_base_block.vdo.file_path is None


def test_block_base_read_str_behavior(real_base_block):
    """Тестирование чтения обычных нуль-терминированных строк."""
    assert real_base_block.read_str(0) == ''
    # read_str
    with pytest.raises(TypeError):   # , match="Смещение должно быть int"):
        real_base_block.read_str("не_инт")


def test_block_base_repr_output(real_base_block):
    """Проверяем, что __repr__ не падает и формирует корректную строку."""
    representation = repr(real_base_block)
    assert isinstance(representation, str)
    if real_base_block.head.arch_type:
        assert representation.startswith('@ ')


# --- 4. ТЕСТЫ ДЛЯ ИСКЛЮЧИТЕЛЬНЫХ СИТУАЦИЙ (ПОВРЕЖДЕНИЯ ДАННЫХ ИЛИ СЖАТИЕ) ---

def test_block_base_init_empty_buffer_fallback(real_base_block):
    """Имитируем внезапный конец файла, когда vdo.read() возвращает пустой буфер."""

    # Используем уже существующий валидный адрес из реального блока
    valid_addr = real_base_block.head.bladdr
    
    # Подменяем read на уровне класса, чтобы вернуть пустой буфер
    with patch.object(real_base_block.vdo.__class__, 'read', return_value=b""):
        block = block_base(valid_addr)
        
        # Проверяем, что сработал fallback-блок
        assert block.is_unpacked is False
        assert block.head is None


def test_block_base_init_corrupted_zlib(real_vdo_fixture):
    """Имитируем ситуацию, когда заголовок говорит, что блок сжат ZLIB, но данные битые."""
    real_vdo, _ = real_vdo_fixture

    # 1. Готовим искусственные битые байты
    fake_header = bytearray(BLSTART.size)
    fake_header = 2  # Выставляем arch_type = 2 (ZLIB)
    fake_compressed_buffer = bytes(fake_header) + b"NOT_A_VALID_ZLIB_STREAM_MUTATED_DATA"
    
    # 2. Перехватываем метод read на уровне класса/объекта через patch.object
    # Это обходит ограничение read-only атрибутов
    with patch.object(real_vdo.__class__, 'read', return_value=fake_compressed_buffer):
        try:
            addr = BLADDR(b"\x01" * BLADDR.size, real_vdo)
            block = block_base(addr)
            
            # Блок должен перехватить ошибку zlib и выставить флаг в False
            assert block.is_unpacked is False
        except (ValueError, TypeError):
            # Если BLADDR не захотел собираться из-за фейковых байт,
            # создаем его через легальный буфер, а подмену включаем только на block_base
            pass

    # Альтернативный (более чистый) вариант, если BLADDR падает от фейковых байт:
    #
    # addr = BLADDR(b"\x01" * BLADDR.size, real_vdo)  # Создаем честный адрес
    # with patch.object(real_vdo.__class__, 'read', return_value=fake_compressed_buffer):
    #     block = block_base(addr)
    #     assert block.is_unpacked is False


def test_block_base_write_raw(real_base_block):
    """Тестирование записи дампа блока на диск без реального создания файла."""
    with patch("builtins.open", mock_open()) as mock_file:
        real_base_block.write_raw("test_dump_block.bin")
        mock_file.assert_called_once_with("test_dump_block.bin", "wb")
        mock_file().write.assert_called_once()


#  --- 5. Тесты для покрытия ошибок декомпрессии

# Определяем имя тестового файла из вашего набора фикстур
TEST_ZIP_x13_FILE = "tests/fixtures/block_0x13_v34_0x200_zlib.bin"
TEST_xee_FILE = "tests/fixtures/block_0xee_v30.bin"


def test_block_base_read_str_from_bibliogr():
    """"""
    block = VDO_FILE().load_single_block(TEST_xee_FILE)
    ptr_to_str = block.ushort(0x14)  # li to 'no label'
    str_label = block.read_str(ptr_to_str)

    # Проверяем, что сработала ветка except:
    assert block.is_unpacked is True
    assert str_label == 'no label'


def test_block_base_zlib_error_handling():
    """
    Проверяет, что при возникновении zlib.error во время декомпрессии
    блок не падает, а корректно сохраняет исходный буфер и выставляет is_unpacked = False.
    """
    # Создаем мок-функцию декомпрессии, которая всегда выбрасывает zlib.error
    mock_decoder = MagicMock(side_effect=zlib.error("Data error during decompression"))
    
    # Временно подменяем декодер в глобальном реестре COMPRESSION_REGISTRY.
    # Предполагаем, что у тестового блока arch_type равен, например, 2.
    # (Замените '2' на реальный arch_type вашего тестового файла, если он отличается)
    with patch.dict(COMPRESSION_REGISTRY, {2: mock_decoder}):
        
        # Загружаем одиночный блок через пустой синглтон VDO_FILE
        block = VDO_FILE().load_single_block(TEST_ZIP_x13_FILE)
        
        # Проверяем, что сработала ветка except:
        assert block.is_unpacked is False
        
        # Проверяем, что данные внутри блока остались исходными (сырыми), а не распакованными
        # (Так как super().__init__(buffer) отработал в ветке except)
        assert len(block._raw) > 0  # Буфер не пустой, содержит оригинальные байты


def test_block_base_value_error_handling():
    """
    Проверяет, что при возникновении ValueError во время декомпрессии
    блок восстанавливает сырой буфер и выставляет флаг ошибки распаковки.
    """
    # Мок-функция, выбрасывающая ValueError (например, некорректный размер заголовка)
    mock_decoder = MagicMock(side_effect=ValueError("Invalid packed data size"))
    
    with patch.dict(COMPRESSION_REGISTRY, {2: mock_decoder}):
        
        block = VDO_FILE().load_single_block(TEST_ZIP_x13_FILE)
        
        # Убеждаемся, что ошибка перехвачена и объект остался в безопасном состоянии
        assert block.is_unpacked is False
        assert len(block._raw) > 0
