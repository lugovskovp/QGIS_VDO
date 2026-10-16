"""
Тесты для POI_ITEM — структуры данных POI-записи блока 0x06.

Поля POI_ITEM (28 байт, T[0x32]):
    0x00   4   BLOCK_ID of the 0x10 block
    0x04   2   byte offset within 0x10 block (S0 index record)
    0x06   2   LOCAL_X    position in tile, step 64
    0x08   2   LOCAL_Y    position in tile, step 64
    0x0A   2   CATEGORY
    0x0C   2   BRAND      offset of the POI's brand in name blob, 0 = no brand
    0x0E   2   0 or 1 on ports and airports
    0x10   4   POI_ID
    0x14   8   0          DB-REL 34 only
"""

import pytest
import struct

from QGIS_VDO.vdo.blocks.block_0x06 import POI_ITEM
from QGIS_VDO.vdo.enums import en_POI_CAT


# ------------------------------------------------------------------
# Фикстуры и константы
# ------------------------------------------------------------------

# Реальный POI_ITEM из базы:
#   _bladr10=0x00102030, _ptr10=0x0040, LOCAL_X=0x0100, LOCAL_Y=0x0200,
#   CATEGORY=12 (petrol), BRAND=0x0050, is_custom=0, id=0x00AABBCC, zero1=0, zero2=0
POI_ITEM_STRUCT = struct.Struct(">LHHHHHHLLL")

FAKE_BLADDR_10 = 0x00102030
FAKE_PTR10 = 0x0040
FAKE_LOCAL_X = 0x0100
FAKE_LOCAL_Y = 0x0200
FAKE_CATEGORY = 12  # petrol
FAKE_BRAND_PTR = 0x0050
FAKE_IS_CUSTOM = 0
FAKE_POI_ID = 0x00AABBCC
FAKE_ZERO1 = 0
FAKE_ZERO2 = 0

RAW_POI_ITEM = POI_ITEM_STRUCT.pack(
    FAKE_BLADDR_10, FAKE_PTR10, FAKE_LOCAL_X, FAKE_LOCAL_Y,
    FAKE_CATEGORY, FAKE_BRAND_PTR, FAKE_IS_CUSTOM,
    FAKE_POI_ID, FAKE_ZERO1, FAKE_ZERO2
)

# POI_ITEM без бренда (BRAND=0)
RAW_POI_ITEM_NO_BRAND = POI_ITEM_STRUCT.pack(
    FAKE_BLADDR_10, FAKE_PTR10, FAKE_LOCAL_X, FAKE_LOCAL_Y,
    FAKE_CATEGORY, 0, FAKE_IS_CUSTOM,
    FAKE_POI_ID, FAKE_ZERO1, FAKE_ZERO2
)

# POI_ITEM с non-zero zero1 (должен вызвать NotImplementedError)
RAW_POI_ITEM_ZERO1 = POI_ITEM_STRUCT.pack(
    FAKE_BLADDR_10, FAKE_PTR10, FAKE_LOCAL_X, FAKE_LOCAL_Y,
    FAKE_CATEGORY, FAKE_BRAND_PTR, FAKE_IS_CUSTOM,
    FAKE_POI_ID, 1, FAKE_ZERO2
)

# POI_ITEM с non-zero zero2
RAW_POI_ITEM_ZERO2 = POI_ITEM_STRUCT.pack(
    FAKE_BLADDR_10, FAKE_PTR10, FAKE_LOCAL_X, FAKE_LOCAL_Y,
    FAKE_CATEGORY, FAKE_BRAND_PTR, FAKE_IS_CUSTOM,
    FAKE_POI_ID, FAKE_ZERO1, 1
)


# ------------------------------------------------------------------
# Фикстуры
# ------------------------------------------------------------------

@pytest.fixture
def raw_poi_item():
    """Сырые байты POI_ITEM с полным набором данных."""
    return RAW_POI_ITEM


@pytest.fixture
def poi_item():
    """Экземпляр POI_ITEM с полным набором данных."""
    return POI_ITEM(RAW_POI_ITEM)


@pytest.fixture
def poi_item_no_brand():
    """Экземпляр POI_ITEM без бренда."""
    return POI_ITEM(RAW_POI_ITEM_NO_BRAND)


# ------------------------------------------------------------------
# Тесты: инициализация и слоты
# ------------------------------------------------------------------

