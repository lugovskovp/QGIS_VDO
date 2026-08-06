import pytest     # type: ignore # noqa
# from unittest.mock import Mock

# Замените импорты под вашу структуру проекта
from QGIS_VDO.vdo.geotypes import COORD

# Константы для тестов
MULCOORD = 5555554
DOUBLE_BYTES_CNT = 8
MOST_SIGNIFICANT_BIT = 0x80000000


@pytest.fixture
def raw_coord_bytes():
    """Сырые байты для координат в формате Big-Endian.
    Координаты: 6.356619 N, 26.249632 W
    hlon = 20835376 -> hex: 0x013DEC30 -> Big-Endian: b'\x01\x3D\xEC\x30'
    hlat = 35314544 -> hex: 0x021ADB70 -> Big-Endian: b'\x02\x1A\xDB\x70'
    """
    return b'\x01\x3D\xEC\x30\x02\x1A\xDB\x70'


# =========================================================================
# 1. ТЕСТЫ ИНИЦИАЛИЗАЦИИ (Сценарии A, B, C)
# =========================================================================

def test_init_scenario_a_bytes(raw_coord_bytes):
    """Сценарий A: Инициализация из сырого буфера байт."""
    coord = COORD(raw_coord_bytes)
    assert coord._hlon == 20835376
    assert coord._hlat == 35314544
    assert pytest.approx(coord.lon) == -26.249632
    assert pytest.approx(coord.lat) == 6.356619


def test_init_scenario_b_ints():
    """Сценарий B: Инициализация из двух целых чисел (hlon, hlat) с маскированием."""
    # Передаем числа, выходящие за пределы 32 бит, для проверки маски & 0xFFFFFFFF
    coord = COORD(20835376 + 0x100000000, 35317104)
    assert coord._hlon == 20835376
    assert coord._hlat == 35317104


def test_init_scenario_c_floats():
    """Сценарий C: Инициализация из координат float (в градусах)."""
    # 6.356619 N, 26.249632 W
    coord = COORD(-26.249632, 6.356619)
    assert coord._hlon == 20835371
    assert coord._hlat == 35314540


def test_init_invalid_types():
    """Проверка выброса ValueError при передаче неверных типов данных."""
    # with pytest.raises(TypeError, match="memoryview:"):
    with pytest.raises(ValueError, match="Неверные типы аргументов для COORD"):
        COORD("строка вместо байт", None)

    with pytest.raises(ValueError, match="Неверные типы аргументов для COORD"):
        COORD(155, "строка вместо байт")


# =========================================================================
# 2. ТЕСТЫ ЗНАКОВЫХ ЧИСЕЛ И ОТРИЦАТЕЛЬНЫХ КООРДИНАТ
# =========================================================================

def test_negative_coordinates_handling():
    """Проверка корректности работы со знаковым битом (MOST_SIGNIFICANT_BIT).
    Проверяем на южном (S) и западном дальше -30° (W) полушариях, где значения знаковые.
    """
    # Пусть lat = -12.5°, тогда hlat = -69999993. В unsigned 32-bit: -69999993 + 2**32 = 4225522871
    # Пусть lon = -35.0°, тогда hlon = (-35 + 30) * MULCOORD = -27777775 -> -27777775 + 2**32 = 4267189526
    u_hlon = 4267189526 & 0xFFFFFFFF
    u_hlat = 4225522871 & 0xFFFFFFFF
    
    coord = COORD(int(u_hlon), int(u_hlat))

    assert coord._hlongitude == -27777770
    assert coord._hlatitude == -69444425
    assert coord.lat == -12.5
    assert coord.lon == -35.0


# =========================================================================
# 3. ТЕСТЫ СВОЙСТВ И ЭКСПОРТА
# =========================================================================

def test_as_tuple(raw_coord_bytes):
    """Проверка экспорта координат в tuple для QGIS."""
    coord = COORD(raw_coord_bytes)
    lon, lat = coord.as_tuple()
    assert pytest.approx(coord.lon) == -26.249632
    assert pytest.approx(coord.lat) == 6.356619


def test_repr_formatting():
    """Проверка строкового представления __repr__ для разных полушарий."""
    coord_north_west = COORD(-9.161808, 35.317104)
    assert repr(coord_north_west) == '35.317104N 9.161808W'

    coord_south_east = COORD(15.5, -45.123456)
    assert repr(coord_south_east) == "45.123456S 15.500000E"


# =========================================================================
# 4. СРАВНЕНИЕ И ДЕЛЬТА (__eq__, delta)
# =========================================================================

def test_equality():
    """Проверка равенства координат через __eq__."""
    c1 = COORD(-9.161808, 35.317104)
    c2 = COORD(-9.161808, 35.317104)
    c3 = COORD(10.0, 20.0)
    
    assert c1 == c2
    assert c1 != c3
    assert (c1 == "не объект COORD") is False


def test_equality_returns_not_implemented():
    """Проверка, что __eq__ возвращает NotImplemented для чужих типов."""
    coord = COORD(0.0, 0.0)
    assert coord.__eq__("строка") is NotImplemented


def test_delta_calculation():
    """Проверка вычисления разницы между координатами."""
    c1 = COORD(10.50, 20.80)
    c2 = COORD(10.00, 20.00)
    
    assert c1.delta(c2) == "lat:0.80° x lon:0.50°"
    assert c1.delta("не COORD") is NotImplemented


# =========================================================================
# 5. ПРОВЕРКА ОПТИМИЗАЦИИ ПАМЯТИ
# =========================================================================

def test_slots_efficiency_coord():
    """Проверка, что у класса COORD заблокирован динамический __dict__."""
    coord = COORD(0.0, 0.0)
    with pytest.raises(AttributeError):
        _ = coord.__dict__
