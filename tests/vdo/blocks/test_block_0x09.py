import pytest
# from unittest.mock import MagicMock

from QGIS_VDO.vdo.datatypes import VDO_FILE, BLADDR
from QGIS_VDO.vdo.geotypes import COORD
from QGIS_VDO.vdo.blocks import block_0x09
from QGIS_VDO.vdo.consts import struct_UINT     # , struct_WORD

from QGIS_VDO.tests.fixtures import FIXTURES_DIR

# --- Настройки окружения и фикстуры ---

#  EE sc=7  bl=0x0515a202 lo=317323264 la=326782976; lo=334100480 la=343560192
# кронштадт 13C74CE413DE50A0 = None
# сосновый бор '1390805613D22F1F' = 0x55D7101
# 1/2 '12F4659413A5F77A' = 0x55d4805
# 1/4 '1304FD2313A65A1C' = 0x55D4F05

FIXTURE_09_FILE_7 = FIXTURES_DIR / '0x09_EE_0x0515a202.bin'
FIXTURE_09_FILE_2 = FIXTURES_DIR / '0x09_ee34_sc2_0x05119602.bin'     # 0x05119602
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
        "name": "Беларусь outside_folder",
        "coord_str": "54.466475N 28.065053E",
        "map_val": None,
    },
}


@pytest.fixture(
    scope="function",
    params=list(EXPECTED_TEST_POINTS),
    ids=[EXPECTED_TEST_POINTS[k]["name"] for k in EXPECTED_TEST_POINTS])  # <--- Понятные имена в логах pytest
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
    bl_09: block_0x09 = VDO_FILE().load_single_block(FIXTURE_09_FILE_7, 34, 0x800, COORD_ORIGIN, COORD_MAX)
    return bl_09


@pytest.fixture
def ee_09_block_2():
    #  EE sc=7  (051196 02, 49.761253N 24.098304E, 61.840852N 36.177903E)
    origin = COORD(bytes.fromhex('11E9F800107A5000'))
    max = COORD(bytes.fromhex('15E9F800147A5000'))
    bl_09: block_0x09 = VDO_FILE().load_single_block(FIXTURE_09_FILE_2, 34, 0x800, origin, max)
    vdo = VDO_FILE(FIXTURES_DIR / 'carindb34_0h_6800h.bin')
    bl_09.vdo = vdo
    return bl_09


def test_coord_from_bytes(point_fixture):
    """ Проверка координат по реальным точкам"""
    c, metric = point_fixture

    assert str(c) == metric["coord_str"]


def test_block_0x09_slots_are_effective(ee_09_block):
    """Проверяем, что оптимизированный block_0x09 жестко держит структуру слотов памяти."""
    slots = (
        'li_items',
        'li_valid',
        'item_side',
        'origin',
        'qty_y',
        'qty_x',
        'items',
        'quant',
    )
    assert not hasattr(ee_09_block, '__dict__'), "Обнаружен __dict__! Проверьте __slots__ дочернего класса."
    assert hasattr(ee_09_block, '__slots__')

    for slot in slots:
        assert slot in ee_09_block.__slots__


def test_block_0x09_init_unpacks_and_calculates_correctly(ee_09_block_2):
    """Проверяем, что __init__ корректно раскладывает COORD на примитивы int и считает сетку."""
    # bl_09 = VDO_FILE().load_single_block(FIXTURE_09_FILE, 34, 0x800, COORD_ORIGIN, COORD_MAX)

    # Проверяем распаковку в плоские слоты
    assert ee_09_block_2.origin._hlon == 300546048
    assert ee_09_block_2.origin._hlat == 276451328
    #item_side = 524288
    # Проверяем деление сетки: 334100480-317323264 // 524288 = 32, 343560192-326782976 // 524288 = 32
    assert ee_09_block_2.qty_x == 32
    assert ee_09_block_2.qty_y == 32


def test_block_0x09_items_cnt(ee_09_block):
    """Проверяем сквозное получение количества элементов из листа валидности."""
    assert ee_09_block.items_cnt() == 19


def test_block_0x09_items_cnt_break(ee_09_block_2):
    """ Проверка break по li.items.cnt"""
    # ptr сетка  32*32
    alm: block_0x09 = ee_09_block_2
    
    # Все 32*32 итема заполняем значениями val 0x0818 (т.к. с 0x814 BLADDRs)
    val = bytes.fromhex('0818')
    items = val * (32 * 32)
    # len = items.count()
    src = bytearray(alm._raw)
    res = src[:0x14] + items + src[0x14 + 32 * 32 * 2:]
    alm._raw = res

    # Тест выхода за границы x, y
    assert alm._get_xy_item(32, 1) is None    # x >= 32
    assert alm._get_xy_item(1, 32) is None    # y >= 32

    # получаем последний элемент
    last_bladdr = alm._get_xy_item(31, 31)
    assert last_bladdr is not None
    assert isinstance(last_bladdr, BLADDR)
    assert '0514fd 01' in repr(last_bladdr)

    # проверка прохода до граничных значений RLE x, y
    items = list(alm.get_items())
    
    assert len(items) == 1  # там один сплощной элемент в файле

    # Уменьшаем счетчик на 4
    li = struct_UINT.unpack(alm.li_items._raw)[0]
    li = li - 4          # cnt < 0x400 - 4
    alm.li_items._raw = struct_UINT.pack(li)       # Уменьшили кол-во итемов на 4

    # получаем последний элемент
    last_bladdr = alm._get_xy_item(31, 31)
    assert last_bladdr is None

    # _fill_items if curr_item >= total_cnt:
    alm._fill_items()
    items = list(alm.get_items())
    assert len(items) == 1


def test_block_0x09__get_xy_item_valid(ee_09_block_2):
    """Тестируем точечную выборку гео-блока по ячейке сетки (X, Y)."""
    # Сетка 32х32.
    alm: block_0x09 = ee_09_block_2

    # Тест успешного извлечения адреса подблока карты
    res_bladdr = alm._get_xy_item(0, 13)        # 055d3e 05  2068/0x814: [85261057/0x514FB01, 0, 12, 1, 1]
    assert res_bladdr is not None
    assert res_bladdr.value == 0x0514fd01

    # Тест обработки пустой ячейки (нулевой указатель)
    assert alm._get_xy_item(0, 0) is None       # == 0 in file


def test_block_0x09__get_xy_item_less_items(ee_09_block_2):
    """Тестируем точечную выборку гео-блока по ячейке сетки (X, Y)."""
    # Сетка 32х32.
    alm: block_0x09 = ee_09_block_2

    # 2.
    assert alm._get_xy_item(31, 1) is None


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
    block: block_0x09 = ee_09_block

    for k in block.get_items():
        print(k)
    # results = list(block.get_items())
    results = [k for k in block.get_items()]

    # Проверяем, что генератор успешно выдал структуру
    assert len(results) == 19   # li valid = 0814 0013
    
    # Распаковываем плоский кортеж (больше никаких объектов COORD внутри списка!)
    bladdr, lon_min, lat_min, lon_max, lat_max = results[0]
    
    assert bladdr == 0x55d3e05
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


# -------------------------
