import pytest   # type: ignore # noqa
import os


from QGIS_VDO.vdo.datatypes import BLADDR, VDO_FILE
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
    # QGISvdoGroupName
    assert empty_vdo.QGISvdoGroupName is None


def test_empty_vdo_slots_integrity(empty_vdo_fixture):
    """Проверяет работу __slots__ на пустом VDO / синглтоне"""
    empty_vdo, _ = empty_vdo_fixture
    
    assert not hasattr(empty_vdo, "__dict__")
    
    with pytest.raises(AttributeError):
        empty_vdo.new_arbitrary_property = 42


def test_vdo_file_init_too_small_file():
    """Проверка создания пустого синглтона на слишком маленьком файле"""
    filename = 'too_small_carindb.bin'
    # тестовые файлы лежат в папке с тестами
    file_path = f"tests/fixtures/{filename}"
    
    # Дополнительная проверка на случай, если файла физически нет на диске
    if not os.path.exists(file_path):             # pragma: no cover
        pytest.skip(f"Тестовый файл {filename} не найден на диске, пропускаем.")

    empty_vdo = VDO_FILE()
    test_vdo = VDO_FILE(file_path)

    assert empty_vdo is test_vdo


def test_vdo_file_init_first_bl_not_0x12():
    """Проверка создания vdo, если первые 4 байта не 00 00 00 01"""
    filename = 'block_0x13_v30.bin'
    # тестовые файлы лежат в папке с тестами
    file_path = f"tests/fixtures/{filename}"
    
    # Дополнительная проверка на случай, если файла физически нет на диске
    if not os.path.exists(file_path):             # pragma: no cover
        pytest.skip(f"Тестовый файл {filename} не найден на диске, пропускаем.")

    empty_vdo = VDO_FILE()
    test_vdo = VDO_FILE(file_path)

    assert empty_vdo is test_vdo
