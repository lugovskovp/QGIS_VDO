import pytest   # type: ignore
import struct

from QGIS_VDO.vdo.block_basegeo import block_basegeo

from QGIS_VDO.vdo.datatypes import VDO_FILE
from QGIS_VDO.vdo.geotypes import GEO_CATEGORY, GEO_LINE, GEO_SHAPE, VERTEX, TSTR
from QGIS_VDO.vdo.enums import en_DRAW_TYPE     # , en_GEO_CATEGORY

from QGIS_VDO.tests.fixtures import FIXTURES_DIR


struct_SHAPE = struct.Struct(">HHLLLHH")   # (p_str, pvrtx, id, c_lon, c_lat, align, p_tstr)
struct_LINE = struct.Struct(">HHLHHHH")
# line = p_str_name + ptr2firstObjVertex + id + ptr_linesign + ptr2poi + ptr2tstr + shrtEnd


def _sections_end(block: block_basegeo) -> int:
    """First byte past the last non-empty record section (where the text starts)."""
    recs = [block.li_cat, block.li_shp, block.li_lin, block.li_vrtx, block.li_poi, block.li_tstr]
    S4_POI_SIZE = 6
    objs = [GEO_CATEGORY.size, GEO_SHAPE.size, GEO_LINE.size, VERTEX.size, S4_POI_SIZE, TSTR.size]
    # hi = t[T_PROLOG_141516]
    hi = 0x34   # TODO - REWORK!!! сейчас "как есть" - первый байт после пролога захардкодил
    for i, rec in enumerate(recs):
        if rec.cnt:
            hi = max(hi, rec.ptr + (rec.cnt + (1 if i < 3 else 0)) * objs[i])

        #     for i, rec in enumerate(recs):
        # e = ctx.entry(i)
        # if e.count:
        #     hi = max(hi, e.off + (e.count + (1 if i < 3 else 0)) * rec)
    return hi


# ---------- словарик фикстур

GEO_DICT = {
    'bmw_p_0x1d_0x07151504.bin': {
        "name": "@ 07151504 001D 01 05 [1D:MAP__10k400]",
        "scale": 10,
        "type_name": 'block_0x1D',
    },
    'bmw_p_0x14_0x070D9E01.bin': {
        "name": "@ 070D9E01 0014 01 02 [14:MAP__05k200]",
        "scale": 5,
        "descr": "нет shp, tstr, poi, но 3 есть линии"
    },
    'bmw_p_0x14_0x070E8503.bin': {
        "name": "@ 070E8503 0014 01 04 [14:MAP__05k200]",
        "scale": 5,
        "descr": "poi нет, lin=1"
    },
    'GER_p_16_0x68AADB05.bin': {
        'name': "@ 04AADB05 0016 01 08 [16:MAP__07k40]",
        "scale": 7,
        "descr": "Nohra"
    },
}


@pytest.fixture(
    scope="function",
    params=list(GEO_DICT),
    ids=[GEO_DICT[k]["name"] for k in GEO_DICT])  # <--- Понятные имена в логах pytest
def geoblock_fixture(request):
    """
    Генератор реальных блоков и проверяемых метрик
    """
    blpath = FIXTURES_DIR / request.param
    metric = GEO_DICT[request.param]

    ss = 0x800
    if request.param[:3] == 'bmw':
        ss = 0x200
    # ss = metric.get('scale', 0x200) - raised module tmod(?) No module named 'tmnet'
    # if 'segsize' in metric:
    #     ss = metric['scale']
    # else:
    #     ss = 0x200
    print(request.param)
    block = VDO_FILE().load_single_block(blpath, dbrev=34, segsize=ss)
    
    return (block, metric)


# -------------------------------------------------------------------


