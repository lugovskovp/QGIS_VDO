import pytest   # type: ignore # noqa
# from unittest.mock import MagicMock
from pathlib import Path


from QGIS_VDO.vdo.datatypes import VDO_FILE, BLADDR
from QGIS_VDO.vdo.blocks import block_0x12
from QGIS_VDO.vdo.consts import struct_UINT
from QGIS_VDO.vdo.enums import BlockType


@pytest.mark.parametrize("invalid_addr", [
    None,                           # Аргумент None
    0x10,                           # Смещение не на начало настоящего блока
])
def test_get_block_returns_none_for_invalid_inputs(real_vdo_fixture, invalid_addr):
    """get_block возвращает None на некорректные смещения или None"""
    real_vdo, _ = real_vdo_fixture
    assert real_vdo.get_block(invalid_addr) is None


def test_get_block_returns_none_for_zero_bladdr(real_vdo_fixture):
    """get_block возвращает None, если у BLADDR взведен флаг isZero"""
    real_vdo, _ = real_vdo_fixture
    bla_zero = BLADDR(b'\x00' * 4, real_vdo)
    assert real_vdo.get_block(bla_zero) is None


def test_get_block_returns_none_out_of_file_bounds(real_vdo_fixture):
    """get_block возвращает None, если блок находится за пределами размера файла"""
    real_vdo, _ = real_vdo_fixture
    # Смещение гарантированно за пределами файла (0x11... в разы больше ваших размеров файлов)
    bla_out_of_bounds = BLADDR(b'\x11\x00\x02\x01')
    assert real_vdo.get_block(bla_out_of_bounds) is None


def test_get_block_raises_value_error_on_wrong_type(real_vdo_fixture):
    """get_block вызывает ValueError, если передан некорректный тип данных (str)"""
    real_vdo, _ = real_vdo_fixture
    with pytest.raises(ValueError, match="Неверный тип адреса"):
        real_vdo.get_block("strings not good choice here")


def test_get_block_successful_with_virtual_bladdr(real_vdo_fixture):
    """Успешное получение блока через виртуальный BLADDR"""
    real_vdo, expected = real_vdo_fixture
    bla = BLADDR(b'\x00\x00\x02\x01')
    
    block = real_vdo.get_block(bla)
    assert isinstance(block, expected["bl_201"])


def test_get_block_0x12_properties_and_types(real_vdo_fixture):
    """Проверка структуры, типов и repr() для считанного блока 0x12 (offset=0)"""
    real_vdo, expected = real_vdo_fixture
    
    bl_0x12 = real_vdo.get_block(0)
    
    assert isinstance(bl_0x12, block_0x12)
    assert isinstance(bl_0x12.bladdr_scales, BLADDR)
    assert repr(bl_0x12.area_A) == expected["bl_0x12.area_A"]


"""
Для проверки __slots__ в тестировании Python принято проверять два ключевых аспекта:
1. У экземпляра класса отсутствует атрибут __dict__ (это гарантирует, что память оптимизирована
    и динамически добавлять любые атрибуты нельзя).
2. Попытка записать произвольное («левое») свойство в объект вызывает исключение AttributeError.
"""


def test_vdo_file_has_no_dict(real_vdo_fixture):
    """Проверяет, что у класса VDO_FILE заблокирован __dict__ через __slots__"""
    real_vdo, _ = real_vdo_fixture
    
    # Успешно настроенный __slots__ полностью убирает __dict__ из объекта
    assert not hasattr(real_vdo, "__dict__")


def test_vdo_file_slots_prevent_dynamic_attributes(real_vdo_fixture):
    """Проверяет, что нельзя динамически добавить неперечисленный в __slots__ атрибут"""
    real_vdo, _ = real_vdo_fixture
    
    # При попытке создать новое свойство должно бросаться исключение AttributeError
    with pytest.raises(AttributeError):
        real_vdo.some_dynamic_random_attribute = "test_value"


@pytest.mark.parametrize("slot_name", [
    "file_path",
    "is_empty",
    "is_single",
    "filename",
    "_initialized",
    "dbrev",
    "segsize",
    "file_size",
])
def test_vdo_file_allowed_slots_exist(real_vdo_fixture, slot_name):
    """Проверяет, что все заявленные в __slots__ атрибуты доступны на объекте"""
    real_vdo, _ = real_vdo_fixture
    
    # Проверяем, что класс содержит описание слота, либо объект имеет этот атрибут
    assert slot_name in VDO_FILE.__slots__
    assert hasattr(real_vdo, slot_name)


def test_get_bladdr_with_int_argument(all_vdo_fixture):
    """get_bladdr корректно упаковывает int и возвращает BLADDR с привязанным vdo"""
    real_vdo, _ = all_vdo_fixture
    
    # Передаем целое число (например, 0x01020304)
    int_addr = 0x01020304
    res = real_vdo.get_bladdr(int_addr)
    
    # Проверяем, что вернулся именно объект класса BLADDR
    assert isinstance(res, BLADDR)
    
    # Проверяем, что в BLADDR передался правильный self (текущий vdo)
    assert getattr(res, "vdo", None) is real_vdo
    
    # Проверяем правильность упаковки struct_UINT (Big-Endian или Little-Endian)
    # Если struct_UINT пакует в Big-Endian (например, '>I'), то будет b'\x01\x02\x03\x04'
    assert res._raw == struct_UINT.pack(int_addr)


