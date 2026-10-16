import pytest   # type: ignore
# import struct

from QGIS_VDO.vdo.blocks import block_0x06
from QGIS_VDO.vdo.blocks.block_0x06 import OFFSET_S0_ITEMS  # , POI_ITEM
# from QGIS_VDO.vdo.blocks.block_0x10 import POI_BRIF, POI_DETAILS
from QGIS_VDO.vdo.datatypes import VDO_FILE
from QGIS_VDO.vdo.geotypes import COORD, MAP_AREA
from QGIS_VDO.vdo.enums import en_POI_CAT

from QGIS_VDO.tests.fixtures import FIXTURES_DIR


BLOCK_DICT = {
    'bnl_06_0x8f4a06.bin': {
        'name': 'BNL34 0x800 type 0x06',
        'segsize': 0x800,
        'dbrev': 34,
        's_brand': 'GULF',
        # 'bl_0x10':
        'first_item': {
            '_bladr10': 0x76BB08,
            '_ptr10': 0x398,
            '_LOCAL_X': 0x42,
            '_LOCAL_Y': 0x2ceb,
            '_cat': en_POI_CAT.Hotel,
            '_p_brand': 0,
            'is_custom': 0,
            'id': 0x3d7f74e9,
            'brand': '',
            'coord': '52.556052N 6.736922E',
        },
    },
    'ru30_06_0x9e8601.bin': {
        'name': 'RUS30 0x800 type 0x06',
        'segsize': 0x800,
        'dbrev': 30,
        's_brand': '',
        'first_item': {
            '_bladr10': 0x6BC70C,
            '_ptr10': 0x128,
            '_LOCAL_X': 0x209,
            '_LOCAL_Y': 0x312a,
            '_cat': en_POI_CAT.City,
            '_p_brand': 0,
            'is_custom': 1,         # !!!
            'id': 0,
            'brand': '',
            'coord': '60.380991N 29.486025E',
        },
    },
    'ru34_06z_01ac7e01.bin': {
        'name': 'RUS34 0x200 type 0x06 lzw packed',
        'segsize': 0x200,
        'dbrev': 34,
        's_brand': '',
        'first_item': {
            '_bladr10': 0x152C722,
            '_ptr10': 0x1658,
            '_LOCAL_X': 0x372F,
            '_LOCAL_Y': 0x9C99,
            '_cat': en_POI_CAT.Shcool,
            '_p_brand': 0,
            'is_custom': 0,
            'id': 0x41609601,
            'brand': '',
            'coord': '46.512474N 37.197146E',
        },
    },
}


@pytest.fixture(
    scope="function",
    params=list(BLOCK_DICT),
    ids=[BLOCK_DICT[k]["name"] for k in BLOCK_DICT])  # <--- Понятные имена в логах pytest
def block_06_fixture(request):
    """
    Генератор реальных блоков и проверяемых метрик
    """
    blpath = FIXTURES_DIR / request.param
    metric = BLOCK_DICT[request.param]
    # print(metric)
    dbr = metric["dbrev"]
    ss = metric['segsize']
    block = VDO_FILE().load_single_block(blpath, dbrev=dbr, segsize=ss)
    
    return (block, metric)


# @pytest.fixture(scope="function")
# def vdo_bnl_fixture():
#     """Полный VDO объект для BNL (для extended-тестов)."""
#     from QGIS_VDO.vdo.fixtures_vdo import vdo34bnl as vdo
#     return vdo


# № ----------------------------------------------------------------------------

def test_init_block(block_06_fixture):
    """Проверка инициализации блока верными значениями"""
    (block, metrics) = block_06_fixture
    block: block_0x06

    assert block.dbrev == metrics['dbrev']
    assert block.vdo.segsize == metrics['segsize']

# ======================================================================
# 1. POI_ITEM — парсинг и структура
# ======================================================================


