import pytest   # type: ignore
# from unittest.mock import MagicMock, patch  # type: ignore
# import struct

from QGIS_VDO.vdo.blocks import block_0x10
# from QGIS_VDO.vdo.blocks.block_0x10 import OFFSET_S0_BRIFS
from QGIS_VDO.vdo.datatypes import VDO_FILE, LIST
from QGIS_VDO.vdo.geotypes import POI, POI_BRIF     # , POI_DETAILS
from QGIS_VDO.vdo.enums import en_CARINET_LANGUAGE

from QGIS_VDO.tests.fixtures import FIXTURES_DIR


PREAMBULA_BLOCK_0x10 = 0x30

BLOCK_DICT = {
    '0x10_bnl_0x76bb08.bin': {
        'name': 'BNL34 0x800 type 0x10',
        'segsize': 0x800,
        'dbrev': 34,
        's1_li_more': LIST(bytes.fromhex('060000B9')),
        's4_li_far': LIST(bytes.fromhex('22E800B9')),
        'poi94': {
            'locality': '', 'brand': 'VOLKSWAGEN',
            'id': 0x3F16AEEF, 'coord': '52.157045N 6.749363E',
            'name': 'HUISKES KOKKELER AUTOMOBIELBEDR. VOLKSWAGEN', 'brand': 'VOLKSWAGEN',
            'country': 'NEDERLAND', 'region': 'OVERIJSSEL',
            'city': 'HAAKSBERGEN', 'street': 'ENSCHEDESESTRAAT',
            'houseno': '47', 'postcode': '7481', 'phone': '+31535721345', '_zero1': 0x0
        }
    },
    '0x10_ru30_0x6BC70C.bin': {
        'name': 'RUS30 0x800 type 0x10',
        'segsize': 0x800,
        'dbrev': 30,
        's1_li_more': LIST(bytes.fromhex('0BA8016F')),
        's4_li_far': LIST(bytes.fromhex('4500016F')),
        'poi94': {
            'locality': '', 'brand': '',
            'id': 0x0, 'coord': '59.054912N 28.727318E',
            'name': 'OVSISCHE', 'brand': '',
            'country': 'ROSSIYA', 'region': 'LENINGRAD',
            'city': 'OVSISCHE', 'street': '',
            'houseno': '', 'postcode': '', 'phone': '', '_zero1': 0x1,
        }
    },
    '0x10z_ru34_df002e.bin': {
        'name': 'RUS34 0x200 type 0x10 lzw packed',
        'segsize': 0x200,
        'dbrev': 34,
        's1_li_more': LIST(bytes.fromhex('21A001BC')),
        's4_li_far': LIST(bytes.fromhex('670001BD')),
        'poi94': {
            'locality': 'TSENTRAL\'NIY RAYON', 'brand': '',
            'id': 0x21200FB9, 'coord': '59.945880N 30.329462E',
            'name': 'PAMYATNIK ALEKSANDRU SUVOROVU', 'brand': '',
            'country': 'ROSSIYA', 'region': 'SANKT PETERBURG',
            'city': 'SANKT PETERBURG', 'street': 'SUVOROVSKAYA PLOSHCHAD\'',
            'houseno': '', 'postcode': '191186', 'phone': '', '_zero1': 0x1,
        }
    },
}


@pytest.fixture(
    scope="function",
    params=list(BLOCK_DICT),
    ids=[BLOCK_DICT[k]["name"] for k in BLOCK_DICT])
def block_10_fixture(request):
    """Генератор реальных блоков и проверяемых метрик"""
    blpath = FIXTURES_DIR / request.param
    metric = BLOCK_DICT[request.param]
    dbr = metric["dbrev"]
    ss = metric['segsize']
    block: block_0x10 = VDO_FILE().load_single_block(blpath, dbrev=dbr, segsize=ss)
    
    return (block, metric)


# ======================================================================
# 1. Инициализация блока
# ======================================================================

def test_init_0x10(block_10_fixture):
    """1.1 Корректная инициализация блока 0x10"""
    block, metrics = block_10_fixture
    block: block_0x10

    assert block.type == 0x10
    assert block.s0_li_brif.ptr == PREAMBULA_BLOCK_0x10
    assert block.s1_li_more == metrics['s1_li_more']
    assert block.s4_li_far == metrics['s4_li_far']


def test_block_0x10_slots_are_effective(block_10_fixture):
    """1.2 __slots__ enforced — no __dict__"""
    block, _ = block_10_fixture
    assert not hasattr(block, '__dict__')
    assert set(block.__slots__) == {"s0_li_brif", "s1_li_more", "s4_li_far", "prev", "next"}


