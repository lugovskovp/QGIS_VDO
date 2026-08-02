import pytest     # type: ignore # noqa

from QGIS_VDO.vdo.geotypes import VERTEX, VERTEX_struct
# from QGIS_VDO.vdo.datatypes import BYTESTRUCT
# from QGIS_VDO.vdo.enums import en_GEO_CATEGORY


# --- СРЕДА ДЛЯ ТЕСТИРОВАНИЯ ---
# VERTEX_struct = struct.Struct(">HH")

# --------------------------------------------------------------------------

def test_vertex_successful_unpack():
    """Проверяем стандартную распаковку валидных координат X и Y."""
    # 0x1A06 = 6662, 0x0082 = 130
    buf = bytearray(VERTEX_struct.pack(0x1A06, 0x0082))
    
    vtx = VERTEX(buf)
    
    assert vtx.x == 0x1A06
    assert vtx.y == 0x0082
    assert vtx.getXY() == (0x1A06, 0x0082)
    assert repr(vtx) == "1A06 0082"
    assert len(vtx._raw) == 4


def test_vertex_short_buffer_handling():
    """Проверяем, что класс безопасно обрабатывает слишком короткий буфер."""
    short_buf = bytearray(b"\x00\x1A")  # Всего 2 байта вместо 4
    
    vtx = VERTEX(short_buf)
    
    assert vtx.x is None
    assert vtx.y is None
    assert vtx.getXY() == (None, None)
    assert hasattr(vtx, '_raw')  # Базовый слот существует и не вызывает AttributeError
    assert repr(vtx) == "INVALID VERTEX (EMPTY BUF)"


def test_vertex_slots_optimization():
    """Проверяем отсутствие динамического словаря __dict__ у объекта."""
    buf = bytearray(VERTEX_struct.pack(10, 20))
    vtx = VERTEX(buf)
    
    assert not hasattr(vtx, '__dict__')
    
    with pytest.raises(AttributeError):
        vtx.dynamic_offset = 120  # type: ignore


def test_vertex_slots_contract():
    """Проверяем, что в слоты класса VERTEX добавлены только ожидаемые поля."""
    assert set(VERTEX.__slots__) == {'_x', '_y'}
