import pytest     # type: ignore # noqa
import struct

from QGIS_VDO.vdo.geotypes import POI_CATEGORY
from QGIS_VDO.vdo.datatypes import VDO_FILE, FAR_LIST
from QGIS_VDO.vdo.enums import en_POI_CAT


# --------------------------------------------------------------------------

def test_poi_category_successful_initialization():
    """Проверяем сборку POI_CATEGORY, чтение енамов и использование self.size."""
    mock_vdo = VDO_FILE()
    
    # Формируем 12 байт под структуру POI_CATEGORY
    buffer = bytearray(12)
    struct.pack_into(">H", buffer, 8, 0x0C)       # poi_type = Gas_station 0x0C
    struct.pack_into(">H", buffer, 10, 0x0A50)  # p_str = 0x0A50
    
    poi_cat = POI_CATEGORY(buffer, mock_vdo)
    
    assert isinstance(poi_cat.fl_POIs, FAR_LIST)
    assert poi_cat.fl_POIs.vdo is mock_vdo
    assert poi_cat.poi_type == en_POI_CAT.Gas_station
    assert poi_cat.p_str == 0x0A50
    assert poi_cat.size == 12
    assert len(poi_cat._raw) == 12


def test_poi_category_repr_formatting():
    """Проверяем корректность сборки отладочной строки."""
    mock_vdo = VDO_FILE()
    buffer = bytearray(12)
    struct.pack_into(">H", buffer, 8, 0x15)      # Hotel
    struct.pack_into(">H", buffer, 10, 0x12F0)
    
    poi_cat = POI_CATEGORY(buffer, mock_vdo)
    poi_cat.name = "Gazpromneft"
    
    expected = "Hotel [000000 00 virt : 0000:0000 cnt:0] -> 0x12F0: Gazpromneft"
    assert repr(poi_cat) == expected
    assert str(poi_cat) == expected


def test_poi_category_slots_optimization():
    """Гарантируем, что у класса POI_CATEGORY отсутствуют динамические словари."""
    mock_vdo = VDO_FILE()
    buffer = bytearray(12)
    struct.pack_into(">H", buffer, 8, 0x20)      # Museum 0x20
    poi_cat = POI_CATEGORY(buffer, mock_vdo)
    
    assert not hasattr(poi_cat, '__dict__')
    
    with pytest.raises(AttributeError):
        poi_cat.injected_runtime_attribute = "denied"  # type: ignore


def test_poi_category_slots_contract():
    """Проверяем точное совпадение контракта слотов класса."""
    assert set(POI_CATEGORY.__slots__) == {'fl_POIs', 'poi_type', 'p_str', 'name'}