def test_poi_item_unpack(block_06_fixture):
    """1.1 Корректность распаковки struct POI_ITEM_struct (>LHHHHHHLLL, 28 байт)"""
    (block, metrics) = block_06_fixture
    block: block_0x06

    # get first item
    item = next(block.get_all_items())
    expected = metrics['first_item']

    assert item._bladr10 == expected['_bladr10']
    assert item._ptr10 == expected['_ptr10']
    assert item._LOCAL_X == expected['_LOCAL_X']
    assert item._LOCAL_Y == expected['_LOCAL_Y']
    assert item._cat == expected['_cat']
    assert item._p_brand == expected['_p_brand']
    assert item.is_custom == expected['is_custom']
    assert item.id == expected['id']
    assert item.brand == expected['brand']
    assert item.bladdr is None
    assert repr(item.coord) == expected['coord']
    assert item.poi is None


# ======================================================================
# 2. POI_ITEM — координаты и бренд
# ======================================================================

def test_poi_item_coord_calculation(block_06_fixture):
    """2.1 LOCAL_X/Y → абсолютные координаты: base + (local << 8)"""
    block, metrix = block_06_fixture

    # items = list(block.get_all_items())
    items = [item for item in block.get_all_items(is_load_extended=False)]
    second = items[1]

    assert len(items) > 0

    assert second.coord is not None
    assert second.brand is not None  # == metrix['s_brand']
    
    # Вычисляем ожидаемую координату
    base_hlon = block.area.left_bottom._hlon
    base_hlat = block.area.left_bottom._hlat
    expected_hlon = base_hlon + (second._LOCAL_X << 8)
    expected_hlat = base_hlat + (second._LOCAL_Y << 8)

    assert second.coord._hlon == expected_hlon
    assert second.coord._hlat == expected_hlat


def test_poi_item_brand_parsing(block_06_fixture):
    """2.2 Извлечение бренда из name blob по BRAND offset"""
    block, _ = block_06_fixture

    # Находим item с брендом (p_brand > 0)
    items_with_brand = [
        item for item in block.get_all_items()
        if item._p_brand > 0
    ]

    if items_with_brand:
        item = items_with_brand[0]
        # Бренд должен быть не пустым и в верхнем регистре
        assert len(item.brand) > 0
        assert item.brand == item.brand.upper()
        # Проверяем, что бренд действительно прочитан из блока
        raw_brand = bytes(block.read(item._p_brand, 64))
        null_idx = raw_brand.find(b'\x00')
        if null_idx != -1:
            raw_brand = raw_brand[:null_idx]
        expected_brand = raw_brand.decode('latin-1').upper()
        assert item.brand == expected_brand


def test_poi_item_no_brand(block_06_fixture):
    """2.3 BRAND == 0 → item.brand == ''"""
    block, _ = block_06_fixture
    items = list(block.get_all_items())

    # Находим item без бренда
    items_no_brand = [item for item in items if item._p_brand == 0]
    if items_no_brand:
        assert items_no_brand[0].brand == ''


# ======================================================================
# 3. block_0x06 — инициализация и структура
# ======================================================================

def test_block_06_area(block_06_fixture):
    """3.1 MAP_AREA корректно загружен (left_bottom, right_top)"""
    block, _ = block_06_fixture

    assert block.area is not None
    assert isinstance(block.area, MAP_AREA)
    assert block.area.left_bottom is not None
    assert block.area.right_top is not None
    assert isinstance(block.area.left_bottom, COORD)
    assert isinstance(block.area.right_top, COORD)

    # right_top должен быть больше left_bottom
    assert block.area.right_top._hlon > block.area.left_bottom._hlon
    assert block.area.right_top._hlat > block.area.left_bottom._hlat


def test_block_06_s0_list(block_06_fixture):
    """3.2 s0_li_items имеет верные ptr/cnt"""
    block, _ = block_06_fixture

    assert block.s0_li_items is not None
    assert hasattr(block.s0_li_items, 'ptr')
    assert hasattr(block.s0_li_items, 'cnt')
    assert block.s0_li_items.cnt > 0
    assert block.s0_li_items.ptr > 0

    # ptr должен указывать на данные внутри блока (после заголовка)
    assert block.s0_li_items.ptr >= OFFSET_S0_ITEMS