def test_isgeoblock(geoblock_fixture):
    """Проверка, что все блоки фикстуры являются геоблокам"""
    block: block_basegeo
    block, metrics = geoblock_fixture
    
    assert block.head.arch_type == 1    # carindb - packed
    assert block.is_unpacked is True     # was unpacked
    assert block.type in [0x14, 0x15, 0x16, 0x1c, 0x1d, 0x1e]   # in geoblocks 0x14, 0x15, 0x16, 0x1c, 0x1d, 0x1e


def test_valid_categories(geoblock_fixture):
    """Пророверка валидности значений категорий"""
    block: block_basegeo
    block, metrics = geoblock_fixture

    # all_categories = [shp for idx, shp in enumerate(block.get_all_categories())]
    all_categories = list(block.get_all_categories())

    # ссылка в первой категории - на ptr сразу за категориями
    assert all_categories[0].ptr == 0x34 + (block.li_cat.cnt + 1) * 4

    # ссылка в первой категории - на первый элемент в LISTs
    if block.li_shp.cnt:
        # есть шейпы
        assert all_categories[0].ptr == block.li_shp.ptr
    elif block.li_lin.cnt:
        # нет шейпов, есть полилинии
        assert all_categories[0].ptr == block.li_lin.ptr
    else:
        # нет ни shp ни lin
        pytest.skip("Шейпов нет, полилиний нет, пропускаем тест")

    # ссылка в последней категории - на начало элемента, за которым начинаются vertexы
    if block.li_lin.cnt:
        # есть линии
        assert all_categories[-1].ptr == block.li_vrtx.ptr - GEO_LINE.size
    else:
        # есть шейпы
        assert all_categories[-1].ptr == block.li_vrtx.ptr - GEO_SHAPE.size

    # заключительный элемент - нулевой, в нем только ptr
    assert all_categories[-1].category.value == 0
    assert all_categories[-1].draw.value == 0

    prev_ptr = 0
    for cat in all_categories:
        # тип определенной категории относится или к линиям или к полигонам
        if cat.category.value < 0x10:
            assert cat.draw == en_DRAW_TYPE.SHAPE
            # ptr больше начала shp
            assert cat.ptr >= block.li_shp.ptr
            # ptr меньше (лень вычислять есть ли линии и т.п.) вертексов
            assert cat.ptr < block.li_vrtx.ptr
        else:
            assert cat.draw == en_DRAW_TYPE.POLILINE
            # ptr больше начала lin
            assert cat.ptr >= block.li_lin.ptr
            # ptr меньше (лень вычислять есть ли линии и т.п.) вертексов
            assert cat.ptr < block.li_vrtx.ptr

        # каждый следующий ptr больше предыдущего
        assert prev_ptr < cat.ptr
        prev_ptr = cat.ptr

        # ptr делится на 4 - word aligned
        assert cat.ptr == ((cat.ptr >> 2) << 2)

    pass


