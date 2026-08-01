import pytest   # type: ignore # noqa


from QGIS_VDO.vdo.datatypes import BLADDR
# from QGIS_VDO.vdo.blocks import block_0x12


@pytest.mark.parametrize("any_addr", [
    None,
    0,
    0x10,
    "strings not good choice here",
    BLADDR(b'\x00\x00\x02\x01')
])
def test_get_block_always_returns_none_when_vdo_is_empty(empty_vdo_fixture, any_addr):
    """Если VDO пустой/невалидный, get_block всегда возвращает None для любых аргументов"""
    empty_vdo, expected = empty_vdo_fixture
    
    assert empty_vdo.is_empty is expected["is_empty"]
    assert empty_vdo.get_block(any_addr) is None


def test_empty_vdo_slots_integrity(empty_vdo_fixture):
    """Проверяет работу __slots__ на пустом VDO / синглтоне"""
    empty_vdo, _ = empty_vdo_fixture
    
    assert not hasattr(empty_vdo, "__dict__")
    
    with pytest.raises(AttributeError):
        empty_vdo.new_arbitrary_property = 42
