import pytest   # noqa type: ignore

from QGIS_VDO.vdo.geotypes import POI_DETAILS


# ======================================================================
# block_0x10. POI_DETAILS — структура и поля
# ======================================================================

def test_poi_details_size_constant():
    """5.1 POI_DETAILS.size == 0x28"""
    assert POI_DETAILS.size == 0x28


def test_poi_details_slots():
    """5.2 POI_DETAILS имеет __slots__"""
    raw = bytes(0x28)
    det = POI_DETAILS(raw)
    assert not hasattr(det, '__dict__')


def test_poi_details_has_coord():
    """5.3 POI_DETAILS содержит coord"""
    raw = bytes(0x28)
    det = POI_DETAILS(raw)
    assert hasattr(det, 'coord')


def test_poi_details_has_li_road():
    """5.4 POI_DETAILS содержит li_road"""
    raw = bytes(0x28)
    det = POI_DETAILS(raw)
    assert hasattr(det, 'li_road')
