import pytest   # type: ignore

from QGIS_VDO.vdo.datatypes import FAR_LIST


def test_far_list_unpacking(all_vdo_fixture):
    """Тест корректного разделения 8 байт на BLADDR и LIST."""
    custom_vdo, metric = all_vdo_fixture

    # Первые 4 байта: блок 0x000010, размер 0x01
    # Последующие 4 байта: ptr 0x0203, cnt 0x0405
    buffer = b'\x00\x00\x10\x01\x02\x03\x04\x05'
    
    far = FAR_LIST(buffer, vdo=custom_vdo)
    
    # Проверяем интеграцию с BLADDR
    assert far.bladdr.blocknumber == 16
    assert far.bladdr.segcnt == 1
    
    # Проверяем интеграцию с LIST
    assert far.list.ptr == 0x0203
    assert far.list.cnt == 0x0405


def test_far_list_init_vdo_none():
    """Тест инициализации None vdo"""
    buffer = b'\x00\x00\x02\x01\x00\x0A\x00\x01'

    far = FAR_LIST(buffer)

    assert far.vdo.is_empty
    

def test_far_list_offset_calculation(all_vdo_fixture):
    """Тест математики расчета абсолютного смещения в файле."""
    custom_vdo, metric = all_vdo_fixture

    # Пусть custom_vdo.segsize = 2048
    # Блок 2 (смещение 2 * 2048 = 4096). Смещение внутри списка = 10
    buffer = b'\x00\x00\x02\x01\x00\x0A\x00\x01'
    
    far = FAR_LIST(buffer, vdo=custom_vdo)
    assert far.offset == metric["segsize"] * 2 + 10


def test_far_list_identity_preservation(all_vdo_fixture):
    """Проверка, что свойства .bladdr и .list возвращают один и тот же объект в памяти."""
    custom_vdo, _ = all_vdo_fixture

    buffer = b'\x01\x02\x03\x04\x05\x06\x07\x08'
    far = FAR_LIST(buffer, vdo=custom_vdo)
    
    # Сохраняем ссылки при первом вызове
    first_bladdr = far.bladdr
    first_list = far.list
    
    # Проверяем, что повторный вызов возвращает те же самые объекты (is)
    assert far.bladdr is first_bladdr
    assert far.list is first_list


def test_far_list_repr_eq_hex(all_vdo_fixture):
    """Проверка, что __repr__ показывает .hex"""
    custom_vdo, _ = all_vdo_fixture
    buffer = b'\x01\x02\x03\x04\x05\x06\x07\x08'
    far = FAR_LIST(buffer, vdo=custom_vdo)

    assert repr(far) == far.hex


def test_far_list_slots(empty_vdo_fixture):
    """Проверка, что структура FAR_LIST и её компоненты защищены от __dict__."""
    empty_vdo, _ = empty_vdo_fixture
    far = FAR_LIST(b'\x00' * 8, vdo=empty_vdo)
    
    # Проверяем сам композит
    assert not hasattr(far, '__dict__')
    # Проверяем вложенные свойства на отсутствие утечек памяти
    assert not hasattr(far.bladdr, '__dict__')
    assert not hasattr(far.list, '__dict__')
    
    with pytest.raises(AttributeError):
        far.arbitrary_field = True