def test_get_bladdr_with_bladdr_argument(all_vdo_fixture):
    """get_bladdr корректно упаковывает int и возвращает BLADDR с привязанным vdo"""
    real_vdo, _ = all_vdo_fixture

    if real_vdo.filename == "carindb34_0h_6800h.bin":
        another_file = Path(__file__).parent.parent / 'fixtures' / "wrong_empty"
    else:
        another_file = Path(__file__).parent.parent / 'fixtures' / "carindb34_0h_6800h.bin"
    another_vdo = VDO_FILE(another_file)
    
    bladdr_addr_slf = BLADDR(struct_UINT.pack(0x01020304), real_vdo)
    bladdr_addr_ant = BLADDR(struct_UINT.pack(0x01020304), another_vdo)

    # Передаем bladdr (например, 0x01020304)
    res_slf = real_vdo.get_bladdr(bladdr_addr_slf)
    res_anth = real_vdo.get_bladdr(bladdr_addr_ant)
    
    # Проверяем, что вернулся именно объект класса BLADDR
    assert isinstance(res_slf, BLADDR)
    assert isinstance(res_anth, BLADDR)
    
    # Проверяем, что в BLADDR передался правильный self (текущий vdo)
    assert getattr(res_slf, "vdo", None) is real_vdo
    assert getattr(res_anth, "vdo", None) is real_vdo


def test_vdo_file_get_QGISvdoGroupName(all_vdo_fixture):
    """Проверка, правильно ли формируется имя корневой группы qgis"""
    vdo: VDO_FILE
    vdo, _ = all_vdo_fixture

    if vdo.is_empty:
        assert vdo.QGISvdoGroupName is None
    else:
        assert vdo.QGISvdoGroupName == f'fixtures_0x{vdo.file_size:X}'

# ==================================================================
#  chatGPT was here
# def test_get_block_fallback_to_block_base_when_type_unknown(real_vdo_fixture, monkeypatch):
    """
    Проверяет, что если тип блока отсутствует в KNOWN_BLOCKS
    метод корректно инициализирует и возвращает базовый класс block_base.
    """


class StubBLSTART:
    __slots__ = ("bladdr", "bltype")
    size = 16  # Имитируем переменную класса размера заголовка

    def __init__(self, bladdr):
        self.bladdr = bladdr
        self.bltype = BlockType.UNKNOWN                    # StubBLType(value=type_value)


@pytest.mark.slow
# 2. Пишем изолированный тест-кейс
def test_get_block_fallback_to_block_base_when_type_unknown(real_vdo_fixture, monkeypatch):
    """
    Проверяет, что если тип блока отсутствует в KNOWN_BLOCKS,
    метод корректно инициализирует и возвращает базовый класс block_base.
    Тест полностью совместим со __slots__ в BLSTART.
    """
    real_vdo, _ = real_vdo_fixture
    
    # Смещение, по которому будем имитировать чтение (например, 0)
    target_offset = 0
    # Гарантированно неизвестный тип блока (которого точно нет в KNOWN_BLOCKS)
    unknown_type = 0xff

    # 1. Создаем Stub, имитирующий заголовок BLSTART со слотами
    st_bladdr = BLADDR(b'\x00\x00\x00\x01', real_vdo)
    fake_head = StubBLSTART(st_bladdr)
    
    # 2. Создаем класс-фабрику, у которого есть атрибут size,
    # а при вызове он возвращает наш fake_head
    class FakeBLSTARTClass:
        size = StubBLSTART.size  # Сохраняем размер для успешного self.read(..., BLSTART.size)

        def __new__(cls, bytes_data, vdo_obj):
            return fake_head

    # 3. Подменяем оригинальный BLSTART на наш FakeBLSTARTClass
    # (Замените 'QGIS_VDO.vdo_file.BLSTART' на ваш реальный путь импорта)
    monkeypatch.setattr("QGIS_VDO.vdo.datatypes.BLSTART", FakeBLSTARTClass)
    
    # 4. Подменяем метод read у КЛАССА VDO_FILE, чтобы избежать ошибок teardown
    monkeypatch.setattr(VDO_FILE, "read", lambda vdo_self, offset, size: b"\x01" * StubBLSTART.size)

    # Вызываем тестируемый метод get_block
    block = real_vdo.get_block(target_offset)
    
    # --- ПРОВЕРКИ ---
    assert block is not None
    assert block.type == unknown_type
    assert block.type_name == "block_base"
    
    # Проверяем, что динамически загрузился именно базовый класс
    # (Замените путь импорта на ваш актуальный)
    from QGIS_VDO.vdo.block_base import block_base
    assert isinstance(block, block_base)
