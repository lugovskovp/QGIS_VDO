import pytest   # type: ignore
import struct

from QGIS_VDO.vdo.geotypes import MAP_AREA
from QGIS_VDO.vdo.consts import struct_2UINT


# --- ЗАГЛУШКИ КОНСТАНТ ДЛЯ СРЕДЫ ТЕСТИРОВАНИЯ ---
DOUBLE_BYTES_CNT = 8
# MULCOORD = 1000000
MOST_SIGNIFICANT_BIT = 0x80000000


# --- ГЛОБАЛЬНАЯ ФИКСТУРА-ФАБРИКА ---
@pytest.fixture
def map_buffer_factory():
    """Фабрика для динамического создания байтовых буферов MAP_AREA."""
    def _create_buffer(hlon1, hlat1, hlon2, hlat2, scale):
        coord1 = struct_2UINT.pack(hlon1, hlat1)
        coord2 = struct_2UINT.pack(hlon2, hlat2)
        
        buffer = bytearray(20)
        buffer[0:8] = coord1
        buffer[8:16] = coord2
        struct.pack_into(">H", buffer, 0x12, scale)
        return buffer
    return _create_buffer


# --- ОТДЕЛЬНЫЕ ТЕСТ-ФУНКЦИИ ---

def test_map_area_property_naming(map_buffer_factory):
    """Проверяем доступность и корректность свойства right_top."""
    buf = map_buffer_factory(30000000, 0, 40000000, 10000000, 2)
    area = MAP_AREA(buf)
    
    assert area.right_top is not None
    assert area.right_top._hlon == 40000000


def test_map_area_dimentions_calculation(map_buffer_factory):
    """
    Проверяем форматирование размеров в HEX и расчет километров с новым MULCOORD (0x54C562).
    
    Разница hlat = 5555554 (0x54C562)
    Разница hlon = 5555554 (0x54C562) -> ровно 1 градус при MULCOORD = 5555554
    grad = (111.134861111 * 5555554) / 5555554 = 111.135
    """
    # Левая нижняя точка: hlon=0, hlat=0
    # Правая верхняя точка: hlon=5555554, hlat=5555554
    buf = map_buffer_factory(0, 0, 5555554, 5555554, 0)
    area = MAP_AREA(buf)
    
    # 5555554 в hex — это 54c562
    assert area.dimentions == "54c562*54c562 (111.135km)"


def test_map_area_repr_output(map_buffer_factory):
    """Проверяем отладочный вывод __repr__."""
    buf = map_buffer_factory(30000000, 0, 40000000, 10000000, 1)
    area = MAP_AREA(buf)
    
    expected = f"{repr(area.left_bottom)}  {repr(area.right_top)}"
    assert repr(area) == expected


@pytest.mark.parametrize("scale, expected_max", [
    (0, "54C562 54C562"),  # Сдвиг на 0: 5555554 -> 0x54C562
    (2, "153158 153158"),  # Сдвиг на 2: 5555554 >> 2 = 1388888 -> 0x153158
    (10, "1531 1531"),     # Сдвиг на 10: 5555554 >> 10 = 5425 -> 0x1531
])
def test_map_area_max_vrt_val_with_scales(map_buffer_factory, scale, expected_max):
    """Тестируем битовый сдвиг масштаба с дельтой координат, равной новому MULCOORD."""
    buf = map_buffer_factory(10000000, 10000000, 15555554, 15555554, scale)
    area = MAP_AREA(buf)
    
    assert area.max_vrt_val == expected_max