def test_poi_item_slots_are_effective(poi_item):
    """Проверяем, что POI_ITEM использует __slots__ (нет __dict__)."""
    assert not hasattr(poi_item, '__dict__'), "POI_ITEM должен использовать __slots__"
    assert hasattr(POI_ITEM, '__slots__')
    expected_slots = (
        '_bladr10', '_ptr10', '_LOCAL_X', '_LOCAL_Y', '_cat',
        '_p_brand', 'is_custom', 'id',
        'brand', 'bladdr', 'coord', 'poi',
    )
    assert POI_ITEM.__slots__ == expected_slots


def test_poi_item_size_constant():
    """Проверяем, что размер POI_ITEM = 0x1C (28 байт)."""
    assert POI_ITEM.size == 0x1C
    assert POI_ITEM.size == 28


def test_poi_item_initialization_with_bytes(poi_item, raw_poi_item):
    """Проверяем базовую инициализацию от bytes и создание memoryview."""
    assert isinstance(poi_item._raw, memoryview)
    assert len(poi_item._raw) == len(raw_poi_item)


def test_poi_item_initialization_with_bytearray():
    """Проверяем инициализацию от bytearray."""
    item = POI_ITEM(bytearray(RAW_POI_ITEM))
    assert isinstance(item._raw, memoryview)
    assert item._bladr10 == FAKE_BLADDR_10


def test_poi_item_initialization_with_incorrect_type():
    """Проверяем отказ при невалидном типе буфера."""
    with pytest.raises(TypeError):
        POI_ITEM("not a buffer")  # noqa


# ------------------------------------------------------------------
# Тесты: распаковка полей
# ------------------------------------------------------------------

def test_poi_item_unpack_bladr10(poi_item):
    """Проверяем распаковку BLOCK_ID 0x10 блока."""
    assert poi_item._bladr10 == FAKE_BLADDR_10


def test_poi_item_unpack_ptr10(poi_item):
    """Проверяем распаковку указателя на S0 запись в 0x10 блоке."""
    assert poi_item._ptr10 == FAKE_PTR10


def test_poi_item_unpack_local_x(poi_item):
    """Проверяем распаковку LOCAL_X."""
    assert poi_item._LOCAL_X == FAKE_LOCAL_X


def test_poi_item_unpack_local_y(poi_item):
    """Проверяем распаковку LOCAL_Y."""
    assert poi_item._LOCAL_Y == FAKE_LOCAL_Y


def test_poi_item_unpack_category(poi_item):
    """Проверяем распаковку категории и конвертацию в enum."""
    assert poi_item._cat == en_POI_CAT(FAKE_CATEGORY)
    assert poi_item.cat == en_POI_CAT(FAKE_CATEGORY).name


def test_poi_item_unpack_brand_ptr(poi_item):
    """Проверяем распаковку указателя на бренд."""
    assert poi_item._p_brand == FAKE_BRAND_PTR


def test_poi_item_unpack_is_custom(poi_item):
    """Проверяем распаковку флага is_custom."""
    assert poi_item.is_custom == FAKE_IS_CUSTOM


def test_poi_item_unpack_poi_id(poi_item):
    """Проверяем распаковку POI_ID."""
    assert poi_item.id == FAKE_POI_ID


# ------------------------------------------------------------------
# Тесты: начальные значения ленивых полей
# ------------------------------------------------------------------

def test_poi_item_initial_brand_value(poi_item):
    """Проверяем начальное значение brand — пустая строка."""
    assert poi_item.brand == ''


def test_poi_item_initial_bladdr_value(poi_item):
    """Проверяем начальное значение bladdr — None."""
    assert poi_item.bladdr is None


def test_poi_item_initial_coord_value(poi_item):
    """Проверяем начальное значение coord — None."""
    assert poi_item.coord is None


def test_poi_item_initial_poi_value(poi_item):
    """Проверяем начальное значение poi — None."""
    assert poi_item.poi is None


# ------------------------------------------------------------------
# Тесты: обработка бренда
# ------------------------------------------------------------------

def test_poi_item_no_brand_ptr(poi_item_no_brand):
    """Проверяем POI_ITEM без бренда (BRAND_PTR=0)."""
    assert poi_item_no_brand._p_brand == 0
    assert poi_item_no_brand.brand == ''


def test_poi_item_brand_ptr_nonzero(poi_item):
    """Проверяем, что POI_ITEM с брендом имеет ненулевой указатель."""
    assert poi_item._p_brand == FAKE_BRAND_PTR


