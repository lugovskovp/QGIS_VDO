import pytest   # noqa type: ignore

from QGIS_VDO.vdo.geotypes import POI_BRIF


# ======================================================================
# block_0x10. POI_BRIF — структура и поля
# ======================================================================

def test_poi_brif_size_constant():
    """4.1 POI_BRIF.size == 8"""
    assert POI_BRIF.size == 8


def test_poi_brif_slots():
    """4.2 POI_BRIF имеет __slots__"""
    raw = bytes(8)
    brif = POI_BRIF(raw)
    assert not hasattr(brif, '__dict__')
    assert set(POI_BRIF.__slots__) == {'_ptr_name', 'alias', 'en_Lang', '_ptr_locality',
                                       '_ptr_more', 'name', 'locality'}


def test_poi_brif_init_with_bytes():
    """4.3 POI_BRIF инициализируется из байт"""
    # struct ">HBBHH": _ptr_name(H), alias(B), en_Lang(B), _ptr_locality(H), _ptr_more(H)
    raw = bytes([0x00, 0x01,   # _ptr_name = 1 (big-endian)
                 0x00,         # alias = 0
                 0x01,         # en_Lang = 1
                 0x00, 0x00,   # _ptr_locality = 0
                 0x00, 0x00])  # _ptr_more = 0
    brif = POI_BRIF(raw)
    assert brif._ptr_name == 1
    assert brif.alias == 0
    assert brif.en_Lang.value == 1
    assert brif._ptr_locality == 0
    assert brif._ptr_more == 0


def test_poi_brif_init_with_memoryview():
    """4.4 POI_BRIF инициализируется из memoryview"""
    raw = bytearray([0x00, 0x02, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00])
    mv = memoryview(raw)
    brif = POI_BRIF(mv)
    assert brif._ptr_name == 2


def test_poi_brif_init_with_alias():
    """4.5 POI_BRIF с is_alias=1"""
    raw = bytes([0x00, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00])
    brif = POI_BRIF(raw)
    assert brif.alias == 1


def test_poi_brif_repr():
    """4.6 POI_BRIF.__repr__ содержит язык и name"""
    raw = bytes([0x01, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00])
    brif = POI_BRIF(raw)
    brif.name = 'Test'
    repr_str = repr(brif)
    assert 'Test' in repr_str
