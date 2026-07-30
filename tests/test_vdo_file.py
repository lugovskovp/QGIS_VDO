import pytest   # type: ignore # noqa
import sys
import os
from types import ModuleType
from typing import Any
from pathlib import Path

# Импортируем тестируемый класс и функцию генерации словаря
from QGIS_VDO.vdo.datatypes import VDO_FILE, setup_known_types, KNOWN_BLOCKS, EMPTY_BUFFER, BLADDR
from QGIS_VDO.vdo.blocks import block_0x12, block_0x13, block_0x07


# --- Заглушки для сопутствующих классов (BLSTART и BLADDR) ---

class FakeBladdr:
    def __init__(self, offset: int) -> None:
        self.offset = offset
        self._raw = b'\x00\x00\x00\x01'
        
    @property
    def isZero(self) -> bool:
        return False


class FakeBltype:
    def __init__(self, value: int) -> None:
        self.value = value


class FakeBlstart:
    size = 8

    def __init__(self, buffer: bytes, vdo: Any) -> None:
        # Эмулируем, что заголовок вернул тип блока 0x0B и смещение 100
        self.bladdr = FakeBladdr(offset=100)
        self.bltype = FakeBltype(value=0x0B)


# --- Фейковый класс блока, который должен быть импортирован ---
class FakeBlock0x0B:
    __slots__ = ('bladdr', 'type', 'type_name')

    def __init__(self, bladdr: Any, *args: Any) -> None:
        self.bladdr = bladdr


def test_vdo_get_block_integration(tmp_path, monkeypatch):
    """Интеграционный тест метода get_block с учетом динамического словаря KNOWN_BLOCKS."""
    
    # Шаг 1: Создаем фейковую директорию blocks на диске для проверки setup_known_types
    fake_blocks_dir = tmp_path / "blocks"
    fake_blocks_dir.mkdir()
    
    # Создаем пустой файл блока, имитируя структуру плагина
    # Имя файла 'block_0x0B.py' парсится функцией в тип 11 (0x0B)
    fake_block_file = fake_blocks_dir / "block_0x0B.py"
    fake_block_file.write_text("# Fake block module content")

    # Шаг 2: Генерируем реальный KNOWN_BLOCKS на основе созданной временной папки
    real_generated_blocks = setup_known_types(blocks_dir=str(fake_blocks_dir))
    
    # Подменяем глобальный словарь KNOWN_BLOCKS в модуле на наш сгенерированный
    monkeypatch.setattr("QGIS_VDO.vdo.datatypes.KNOWN_BLOCKS", real_generated_blocks)
    
    # Проверяем, что шаг изоляции прошел успешно и тип 11 (0x0B) зарегистрирован
    assert 11 in real_generated_blocks
    assert real_generated_blocks[11] == "block_0x0B"

    # Шаг 3: Перехватываем динамический импорт importlib через sys.modules
    # Метод get_block выполняет относительный импорт. Вычисляем целевой абсолютный путь:
    target_module_path = "QGIS_VDO.vdo.blocks.block_0x0B"
    
    mock_module = ModuleType("block_0x0B")
    # Внутри модуля должен лежать класс, чье имя совпадает с именем файла (модуля)
    setattr(mock_module, "block_0x0B", FakeBlock0x0B)
    
    # Добавляем наш виртуальный модуль в кэш импорта Python
    monkeypatch.setitem(sys.modules, target_module_path, mock_module)

    # Шаг 4: Подменяем парсер заголовков BLSTART, чтобы не читать бинарник
    monkeypatch.setattr("QGIS_VDO.vdo.datatypes.BLSTART", FakeBlstart)
    monkeypatch.setattr("QGIS_VDO.vdo.datatypes.BLADDR", FakeBladdr)

    # Шаг 5: Инициализируем VDO_FILE и глушим дисковое чтение
    vdo = VDO_FILE()
    vdo.path = "dummy.vdo"
    monkeypatch.setattr(vdo, "read", lambda offset, size: b"\x00" * size)

    # Шаг 6: Вызываем get_block для адреса 100
    block_instance = vdo.get_block(100)

    # Шаг 7: Проверяем, что блок успешно создался, имеет нужный тип и метаданные
    assert block_instance is not None
    assert isinstance(block_instance, FakeBlock0x0B)
    assert block_instance.type == 11          # 0x0B в десятичной системе
    assert block_instance.type_name == "block_0x0B"
    assert block_instance.bladdr.offset == 100
    assert block_instance.bladdr.isZero is False


def test_vdo_files_init_wrong_path():
    """Проверка создания VDO_FILE с несуществующим путём"""
    vdo = VDO_FILE("bla-bla-bla")

    assert vdo.path is None


def test_vdo_files_read_from_empty():
    """Проверка чтения из пустого vdo"""
    vdo = VDO_FILE()

    assert vdo.read(10, 5) == EMPTY_BUFFER
    assert vdo.read(-10, 5) == EMPTY_BUFFER


def test_vdo_files_init_too_little_file():
    """Проверка создания VDO_FILE carindb_0h_1Fh.bin """
    FIXTURES_DIR = Path(__file__).parent
    too_little_file_path = FIXTURES_DIR / 'fixtures' / 'carindb_0h_1Fh.bin'
    vdo = VDO_FILE(too_little_file_path)

    assert vdo.path is None
    assert vdo.QGISvdoGroupName is None
    assert vdo.get_block(0) is None
    