# ------------------------------------------------------------------
# Тесты: обработка zero1/zero2 (порты и аэропорты)
# ------------------------------------------------------------------

def test_poi_item_zero1_raises_not_implemented():
    """Проверяем NotImplementedError при non-zero zero1."""
    with pytest.raises(NotImplementedError, match=r"z1: 1, z2: 0"):
        POI_ITEM(RAW_POI_ITEM_ZERO1)


def test_poi_item_zero2_raises_not_implemented():
    """Проверяем NotImplementedError при non-zero zero2."""
    with pytest.raises(NotImplementedError, match=r"z1: 0, z2: 1"):
        POI_ITEM(RAW_POI_ITEM_ZERO2)


# ------------------------------------------------------------------
# Тесты: __repr__ и cat property
# ------------------------------------------------------------------

def test_poi_item_repr(poi_item):
    """Проверяем строковое представление."""
    repr_str = repr(poi_item)
    assert isinstance(repr_str, str)
    # brand пустой, cat — имя категории
    assert poi_item.cat in repr_str


def test_poi_item_cat_property(poi_item):
    """Проверяем property cat — возвращает имя категории."""
    assert poi_item.cat == en_POI_CAT(FAKE_CATEGORY).name


# ------------------------------------------------------------------
# Тесты: буферные протоколы
# ------------------------------------------------------------------

def test_poi_item_init_with_memoryview():
    """Проверяем инициализацию от memoryview."""
    buf = memoryview(RAW_POI_ITEM)
    item = POI_ITEM(buf)
    assert item._bladr10 == FAKE_BLADDR_10


def test_poi_item_raw_is_memoryview(poi_item):
    """Проверяем, что _raw — memoryview."""
    assert isinstance(poi_item._raw, memoryview)


def test_poi_item_raw_length(poi_item):
    """Проверяем длину _raw."""
    assert len(poi_item._raw) == POI_ITEM.size


# ------------------------------------------------------------------
# Тесты: различные категории POI
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "category_value, expected_name",
    [
        (12, en_POI_CAT(12).name),   # petrol
        (21, en_POI_CAT(21).name),   # hotels
        (37, en_POI_CAT(37).name),   # landmarks
        (48, en_POI_CAT(48).name),   # towns
    ]
)
def test_poi_item_various_categories(category_value, expected_name):
    """Проверяем различные категории POI."""
    raw = POI_ITEM_STRUCT.pack(
        0x00000001, 0x0010, 0x0000, 0x0000,
        category_value, 0, 0, 0x00000000, 0, 0
    )
    item = POI_ITEM(raw)
    assert item._cat.value == category_value
    assert item.cat == expected_name


# ------------------------------------------------------------------
# Тесты: граничные значения полей
# ------------------------------------------------------------------

def test_poi_item_max_poi_id():
    """Проверяем максимальное значение POI_ID (0xFFFFFFFF)."""
    raw = POI_ITEM_STRUCT.pack(
        0xFFFFFFFF, 0xFFFF, 0xFFFF, 0xFFFF,
        12, 0xFFFF, 0, 0xFFFFFFFF, 0, 0
    )
    item = POI_ITEM(raw)
    assert item.id == 0xFFFFFFFF
    assert item._LOCAL_X == 0xFFFF
    assert item._LOCAL_Y == 0xFFFF


def test_poi_item_min_values():
    """Проверяем минимальные значения (все нули кроме BLOCK_ID и en_POI_CAT)."""
    raw = POI_ITEM_STRUCT.pack(
        0x00000001, 0, 0, 0,
        0x0b, 0, 0, 0, 0, 0
    )
    item = POI_ITEM(raw)
    assert item._bladr10 == 0x00000001
    assert item._ptr10 == 0
    assert item._LOCAL_X == 0
    assert item._LOCAL_Y == 0
    assert item._p_brand == 0
    assert item.id == 0


# ------------------------------------------------------------------
# Тесты: производительность и память
# ------------------------------------------------------------------

def test_poi_item_no_dict_overhead(poi_item):
    """Проверяем отсутствие __dict__ — экономия памяти."""
    with pytest.raises(AttributeError):
        _ = poi_item.__dict__


def test_poi_item_memory_footprint():
    """Проверяем размер экземпляра POI_ITEM."""
    import sys
    item = POI_ITEM(RAW_POI_ITEM)
    # Без __dict__ размер должен быть значительно меньше
    size = sys.getsizeof(item)
    assert size < 200  # __slots__ сильно уменьшает размер
