import pytest     # type: ignore # noqa

from QGIS_VDO.vdo.geotypes import GEO_SHAPE, GEO_SHAPE_struct
# from QGIS_VDO.vdo.datatypes import BYTESTRUCT
from QGIS_VDO.vdo.enums import en_GEO_CATEGORY


# Общий размер структуры для unpack одного элемента: 2+2+4+8+2+2+2+2+16 = 40 байт (0x28, что равно self.size * 2)
# GEO_SHAPE_struct = struct.Struct(">HHL8x2xHxxH16x")


# --- ЗАГЛУШКИ ДЛЯ СРЕДЫ ТЕСТИРОВАНИЯ ---
@pytest.fixture
def geo_shape_buffer_factory():
    """Фабрика для генерации бинарного буфера из двух последовательных GEO_SHAPE структур."""
    def _create(p_str, ptr_vrtx, shape_id, ptr_tstr, next_vrtx):
        # Первые 20 байт (текущий объект) + вторые 20 байт (для извлечения следующего ptr_vrtx)
        # Структура требует минимум 40 байт для успешного unpack_from со сдвигом,
        # либо мы упаковываем дважды, чтобы симулировать поток объектов.
        buf1 = GEO_SHAPE_struct.pack(p_str, ptr_vrtx, shape_id, ptr_tstr, next_vrtx)
        buf2 = GEO_SHAPE_struct.pack(0, next_vrtx, 0, 0, 0)
        return bytearray(buf1 + buf2)
    return _create


def test_geo_shape_initialization(geo_shape_buffer_factory):
    """Проверяем корректность парсинга полей и расчет количества вертексов."""
    # ptr_vrtx = 100, next_ptr_vrtx = 116. VRTX_OBJ_SIZE = 4.
    # cnt_vrtx = (116 - 100) / 4 = 4 вертекса.
    buf = geo_shape_buffer_factory(
        p_str=0x1234,
        ptr_vrtx=100,
        shape_id=7685,
        ptr_tstr=0x5678,
        next_vrtx=116
    )
    
    shape = GEO_SHAPE(buf, en_GEO_CATEGORY.FOREST)
    
    assert shape.p_str_name == 0x1234
    assert shape.ptr_vrtx == 100
    assert shape.cnt_vrtx == 4
    assert shape.id == 7685
    assert shape.ptr_tstr == 0x5678
    assert shape.cat == en_GEO_CATEGORY.FOREST
    assert len(shape._raw) == 20  # Строго 0x14 байт сохранено в родителе


def test_geo_shape_repr_output(geo_shape_buffer_factory):
    """Проверяем строковое представление класса."""
    buf = geo_shape_buffer_factory(0, 100, 1, 0, 120)  # (120-100)/4 = 5 вертексов
    shape = GEO_SHAPE(buf, en_GEO_CATEGORY.AMUSEMENT_PARK)
    
    expected = "AMUSEMENT_PARK:[5] Proto shape. Need read from parent"
    assert repr(shape) == expected
    assert str(shape) == expected


def test_geo_shape_slots_optimization(geo_shape_buffer_factory):
    """Убеждаемся, что __slots__ блокирует создание __dict__ и динамических полей."""
    buf = geo_shape_buffer_factory(0, 0, 0, 0, 4)
    shape = GEO_SHAPE(buf, en_GEO_CATEGORY.FOREST)
    
    assert not hasattr(shape, '__dict__')
    
    with pytest.raises(AttributeError):
        shape.new_dynamic_property = "disallowed"  # type: ignore


def test_geo_shape_slots_integrity():
    """Проверяем, что все необходимые свойства попали в объявление слотов."""
    expected_slots = {
        'p_str_name', 'ptr_vrtx', 'cnt_vrtx', 'id',
        'coord', 'ptr_tstr', 'name', 'cat'
    }
    assert set(GEO_SHAPE.__slots__) == expected_slots
