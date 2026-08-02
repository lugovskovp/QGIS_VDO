import pytest     # type: ignore # noqa
# from unittest.mock import Mock

from QGIS_VDO.vdo.geotypes import GEO_CATEGORY, GEO_CATEGORY_struct
from QGIS_VDO.vdo.enums import en_GEO_CATEGORY, en_DRAW_TYPE


# --- ГЛОБАЛЬНАЯ ФИКСТУРА-ФАБРИКА ---
@pytest.fixture
def geo_cat_buffer_factory():
    """Фабрика для генерации 8-байтового буфера категории."""
    def _create(cat: int, draw: int, ptr: int, next_draw: int, next_ptr: int) -> bytearray:
        # >bbHxbH -> cat(b), draw(b), ptr(H), pad(x), next_draw(b), next_ptr(H)
        return bytearray(GEO_CATEGORY_struct.pack(cat, draw, ptr, next_draw, next_ptr))
    return _create


# --- ИЗОЛИРОВАННЫЕ ТЕСТЫ ---

def test_geo_category_shape_with_decrement(geo_cat_buffer_factory):
    """
    Тестируем draw=0 (SHAPE) и next_draw=1 (POLILINE).
    Разница указателей: 0x00A0 - 0x0000 = 160.
    obj_size для SHAPE = 20 (0x14).
    cnt = 160 / 20 = 8.
    Условие (not draw and next_draw) выполняется -> cnt должно стать 8 - 1 = 7.
    """
    buf = geo_cat_buffer_factory(
        cat=0x68,       # ROAD_HIGHWAY
        draw=0,         # SHAPE
        ptr=0x0000,
        next_draw=1,    # POLILINE
        next_ptr=0x00A0
    )
    
    geo_cat = GEO_CATEGORY(buf)
    
    assert geo_cat.category == en_GEO_CATEGORY.ROAD_HIGHWAY
    assert geo_cat.draw == en_DRAW_TYPE.SHAPE
    assert geo_cat.obj_size == 0x14
    assert geo_cat.cnt == 7
    assert geo_cat.ptr == 0x0000
    assert len(geo_cat._raw) == 4  # Проверяем, что размер _raw строго равен size (4)


def test_geo_category_polyline_no_decrement(geo_cat_buffer_factory):
    """
    Тестируем draw=1 (POLILINE) и next_draw=1.
    Разница указателей: 0x0040 - 0x0000 = 64.
    obj_size для POLILINE = 16 (0x10).
    cnt = 64 / 16 = 4.
    Условие уменьшения не выполняется -> cnt остается 4.
    """
    buf = geo_cat_buffer_factory(
        cat=2,       # FOREST
        draw=1,      # POLILINE
        ptr=0x0000,
        next_draw=1,
        next_ptr=0x0040
    )
    
    geo_cat = GEO_CATEGORY(buf)
    
    assert geo_cat.draw == en_DRAW_TYPE.POLILINE
    assert geo_cat.obj_size == 0x10
    assert geo_cat.cnt == 4


def test_geo_category_repr_and_str(geo_cat_buffer_factory):
    """Проверяем текстовый вывод __repr__ и __str__."""
    buf = geo_cat_buffer_factory(1, 0, 0x0010, 0, 0x0038)     # cnt = (56-16)/20 = 2
    geo_cat = GEO_CATEGORY(buf)
    
    expected_string = "SHAPE WATER[2] :0x10"
    assert repr(geo_cat) == expected_string
    assert str(geo_cat) == expected_string


def test_geo_category_slots_optimization(geo_cat_buffer_factory):
    """Убеждаемся, что оптимизация памяти через __slots__ работает."""
    buf = geo_cat_buffer_factory(1, 1, 0, 1, 16)
    geo_cat = GEO_CATEGORY(buf)
    
    # __dict__ не должен существовать
    assert not hasattr(geo_cat, '__dict__')
    
    # Нельзя добавлять левые атрибуты
    with pytest.raises(AttributeError):
        geo_cat.custom_field = 42  # type: ignore


def test_geo_category_slots_integrity():
    """Проверяем точный состав объявленных слотов."""
    expected_slots = {'category', 'draw', 'obj_size', 'cnt', 'ptr'}
    assert set(GEO_CATEGORY.__slots__) == expected_slots
