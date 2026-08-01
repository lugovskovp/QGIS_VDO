import pytest   # type: ignore # noqa


from QGIS_VDO.vdo.datatypes import VDO_FILE, BLADDR
from QGIS_VDO.vdo.blocks import block_0x12


@pytest.mark.parametrize("invalid_addr", [
    None,                           # Аргумент None
    0x10,                           # Смещение не на начало настоящего блока
])
def test_get_block_returns_none_for_invalid_inputs(real_vdo_fixture, invalid_addr):
    """get_block возвращает None на некорректные смещения или None"""
    real_vdo, _ = real_vdo_fixture
    assert real_vdo.get_block(invalid_addr) is None


def test_get_block_returns_none_for_zero_bladdr(real_vdo_fixture):
    """get_block возвращает None, если у BLADDR взведен флаг isZero"""
    real_vdo, _ = real_vdo_fixture
    bla_zero = BLADDR(b'\x00' * 4, real_vdo)
    assert real_vdo.get_block(bla_zero) is None


def test_get_block_returns_none_out_of_file_bounds(real_vdo_fixture):
    """get_block возвращает None, если блок находится за пределами размера файла"""
    real_vdo, _ = real_vdo_fixture
    # Смещение гарантированно за пределами файла (0x11... в разы больше ваших размеров файлов)
    bla_out_of_bounds = BLADDR(b'\x11\x00\x02\x01')
    assert real_vdo.get_block(bla_out_of_bounds) is None


def test_get_block_raises_value_error_on_wrong_type(real_vdo_fixture):
    """get_block вызывает ValueError, если передан некорректный тип данных (str)"""
    real_vdo, _ = real_vdo_fixture
    with pytest.raises(ValueError, match="Неверный тип адреса"):
        real_vdo.get_block("strings not good choice here")


def test_get_block_successful_with_virtual_bladdr(real_vdo_fixture):
    """Успешное получение блока через виртуальный BLADDR"""
    real_vdo, expected = real_vdo_fixture
    bla = BLADDR(b'\x00\x00\x02\x01')
    
    block = real_vdo.get_block(bla)
    assert isinstance(block, expected["bl_201"])


def test_get_block_0x12_properties_and_types(real_vdo_fixture):
    """Проверка структуры, типов и repr() для считанного блока 0x12 (offset=0)"""
    real_vdo, expected = real_vdo_fixture
    
    bl_0x12 = real_vdo.get_block(0)
    
    assert isinstance(bl_0x12, block_0x12)
    assert isinstance(bl_0x12.bladdr_scales, BLADDR)
    assert repr(bl_0x12.area_A) == expected["bl_0x12.area_A"]


"""
Для проверки __slots__ в тестировании Python принято проверять два ключевых аспекта:
1. У экземпляра класса отсутствует атрибут __dict__ (это гарантирует, что память оптимизирована
    и динамически добавлять любые атрибуты нельзя).
2. Попытка записать произвольное («левое») свойство в объект вызывает исключение AttributeError.
"""


def test_vdo_file_has_no_dict(real_vdo_fixture):
    """Проверяет, что у класса VDO_FILE заблокирован __dict__ через __slots__"""
    real_vdo, _ = real_vdo_fixture
    
    # Успешно настроенный __slots__ полностью убирает __dict__ из объекта
    assert not hasattr(real_vdo, "__dict__")


def test_vdo_file_slots_prevent_dynamic_attributes(real_vdo_fixture):
    """Проверяет, что нельзя динамически добавить неперечисленный в __slots__ атрибут"""
    real_vdo, _ = real_vdo_fixture
    
    # При попытке создать новое свойство должно бросаться исключение AttributeError
    with pytest.raises(AttributeError):
        real_vdo.some_dynamic_random_attribute = "test_value"


@pytest.mark.parametrize("slot_name", [
    "file_path",
    "is_empty",
    "filename",
    "_initialized",
    "dbrev",
    "segsize",
    "file_size",
])
def test_vdo_file_allowed_slots_exist(real_vdo_fixture, slot_name):
    """Проверяет, что все заявленные в __slots__ атрибуты доступны на объекте"""
    real_vdo, _ = real_vdo_fixture
    
    # Проверяем, что класс содержит описание слота, либо объект имеет этот атрибут
    assert slot_name in VDO_FILE.__slots__
    assert hasattr(real_vdo, slot_name)
