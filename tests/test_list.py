import pytest   # type: ignore

from QGIS_VDO.vdo.datatypes import LIST


def test_list_unpacking():
    """Тест корректного разделения 4 байт на указатель и счетчик."""
    # ptr = 0x0102, cnt = 0x0304
    buffer = b'\x01\x02\x03\x04'
    lst = LIST(buffer)
    
    assert lst.ptr == 0x0102
    assert lst.cnt == 0x0304


def test_list_repr():
    """Тест строкового представления (проверка на отсутствие ValueError)."""
    buffer = b'\x0A\x0B\x00\x05'
    lst = LIST(buffer)
    
    # Ожидаем формат УКАЗАТЕЛЬ:СЧЕТЧИК_HEX cnt:СЧЕТЧИК_DEC
    assert repr(lst) == "0A0B:0005 cnt:5"


def test_list_slots():
    """Проверка, что структура LIST не создает __dict__."""
    lst = LIST(b'\x00\x00\x00\x00')
    assert not hasattr(lst, '__dict__')
    
    with pytest.raises(AttributeError):
        lst.new_variable = "error"
