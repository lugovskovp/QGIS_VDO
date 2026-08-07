import pytest
# from unittest.mock import MagicMock

from QGIS_VDO.vdo.datatypes import VDO_FILE
from QGIS_VDO.vdo.geotypes import COORD
from QGIS_VDO.vdo.blocks import block_0x09

from QGIS_VDO.tests.fixtures import FIXTURES_DIR

# --- Настройки окружения и фикстуры ---

#  EE sc=7  bl=0x0515a202 lo=317323264 la=326782976; lo=334100480 la=343560192
# кронштадт 13C74CE413DE50A0 = None
# сосновый бор '1390805613D22F1F' = 0x55D7101
# 1/2 '12F4659413A5F77A' = 0x55d4805
# 1/4 '1304FD2313A65A1C' = 0x55D4F05

FIXTURE_09_FILE = FIXTURES_DIR / '0x09_EE_0x0515a202.bin'
COORD_ORIGIN = COORD(317323264, 326782976)
COORD_MAX = COORD(334100480, 343560192)


# кронштадт 13C74CE413DE50A0 = None
# сосновый бор '1390805613D22F1F' = 0x55D7101
# 1/2 '12F4659413A5F77A' = 0x55d4805
# 1/4 '1304FD2313A65A1C' = 0x55D4F05
# Беларусь 133A3BF012092DD4

EXPECTED_TEST_POINTS = {
    "13C74CE413DE50A0" : {
        "name": "кронштадт",
        "coord_str": "60.000629N 29.729138E",
        "map_val": None,
    },
    "1390805613D22F1F" : {
        "name": "сосновый бор",
        "coord_str": "59.857528N 29.082702E",
        "map_val": 0x55D7101,
    },
    "12F4659413A5F77A" : {
        "name": "map 1/2",
        "coord_str": "59.335918N 27.241218E",
        "map_val": 0x55d4805,
    },
    "1304FD2313A65A1C" : {
        "name": "map  1/4",
        "coord_str": "59.340463N 27.436945E",
        "map_val": 0x55D4F05,
    },
    "133A3BF012092DD4" : {
        "name": "outside_folder",
        "coord_str": "54.466475N 28.065053E",
        "map_val": None,
    },
}


@pytest.fixture(
    scope="function",
    params=list(EXPECTED_TEST_POINTS),
    ids=list(EXPECTED_TEST_POINTS))
def point_fixture(request):
    """
    Реальные координаты и проверяемые метрики
    """
    hexcoord = request.param
    coord = COORD(bytes.fromhex(hexcoord))
    metrics = EXPECTED_TEST_POINTS[hexcoord]
    return (coord, metrics)


# --- Набор тестов ---

@pytest.fixture
def ee_09_block():
    #  EE sc=7  bl=0x0515a202 lo=317323264 la=326782976; lo=334100480 la=343560192
    # origin = 58.820952N 27.118204E, max = 61.840852N 30.138103E
    #item_side = 524288
    bl_09: block_0x09 = VDO_FILE().load_single_block(FIXTURE_09_FILE, 34, 0x800, COORD_ORIGIN, COORD_MAX)
    return bl_09


def test_coord_from_bytes(point_fixture):
    """ Проверка координат по реальным точкам"""
    c, metric = point_fixture

    assert str(c) == metric["coord_str"]


def test_block_0x09_slots_are_effective(ee_09_block):
    """Проверяем, что оптимизированный block_0x09 жестко держит структуру слотов памяти."""
    
    assert not hasattr(ee_09_block, '__dict__'), "Обнаружен __dict__! Проверьте __slots__ дочернего класса."
    assert hasattr(ee_09_block, '__slots__')
    assert 'origin_hlon' in ee_09_block.__slots__
    assert 'origin_hlat' in ee_09_block.__slots__
    assert 'qty_x' in ee_09_block.__slots__


def test_block_0x09_init_unpacks_and_calculates_correctly(ee_09_block):
    """Проверяем, что __init__ корректно раскладывает COORD на примитивы int и считает сетку."""
    # bl_09 = VDO_FILE().load_single_block(FIXTURE_09_FILE, 34, 0x800, COORD_ORIGIN, COORD_MAX)

    # Проверяем распаковку в плоские слоты
    assert ee_09_block.origin_hlon == 317323264
    assert ee_09_block.origin_hlat == 326782976
    #item_side = 524288
    # Проверяем деление сетки: 334100480-317323264 // 524288 = 32, 343560192-326782976 // 524288 = 32
    assert ee_09_block.qty_x == 32
    assert ee_09_block.qty_y == 32


def test_block_0x09_items_cnt(ee_09_block):
    """Проверяем сквозное получение количества элементов из листа валидности."""
    assert ee_09_block.items_cnt() == 19


def test_block_0x09_get_xy_item(ee_09_block):
    """Тестируем точечную выборку гео-блока по ячейке сетки (X, Y)."""
    # Сетка 32х32. Ищем элемент (y=2, x=1) -> индекс в листе: 1 + 1 * 32 = 33
    block = ee_09_block
    
    # Вычисляем смещение указателя для ячейки: ptr_offset = 0x14 + 33 * 2 = 0x56 / 86
    # ptr_offset = 0x14 + (1 + 32) * PTR.size
    # target_ptr_value = 0x814
    
    # 1. Тест успешного извлечения адреса подблока карты
    res_bladdr = block.get_xy_item(1, 1)        # 055d3e 05
    assert res_bladdr is not None
    assert res_bladdr.value == 0x55d3e05

    # 2. Тест выхода за границы индексов списка li_items
    assert block.get_xy_item(33, 5) is None

    # 3. Тест обработки пустой ячейки (нулевой указатель)
    assert block.get_xy_item(0, 13) is None


def test_block_0x09_find_by_coord(ee_09_block, point_fixture):
    """Тестируем поиск блока карты по объекту координат COORD."""

    coord_srch, metric = point_fixture
    map_bl = ee_09_block.find_by_coord(coord_srch)

    if map_bl is None:
        assert metric["map_val"] is None
    else:
        assert metric["map_val"] == map_bl.value
    

def test_block_0x09_get_items_flat_tuple_output(ee_09_block):
    """Тестируем zero-alloc генератор и валидацию формата плоского float-кортежа WGS-84."""

    results = list(ee_09_block.get_items())

    # Проверяем, что генератор успешно выдал структуру
    assert len(results) == 19   # li valid = 0814 0013
    
    # Распаковываем плоский кортеж (больше никаких объектов COORD внутри списка!)
    bladdr_val, lon_min, lat_min, lon_max, lat_max = results[0]
    
    assert bladdr_val == 0x55d3e05
    # Проверяем правильность пересчета в WGS-84 float
    # lon_min = 27.118203513096987
    # lat_min = 58.8209521498666
    assert lon_min == 27.118203513096987
    assert lat_min == 58.8209521498666
    
    # Проверяем размеры с учетом склейки (size_X=1, size_Y=1 из-за пустых соседних ячеек)
    # lon_max = 27.495690978793476
    # lat_max = 59.19843961556309
    assert pytest.approx(lon_max) == 27.4957
    assert pytest.approx(lat_max) == 59.1984