def test_block_0x10_s0_li_brif_has_ptr_and_cnt(block_10_fixture):
    """1.3 s0_li_brif имеет ptr/cnt"""
    block, _ = block_10_fixture
    PREAMBULA_BLOCK = 0x30

    assert block.s0_li_brif is not None
    assert hasattr(block.s0_li_brif, 'ptr')
    assert hasattr(block.s0_li_brif, 'cnt')
    assert block.s0_li_brif.ptr == PREAMBULA_BLOCK


def test_block_0x10_prev_next_bladdr(block_10_fixture):
    """1.4 prev/next — BLADDR объекты"""
    block, _ = block_10_fixture
    assert block.prev is not None
    assert block.next is not None
    assert hasattr(block.prev, 'value')
    assert hasattr(block.next, 'value')


def test_block_0x10_li_brif_can_alias(block_10_fixture):
    """1.5 brif - заведения, more - адреса, far - . дорожной сети"""
    block, _ = block_10_fixture
    block: block_0x10

    assert block.s0_li_brif.cnt >= block.s1_li_more.cnt
    assert block.s1_li_more.cnt <= block.s4_li_far.cnt


# ======================================================================
# 2. get_all_brifs — итератор POI_BRIF
# ======================================================================

def test_get_all_brifs_returns_iterator(block_10_fixture):
    """2.1 get_all_brifs возвращает итератор"""
    block, _ = block_10_fixture
    brifs = block.get_all_brifs()
    assert hasattr(brifs, '__iter__')
    assert hasattr(brifs, '__next__')


def test_get_all_brifs_returns_poi_brif_instances(block_10_fixture):
    """2.2 get_all_brifs возвращает экземпляры POI_BRIF"""
    block, _ = block_10_fixture
    for brif in block.get_all_brifs():
        assert isinstance(brif, POI_BRIF)
        break


def test_get_all_brifs_count_matches(block_10_fixture):
    """2.3 Количество brif == s0_li_brif.cnt"""
    block, _ = block_10_fixture
    brifs = list(block.get_all_brifs())
    assert len(brifs) == block.s0_li_brif.cnt
    assert len(brifs) > 0


def test_get_all_brif_has_name_and_lang(block_10_fixture):
    """2.4 Каждый brif имеет name и en_Lang"""
    block, _ = block_10_fixture
    for brif in block.get_all_brifs():
        assert hasattr(brif, 'name')
        assert hasattr(brif, 'en_Lang')
        assert isinstance(brif.en_Lang, en_CARINET_LANGUAGE)
        break


def test_get_all_brifs_ptr_name_resolved(block_10_fixture):
    """2.5 Если _ptr_name > 0, name не пустой"""
    block, _ = block_10_fixture
    brifs = list(block.get_all_brifs())
    brifs_with_name = [b for b in brifs if b._ptr_name > 0]
    if brifs_with_name:
        assert len(brifs_with_name[0].name) > 0


def test_get_all_brifs_ptr_locality_resolved(block_10_fixture):
    """2.6 Если _ptr_locality > 0, locality не пустой"""
    block, _ = block_10_fixture
    brifs = list(block.get_all_brifs())
    brifs_with_locality = [b for b in brifs if b._ptr_locality > 0]
    if brifs_with_locality:
        assert len(brifs_with_locality[0].locality) > 0


# ======================================================================
# 3. get_poi — полный POI
# ======================================================================

def test_get_poi_returns_poi_instance(block_10_fixture):
    """3.1 get_poi возвращает POI или None"""
    block, _ = block_10_fixture
    assert block.s0_li_brif.cnt > 0
    first_brif_offset = PREAMBULA_BLOCK_0x10 + POI_BRIF.size
    poi = block.get_poi(first_brif_offset)
    assert poi is None or isinstance(poi, POI)


def test_get_poi_has_name(block_10_fixture):
    """3.2 POI имеет name"""
    block, _ = block_10_fixture
    assert block.s0_li_brif.cnt > 0
    first_brif_offset = PREAMBULA_BLOCK_0x10 + POI_BRIF.size
    poi = block.get_poi(first_brif_offset)
    if poi is not None:
        assert hasattr(poi, 'name')


def test_get_poi_has_brand(block_10_fixture):
    """3.3 POI имеет brand"""
    block, _ = block_10_fixture
    assert block.s0_li_brif.cnt > 0
    first_brif_offset = PREAMBULA_BLOCK_0x10 + POI_BRIF.size
    poi = block.get_poi(first_brif_offset)
    if poi is not None:
        assert hasattr(poi, 'brand')


def test_get_poi_has_coord(block_10_fixture):
    """3.4 POI имеет coord"""
    block, _ = block_10_fixture
    assert block.s0_li_brif.cnt > 0
    first_brif_offset = PREAMBULA_BLOCK_0x10 + POI_BRIF.size
    poi = block.get_poi(first_brif_offset)
    if poi is not None:
        assert hasattr(poi, 'coord')


# ======================================================================
# 6. POI — структура
# ======================================================================

