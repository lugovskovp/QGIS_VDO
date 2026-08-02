import pytest     # type: ignore # noqa

from QGIS_VDO.vdo.geotypes import TSTR, TSTR_struct
# from QGIS_VDO.vdo.datatypes import BYTESTRUCT
from QGIS_VDO.vdo.enums import en_CARINET_LANGUAGE


#TSTR_struct = struct.Struct(">Hbb")  # Формат: USHORT, SIGNED BYTE, SIGNED BYTE

# --------------------------------------------------------------------------

def test_tstr_initialization():
    """Проверяем стандартную распаковку полей TSTR и приведение типов."""
    # Упаковываем: p_str=0x1234, lang=0x15 (RUSSIAN), obj_type=8 (__street)
    buf = bytearray(TSTR_struct.pack(0x1234, 0x15, 8))
    
    tstr_obj = TSTR(buf)
    
    assert tstr_obj.p_str == 0x1234
    assert tstr_obj.lang == en_CARINET_LANGUAGE.Russian
    assert tstr_obj.geotype == "0x8"
    assert tstr_obj.name == "Proto. Name set where called"
    assert len(tstr_obj._raw) == 4


def test_tstr_repr_output():
    """Проверяем строковое представление отладочного вывода."""
    buf = bytearray(TSTR_struct.pack(0x0000, 2, 0x10))  # lang=2 (ENGLISH), obj_type=16 (__poliline -> 0x10)
    tstr_obj = TSTR(buf)
    tstr_obj.name = "Main Street"
    
    # en_CARINET_LANGUAGE.English.value = 2, .name = "ENGLISH", geotype = "0x10"
    expected = "2 0x10:[English]: Main Street"
    assert repr(tstr_obj) == expected
    assert str(tstr_obj) == expected


def test_tstr_slots_optimization():
    """Убеждаемся, что оптимизация памяти через __slots__ работает корректно."""
    buf = bytearray(TSTR_struct.pack(0, 1, 0))
    tstr_obj = TSTR(buf)
    
    # __dict__ не должен создаваться
    assert not hasattr(tstr_obj, '__dict__')
    
    # Попытка динамически добавить поле вызывает исключение
    with pytest.raises(AttributeError):
        tstr_obj.dynamic_translation = "forbidden"  # type: ignore


def test_tstr_slots_contract():
    """Проверяем, что в слоты класса TSTR добавлены только ожидаемые поля."""
    assert set(TSTR.__slots__) == {'p_str', 'lang', 'geotype', 'name'}
