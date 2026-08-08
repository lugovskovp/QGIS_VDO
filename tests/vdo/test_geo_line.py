import pytest     # type: ignore # noqa

from QGIS_VDO.vdo.geotypes import GEO_LINE, GEO_LINE_struct
# from QGIS_VDO.vdo.datatypes import BYTESTRUCT
from QGIS_VDO.vdo.enums import en_GEO_CATEGORY


# >HHLHHHHxxH12x (общий размер 32 байта, что соответствует двум структурам по 16 байт)
# GEO_LINE_struct = struct.Struct(">HHLHHHHxxH12x")

@pytest.fixture
def geo_line_buffer_factory():
    """Фабрика для генерации последовательного бинарного буфера для GEO_LINE."""
    def _create(p_str, ptr_vrtx, line_id, poi, or_bc, tstr, country, next_vrtx):
        # Упаковываем текущую структуру (16 байт) и дополняем следующей структурой,
        # из которой извлекается поле next_ptr_vrtx (позиция 8-го аргумента)
        buf1 = GEO_LINE_struct.pack(p_str, ptr_vrtx, line_id, poi, or_bc, tstr, country, next_vrtx)
        buf2 = GEO_LINE_struct.pack(0, next_vrtx, 0, 0, 0, 0, 0, 0)
        return bytearray(buf1 + buf2)
    return _create


def test_geo_line_initialization(geo_line_buffer_factory):
    """Проверяем распаковку всех полей линии и математику вершин."""
    # Дельта вертексов: 200 - 160 = 40. При размере объекта 4 получаем: 40 / 4 = 10 вершин.
    buf = geo_line_buffer_factory(
        p_str=0x1111,
        ptr_vrtx=160,
        line_id=99999,
        poi=0x2222,
        or_bc=128,
        tstr=0x3333,
        country=7,
        next_vrtx=200
    )
    
    line = GEO_LINE(buf, en_GEO_CATEGORY.RAILWAY)
    
    assert line.p_str_name == 0x1111
    assert line.ptr_vrtx == 160
    assert line.id == 99999
    assert line.POI_regi == 0x2222
    assert line.or_b_or_c == 128
    assert line.tstr_name == 0x3333
    assert line.or_38_or_0_b_country == 7
    assert line.cnt_vrtx == 10
    assert line.cat == en_GEO_CATEGORY.RAILWAY
    assert len(line._raw) == 16  # Ровно 0x10 байт сохранено в родителе


def test_geo_line_strings(geo_line_buffer_factory):
    """Проверяем строковые методы отображения."""
    buf = geo_line_buffer_factory(0, 10, 1, 0, 0, 0, 0, 18)  # (18-10)/4 = 2 вершины
    line = GEO_LINE(buf, en_GEO_CATEGORY.BORDER)
    
    expected = "BORDER:[2] Proto line. Need read from parent"
    assert repr(line) == expected
    assert str(line) == expected


def test_geo_line_slots_optimization(geo_line_buffer_factory):
    """Проверяем отсутствие динамического словаря __dict__."""
    buf = geo_line_buffer_factory(0, 0, 0, 0, 0, 0, 0, 4)
    line = GEO_LINE(buf, en_GEO_CATEGORY.ROAD_PRIME)
    
    assert not hasattr(line, '__dict__')
    
    with pytest.raises(AttributeError):
        line.forbidden_attribute = "should_fail"  # type: ignore


def test_geo_line_slots_contract():
    """Проверяем, что состав слотов полностью соответствует спецификации класса."""
    expected_slots = {
        'p_str_name', 'ptr_vrtx', 'id', 'POI_regi', 'or_b_or_c',
        'tstr_name', 'or_38_or_0_b_country', 'cnt_vrtx', 'name', 'cat', 'vrtx',
    }
    assert set(GEO_LINE.__slots__) == expected_slots