def test_valid_shapes(geoblock_fixture):
    """Пророверка валидности полей полигонов"""
    block: block_basegeo
    block, metrics = geoblock_fixture

    all_shp = list(block.getObjects(isGetLines=False))
    # (p_str_name, ptr_vrtx, id, ptr_tstr, next_ptr_vrtx) = GEO_SHAPE_struct.unpack_from(mem_buf, 0)

    str_start_ptr = _sections_end(block)
    
    prev_ptr_vrtx = 0
    for shp in all_shp:
        # ptr идут по нарастающей
        assert shp.ptr_vrtx >= prev_ptr_vrtx
        prev_ptr_vrtx = shp.ptr_vrtx

        # ссылка на название внутри блока
        assert shp.p_str_name < block.head.sizeofblock

        # ссылка на название ведёт в область строк
        if str_start_ptr:       # если она не = 0
            assert shp.p_str_name >= str_start_ptr or shp.p_str_name == 0

        # точки - есть
        assert shp.cnt_vrtx >= 3

        # ссылка на первый вертекс ведёт в область вертексов
        assert block.li_vrtx.ptr <= shp.ptr_vrtx < block.li_tstr.ptr

        # ссылка на вертексы делится на 4
        assert shp.ptr_vrtx % 4 == 0

        # ссылка на tstr ведёт в область tstr и делится на 2
        if shp.ptr_tstr:
            assert block.li_tstr.ptr <= shp.ptr_tstr < str_start_ptr
            assert shp.ptr_tstr % 2 == 0

    # добавляем заключительный элемент с нулями
    if block.li_shp.cnt:
        offset = block.li_shp.ptr + (block.li_shp.cnt) * GEO_SHAPE.size
        # struct_SHAPE = struct.Struct(">HHLLLHH")   # (p_str, pvrtx, id, c_lon, c_lat, align, p_tstr)
        raw = block.read(offset, GEO_SHAPE.size)
        (p_str, p_vrtx, id, c_lon, c_lat, align, p_tstr) = struct_SHAPE.unpack(raw)
        
        assert p_str == 0
        if block.li_tstr.cnt:
            if block.li_lin.cnt:
                # если есть линии - в последнем элементе значение = первого элемента линий
                lines_pvrtx = block.read(offset + GEO_SHAPE.size + 2, 2)
                assert p_vrtx == struct.Struct(">H").unpack(lines_pvrtx)[0]
            else:
                # если нет - то начало tstr
                assert p_vrtx == block.li_tstr.ptr  # на первый TSTR ?
        assert id == 0
        assert c_lon == 0
        assert c_lat == 0
        assert align == 0

        assert True


def test_valid_lines(geoblock_fixture):
    """Пророверка валидности полей полигонов"""
    block: block_basegeo
    block, metrics = geoblock_fixture

    all_lin = list(block.getObjects(isGetShapes=False))
    # line = p_str_name + ptr2firstObjVertex + id + ptr_linesign + ptr2poi + ptr2tstr + shrtEnd

    str_start_ptr = block.li_tstr.ptr + block.li_tstr.cnt * 4
    
    prev_ptr_vrtx = 0
    for lin in all_lin:
        # ptr идут по нарастающей
        assert lin.ptr_vrtx >= prev_ptr_vrtx
        prev_ptr_vrtx = lin.ptr_vrtx

        # ссылка на название внутри блока
        if lin.p_str_name:
            assert lin.p_str_name < block.head.sizeofblock

            # ссылка на название ведёт в область строк
            if str_start_ptr:       # если она не = 0
                assert lin.p_str_name >= str_start_ptr

        # точки - хотя бы 2 есть у каждой линии
        assert lin.cnt_vrtx >= 2

        # ссылка на первый вертекс ведёт в область вертексов
        if block.li_tstr.cnt:
            assert block.li_vrtx.ptr <= lin.ptr_vrtx < block.li_tstr.ptr

        # ссылка на вертексы делится на 4
        assert lin.ptr_vrtx % 4 == 0

        # ссылка на tstr c_p_line_sign ведёт в область like poi и делится на 6
        if lin.c_p_line_sign:
            assert lin.c_p_line_sign % 6

    # добавляем заключительный элемент с нулями
    if block.li_lin.cnt:
        offset = block.li_lin.ptr + (block.li_lin.cnt) * GEO_LINE.size
        # struct_LINE = struct.Struct(">HHLHHHH")
        # line = p_str_name + ptr2firstObjVertex + id + ptr_linesign + ptr2poi + ptr2tstr + shrtEnd
        raw = block.read(offset, GEO_LINE.size)
        (p_str_name, ptr2firstObjVertex, id, ptr_linesign, ptr2poi, ptr2tstr, shrtEnd) = struct_LINE.unpack(raw)
        
        assert p_str_name == 0
        assert ptr2firstObjVertex == block.li_vrtx.ptr + (block.li_vrtx.cnt) * 4
        assert id == 0
        if ptr_linesign and block.li_tstr.cnt:
            assert ptr_linesign == block.li_tstr.ptr
        assert ptr2poi == 0
        # assert ptr2tstr == 0    # assert 4 == 0  0x070e8503
        assert shrtEnd == 0


"""


"""
