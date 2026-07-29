import pytest   # type: ignore # noqa
import sys
from types import ModuleType
from typing import Any

# Импортируем тестируемый класс и функцию генерации словаря
from QGIS_VDO.vdo.datatypes import VDO_FILE, setup_known_types


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
