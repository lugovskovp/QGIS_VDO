import pytest   # type: ignore # noqa

# from pathlib import Path
# from unittest.mock import patch

from QGIS_VDO.vdo.datatypes import VDO_FILE
# from QGIS_VDO.vdo.geotypes import COORD

from QGIS_VDO.tests.fixtures import FIXTURES_DIR

EXPECTED_SINGLE_METRIC = {
    "carindb30_0h_9000h.bin": {
        'expected': {
            "len": 20,
            "p": (0x402, b'p', 1, 0x1100002),
        },
        "init": {"dbrev": 30, "segsize": 0x800},  # Передаем как позиционные аргументы по порядку
    },
    "carindb34_0h_6800h.bin": {
        'expected': {
            "len": 9,
            "p": (0x401, b'p', 1, 0x680001),
        },
        "init": {},  # Пустой словарь для дефолтных значений
    },
    "DB34_0h_3A01h.bin": {
        'expected': {
            "len": 17,
            "p": (0x803, b'p', 1, 0xD80002),
        },
        "init": {"dbrev": 34, "segsize": 0x800},  # Передаем как позиционные аргументы по порядку
    },
}


@pytest.fixture(
    scope="function",
    params=list(EXPECTED_SINGLE_METRIC),
    ids=list(EXPECTED_SINGLE_METRIC)
)
def vdo_fixture(request):
    filename = request.param
    metric = EXPECTED_SINGLE_METRIC[filename]
    
    # Динамически вычисляем путь
    file_path = FIXTURES_DIR / filename
    if not file_path.exists():  # pragma: no cover
        pytest.skip(f"Тестовый файл {filename} не найден по пути {file_path}, пропускаем.")

    # начала реальных фалов
    vdo = VDO_FILE(file_path)
    
    return vdo, metric['expected']

# ==================================================================


def test_vdo_get_ch_idxs(vdo_fixture):
    """Проверка правильности get_ch_idxs vdo"""
    from QGIS_VDO.vdo.blocks import block_0x12

    vdo, metric = vdo_fixture
    
    root: block_0x12 = vdo.get_block(0)
    fl_start = root.get_farlist_ch_country()

    curr_idx = vdo.get_ch_idxs(fl_start.bladdr.offset + fl_start.list.ptr, fl_start.list.cnt)
    
    assert len(curr_idx) == metric['len']
    assert curr_idx['p'] == metric['p']


"""
    bl_toc: block_0x12 = vdo.get_block(0)     # начало - в блоке 0 есть информация о расположении начала поиска стран
    fl_start = bl_toc.get_farlist_ch_country()

    curr_idx = vdo.get_ch_idxs(fl_start.bladdr.offset + fl_start.list.ptr, fl_start.list.cnt)

    chars = list(curr_idx)

    ch = 'p'    # choused interactive from UI from chars

    (int_bladr, ch, is_out, int_list) = curr_idx[ch]

    offset_bl = (int_bladr >> 8) * vdo.segsize
    offset_near = ((int_list & 0xFFFF0000) >> 16)
    # offset = (int_bladr >> 4) * vdo.segsize + ((int_list & 0xFFFF0000) >> 16)
    cnt = int_list & 0xFFFF
    if is_out:
        # farlist to address file (0x0a, 0x0c, 0x0e, 0x10)
        # /      curr_names = vdo.get_ch_names(offset_bl, offset_near, cnt)
        # пффф, 0x0a в ru34 - ziped
        block_addr: block_0x0A = vdo.get_block(offset_bl)
        li = LIST(struct_UINT.pack(int_list))
        curr_names = {x.name : x for x in block_addr.get_brifs(li)}
        pass
    else:
        # is_out == 0, to idxses
        curr_idx = vdo.get_ch_idxs(offset_bl + offset_near, cnt)
"""
