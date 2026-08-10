import pytest
# from unittest.mock import MagicMock

from QGIS_VDO.vdo.datatypes import VDO_FILE, BLADDR
from QGIS_VDO.vdo.geotypes import COORD
from QGIS_VDO.vdo.blocks import block_0x07, block_0x12
from QGIS_VDO.vdo.blocks.block_0x07 import TERR_DIV
from QGIS_VDO.vdo.consts import struct_UINT  # , struct_WORD

from QGIS_VDO.tests.fixtures import FIXTURES_DIR


# --- Настройки окружения и фикстуры ---

VDO_DICT = {
    "carindb30_0h_9000h.bin": {
        "name": "ru30",
        "local_0": None,
        "poi0_val": 48,     # city
        "li_POI_cat": "0140:0001",
        "li_countryes": None,
        "li_div": "0148:0000",
        "cnt_pois": 1,
    },
    "carindb34_0h_6800h.bin": {
        "name": "ce34",
        "local_0": "Ceska Republika",
        "const_00": 0,
        "const_01": 1,
        "en_country_val": 56,
        "li_nuts": '0290:0001 cnt:1',
        "unk_4": 402,
        "unk_6": 1,
        "bladdr": 0x5728e01,
        "poi0_val": 11,
        "li_POI_cat": "0174:002C",
        "li_countryes": "0292:000B",
        "li_div": "027C:0001",
        "cnt_pois": 44,
    },
    "DB34_0h_3A01h.bin": {
        "name": "bmw34",
        "local_0": "Andorra",
        "const_00": 1,
        "const_01": 1,
        "en_country_val": 5,
        "li_nuts": '0390:0001 cnt:1',
        "unk_4": 19,
        "unk_6": 1,
        "bladdr": 0x715b101,
        "poi0_val": 11,
        "li_POI_cat": "0174:002B",
        "li_countryes": "03E0:0020",
        "li_div": "0278:000E",
        "cnt_pois": 43,
    },
}


@pytest.fixture(
    scope="function",
    params=list(VDO_DICT),
    ids=[VDO_DICT[k]["name"] for k in VDO_DICT])
def terr_div_fixture(request):
    """
    Фикстура, которая инициализирует реальный блок 0x08 данными из словаря.
    Вместо чтения бинарного файла, мы наполняем его свойствами.
    """
    filename = request.param
    metric = VDO_DICT[filename]
    vdo = VDO_FILE(FIXTURES_DIR / filename)
    bl_tos: block_0x12 = vdo.get_block(0)
    block: block_0x07 = vdo.get_block(bl_tos.bladdr_scales)

    # Защита от StopIteration: если генератор пуст (как в ru30), вернется None
    terr_div = next(block.get_terr_div_countries(), None)
    
    return block, terr_div, metric


def test_terr_div_str(terr_div_fixture):
    """ Проверка фикстур и совпадения с реальным файлом"""
    terr_div: TERR_DIV
    block, terr_div, metric = terr_div_fixture

    if terr_div is not None:
        assert metric["local_0"] in terr_div.name_local.title()
        assert metric["const_00"] == terr_div.const_00_or_01
        assert metric["const_01"] == terr_div.const_01
        assert metric["en_country_val"] == terr_div.en_country.value
        assert metric["li_nuts"] in repr(terr_div.li_NUTS)
        assert metric["unk_4"] == terr_div.unkn_4
        assert metric["unk_6"] == terr_div.unkn_6_mb_cnt
        assert metric["bladdr"] == terr_div.bladdr.value
    else:       # terr div none, dbrev 30
        assert metric["local_0"] is None


def test_terr_div_slots_are_effective(terr_div_fixture):
    """Проверяем, что оптимизированный terr_div жестко держит структуру слотов памяти."""
    block, terr_div, metric = terr_div_fixture

    if terr_div is not None:
        assert not hasattr(terr_div, '__dict__'), "Обнаружен __dict__! Проверьте __slots__ дочернего класса."
        assert hasattr(terr_div, '__slots__')
        assert 'name_local' in terr_div.__slots__
        assert 'vdo' in terr_div.__slots__
    else:
        # Для конфигураций без TERR_DIV тест завершается успешно
        pytest.skip("TERR_DIV отсутствует в данной конфигурации файла VDO")


# block_0x07 tests

def test_block_0x07_poi0_val(terr_div_fixture):
    """ Проверка референсного POI[0] """
    block: block_0x07
    block, terr_div, metric = terr_div_fixture

    poi0 = next(block.get_pois())

    assert metric["poi0_val"] == poi0.value


def test_block_0x07_poi_cat_qty(terr_div_fixture):
    """ Проверка количества POI"""
    block: block_0x07
    block, terr_div, metric = terr_div_fixture

    pois = [i for i in block.get_pois()]

    assert metric["cnt_pois"] == len(pois)


def test_block_0x07_li_poi(terr_div_fixture):
    """ li_poi читается верно"""
    block: block_0x07
    block, terr_div, metric = terr_div_fixture

    li_poi = repr(block.li_POI_cat)

    assert metric["li_POI_cat"] in li_poi


def test_block_0x07_li_countryes(terr_div_fixture):
    """ li_poi читается верно"""
    block: block_0x07
    block, terr_div, metric = terr_div_fixture

    if terr_div is not None:
        li_countryes = repr(block.li_countries)

        assert metric["li_countryes"] in li_countryes
    else:
        # Для конфигураций без TERR_DIV тест завершается успешно
        pytest.skip("TERR_DIV отсутствует, li_countryes - None")


def test_block_0x07_li_country_divisions(terr_div_fixture):
    """ li_poi читается верно"""
    block: block_0x07
    block, terr_div, metric = terr_div_fixture

    li_div = repr(block.li_country_divisions)

    assert metric["li_div"] in li_div


# ------------------- except

def test_block_0x07_init_wrong_dbrev():
    """При неверном vdo.dbrev"""
    vdo: VDO_FILE = VDO_FILE(FIXTURES_DIR / "carindb30_0h_9000h.bin")
    bla = BLADDR(struct_UINT.pack(0x201), vdo)

    bla.vdo.dbrev = 20

    with pytest.raises(ValueError, match='dbrev:'):
        block_0x07(bla)


@pytest.mark.parametrize("id_scale", [
    -5,
    12,
])
def test_block_0x07_find_wrong_id_scale(id_scale):
    """Для неправильного id_scale"""
    vdo: VDO_FILE = VDO_FILE(FIXTURES_DIR / "carindb30_0h_9000h.bin")
    bla = BLADDR(struct_UINT.pack(0x201), vdo)
    block = block_0x07(bla)
    srch = COORD(bytes.fromhex('13F919BE13DA074C'))

    res = block.find_by_coord(srch, id_scale)

    assert res is None


def test_block_0x07_find_empty_scale():
    """Для пустого scale"""
    vdo: VDO_FILE = VDO_FILE(FIXTURES_DIR / "carindb30_0h_9000h.bin")
    bla = BLADDR(struct_UINT.pack(0x201), vdo)
    block = block_0x07(bla)
    srch = COORD(bytes.fromhex('13F919BE13DA074C'))
    id_scale = 8
    res = block.find_by_coord(srch, id_scale)

    assert res is None


def test_block_0x07_find_real_scale(terr_div_fixture):
    """Для правильного id_scale"""
    block: block_0x07
    block, terr_div, metric = terr_div_fixture
    
    srch = COORD(bytes.fromhex('13F919BE13DA074C'))
    id_scale = 5

    with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'find_by_coord'"):
        block.find_by_coord(srch, id_scale)
        # уга, block08 - none, т.к. fixture