# --------------------------------------------------------------
# Тестs на реальных fixtures
# Словарь ожидаемых значений прямо внутри файла с тестами
EXPECTED_VDO_METRICS = {"carindb30_0h_9000h.bin": {"dbrev": 30,
                                                   "segsize": 2048,
                                                   "file_size": 36864,
                                                   "bl_0x12.area_A": 'None',
                                                   "bl_201": block_0x07,
                                                   },
                        "carindb34_0h_6800h.bin": {"dbrev": 34,
                                                   "segsize": 2048,
                                                   "file_size": 0x6800,  # 0x6800,
                                                   "bl_0x12.area_A": '(41.264594N 12.107514E, 59.895456N 29.673966E)',
                                                   "bl_201": block_0x07,
                                                   },
                        "DB34_0h_3A01h.bin": {"dbrev": 34,
                                              "segsize": 512,
                                              "file_size": 0x3A01,  # реальный размер файла в байтах
                                              "bl_0x12.area_A": '(35.317104N 9.161808W, 70.479517N 93.151702E)',
                                              "bl_201": block_0x13,
                                              }
                        }


def test_get_block_with_unknown_type(real_vdo, monkeypatch):
    """
    Тест проверяет ветку else в get_block, когда считанный из фикстуры
    тип блока отсутствует в словаре KNOWN_BLOCKS.
    """
    test_addr = 0
    real_block_type = 0x12

    # самый первый блок по смещению 0 - тип блока 0x12, из фейкового словаря известных блоков
    monkeypatch.delitem(KNOWN_BLOCKS, real_block_type, raising=False)

    bl_instance = real_vdo.get_block(test_addr)

    # Блок должен создаться как базовый класс "block_base"
    assert bl_instance is not None
    assert bl_instance.type == real_block_type
    assert bl_instance.type_name == "block_base"
    
    # Проверяем, что имя класса соответствует базовому классу
    assert bl_instance.__class__.__name__ == "block_base"


def test_vdo_files_init_exists_fixture_files(bin_file_path):
    """ """
    # Проверка существования 3-х bin_file_path файлов
    vdo = VDO_FILE(bin_file_path)
    isinstance(vdo, VDO_FILE)
    assert vdo.path != ''

    # если виртуальный BLADDR - без vdo
    bla_zero = BLADDR(b'\x00' * 4)
    a = vdo.get_block(bla_zero)
    assert a is None


@pytest.mark.slow
def test_vdo_files_get_block(real_vdo):
    """ Проверка правильной  работы get_block"""
    assert real_vdo.get_block(None) is None

    # если виртуальный zero BLADDR - c vdo
    bla_zero = BLADDR(b'\x00' * 4, real_vdo)
    a = real_vdo.get_block(bla_zero)
    assert a is None

    # если указатель не на начало настоящего блока
    a = real_vdo.get_block(0x10)
    assert a is None

    # если аргумент не гото типа
    with pytest.raises(ValueError):
        real_vdo.get_block("strings not good choice here")

    # ------------------------------------------
    # Получаем эталонный набор для текущего файла
    filename = os.path.basename(real_vdo.path)
    expected = EXPECTED_VDO_METRICS[filename]

    # если виртуальный BLADDR - без vdo
    bla = BLADDR(b'\x00\x00\x02\x01')
    a = real_vdo.get_block(bla)
    assert isinstance(a, expected["bl_201"])

    # если блок за пределами файла
    bla = BLADDR(b'\x11\x00\x02\x01')
    a = real_vdo.get_block(bla)
    assert a is None

    #
    bl_0x12 = real_vdo.get_block(0)
    assert isinstance(bl_0x12, block_0x12)
    bla_0x07 = bl_0x12.bladdr_scales
    
    assert bl_0x12.area_A.__repr__() == expected["bl_0x12.area_A"]
    assert isinstance(bla_0x07, BLADDR)


@pytest.mark.slow
def test_vdo_files_expected_dbrev(real_vdo):
    """ При инициализации правильно считывается версия БД - dbrev """
    # Извлекаем чистое имя файла из пути (например, 'DB34_0h_3A01h.bin')
    filename = os.path.basename(real_vdo.path)
    # Получаем эталонный набор для текущего файла
    expected = EXPECTED_VDO_METRICS[filename]

    assert real_vdo.dbrev == expected["dbrev"]


@pytest.mark.slow
def test_vdo_files_expected_segsize(real_vdo):
    """ При инициализации правильно считывается размеры сегмента """
    # Извлекаем чистое имя файла из пути (например, 'DB34_0h_3A01h.bin')
    filename = os.path.basename(real_vdo.path)
    expected = EXPECTED_VDO_METRICS[filename]

    assert real_vdo.segsize == expected["segsize"]


@pytest.mark.slow
def test_vdo_files_expected_size(real_vdo):
    """ При инициализации правильно считывается размер файла и работает QGISvdoGroupName"""
    # Извлекаем чистое имя файла из пути (например, 'DB34_0h_3A01h.bin')
    filename = os.path.basename(real_vdo.path)
    expected = EXPECTED_VDO_METRICS[filename]

    assert real_vdo.file_size == expected["file_size"]
    assert real_vdo.QGISvdoGroupName == f'fixtures_0x{real_vdo.file_size:X}'
# 'fixtures_0x3A01'


@pytest.mark.slow
def test_vdo_files_read_success(real_vdo):
    """Проверка чтения реальных данных"""
    expected = b'\x00\x01\x00\x12\x00'

    assert real_vdo.read(2, 5) == expected