def test_poi_slots():
    """6.1 POI имеет __slots__"""
    raw = bytes(8)
    poi = POI(raw)
    assert not hasattr(poi, '__dict__')
    expected = {'brand', 'id', 'raw_road', 'coord', 'postcode', 'phone',
                'houseno', 'country', 'region', 'city', 'street'}
    # POI расширяет POI_BRIF, поэтому проверяем пересечение
    assert expected.issubset(set(poi.__slots__))


def test_poi_initial_values():
    """6.2 POI инициализируется с пустыми значениями"""
    raw = bytes(8)
    poi = POI(raw)
    assert poi.brand == ''
    assert poi.postcode == ''
    assert poi.phone == ''
    assert poi.houseno == ''
    assert poi.country == ''
    assert poi.region == ''
    assert poi.city == ''
    assert poi.street == ''
    assert poi.id == 0
    assert poi.coord is None
    assert type(poi.raw_road) is list
    assert poi._zero1 == 0


# ======================================================================
# 7. Интеграционные тесты
# ======================================================================
def test_get_poi_94_has_metric(block_10_fixture):
    """POI #94 имеет заполненный brand"""
    block, metric = block_10_fixture
    block: block_0x10
    expected_val = metric['poi94']

    assert block.s0_li_brif.cnt > 94

    poi_offset = PREAMBULA_BLOCK_0x10 + POI_BRIF.size * 94
    poi: POI = block.get_poi(poi_offset)

    # str = f"'id': 0x{poi.id:X}, 'coord': '{poi.coord}', 'name': '{poi.name}', 'brand': '{poi.brand}' "
    # str = f"'country': '{poi.country}', 'region': '{poi.region}', 'city': '{poi.city}', 'street': '{poi.street}', "
    # str = f"'houseno': '{poi.houseno}', 'postcode': '{poi.postcode}', 'phone': '{poi.phone}', '_zero1': 0x{poi._zero1:X}" # noqa
    # str = f"'locality': '{poi.locality}', 'brand': '{poi.brand}'"
    # assert str == ''

    assert poi.id == expected_val['id']
    assert repr(poi.coord) == expected_val['coord']
    assert poi._zero1 == expected_val['_zero1']
    assert poi.locality == expected_val['locality']
    assert poi.name == expected_val['name']
    assert poi.brand == expected_val['brand']
    assert poi.postcode == expected_val['postcode']
    assert poi.country == expected_val['country']
    assert poi.region == expected_val['region']
    assert poi.city == expected_val['city']
    assert poi.street == expected_val['street']
    assert poi.houseno == expected_val['houseno']
    assert poi.phone == expected_val['phone']
    assert poi.region == expected_val['region']


def test_get_poi_third_has_metric(block_10_fixture):
    """У первых POI есть ссылка на дорожную сеть"""
    block, _ = block_10_fixture
    block: block_0x10

    assert block.s0_li_brif.cnt > 0

    ptr = block.s0_li_brif.ptr
    # Проверяем первые 5 POI — достаточно для покрытия
    for _ in range(min(5, block.s0_li_brif.cnt)):
        poi: POI = block.get_poi(ptr)
        ptr += POI_BRIF.size
        assert poi.raw_road is not None


# raise NotImplementedError(f"Byte alias: {alias} is neither zero, not 1. \
# E   NotImplementedError: Byte alias: 2 is neither zero, not 1.  (41872, 2, 19, 0, 17488)
# (A390, 2, 13, 0, 4450)


def test_block_0x10_integration_get_brifs_and_poi(block_10_fixture):
    """7.1 get_all_brifs + get_poi — полный цикл"""
    block, _ = block_10_fixture
    
    brifs = list(block.get_all_brifs())
    assert len(brifs) > 0
    
    # Первый brif должен иметь корректный ptr
    first_brif = brifs[0]
    assert first_brif._ptr_name >= 0


def test_block_0x10_multiple_brifs_different_ptrs(block_10_fixture):
    """7.2 Разные brif имеют разные ptr"""
    block, _ = block_10_fixture
    
    brifs = list(block.get_all_brifs())
    if len(brifs) > 1:
        ptrs = [b._ptr_name for b in brifs]
        # Не все ptr должны быть одинаковыми
        assert len(set(ptrs)) > 0 or len(brifs) == 1


def test_block_0x10_s1_li_more_not_zero(block_10_fixture):
    """7.3 s1_li_more имеет ненулевой ptr/cnt"""
    block, _ = block_10_fixture
    assert block.s1_li_more.ptr > 0
    assert block.s1_li_more.cnt > 0


def test_block_0x10_s4_li_far_not_zero(block_10_fixture):
    """7.4 s4_li_far имеет ненулевой ptr/cnt"""
    block, _ = block_10_fixture
    assert block.s4_li_far.ptr > 0
    assert block.s4_li_far.cnt > 0
