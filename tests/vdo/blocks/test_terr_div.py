import pytest
# from unittest.mock import MagicMock

from QGIS_VDO.vdo.datatypes import VDO_FILE
# from QGIS_VDO.vdo.geotypes import COORD
from QGIS_VDO.vdo.blocks import block_0x07, block_0x12
from QGIS_VDO.vdo.blocks.block_0x07 import TERR_DIV
# from QGIS_VDO.vdo.consts import struct_UINT, struct_WORD

from QGIS_VDO.tests.fixtures import FIXTURES_DIR


# --- Настройки окружения и фикстуры ---

VDO_DICT = {
    "carindb30_0h_9000h.bin": {
        "name": "ru30",
        "local_0": None,
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
        assert metric["local_0"] in terr_div.name_local
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
