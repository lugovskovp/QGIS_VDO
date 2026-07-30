import pytest   # type: ignore

from QGIS_VDO.vdo.datatypes import PTR


@pytest.fixture
def zero_buffer() -> bytes:
    """Буфер с нулевым указателем."""
    return b'\x00\x00'


@pytest.fixture
def valid_buffer() -> bytes:
    """Буфер с указателем 0x0102 (Big-Endian)."""
    return b'\x01\x02'


@pytest.fixture
def max_buffer() -> bytes:
    """Буфер с максимальным 16-битным указателем 0xFFFF."""
    return b'\xFF\xFF'


@pytest.fixture
def dirty_buffer() -> bytes:
    """Буфер с лишними хвостами, чтобы проверить срез по size."""
    return b'\x0A\x0B\x0C\x0D\x0E'


def test_ptr_unpacking(valid_buffer, max_buffer):
    """Тест корректности извлечения Big-Endian значения из буфера."""
    ptr_normal = PTR(valid_buffer)
    assert ptr_normal.value == 0x0102
    
    ptr_max = PTR(max_buffer)
    assert ptr_max.value == 0xFFFF


def test_ptr_is_zero(zero_buffer, valid_buffer):
    """Тест свойства isZero для пустых и заполненных указателей."""
    ptr_zero = PTR(zero_buffer)
    assert ptr_zero.isZero is True
    
    ptr_active = PTR(valid_buffer)
    assert ptr_active.isZero is False


def test_ptr_string_representation(valid_buffer):
    """Тест __repr__ и свойства hexptr на корректность hex-форматирования (4 символа)."""
    ptr = PTR(valid_buffer)
    
    # Проверяем, что hexptr возвращает строку в верхнем регистре с префиксом
    assert ptr.hexptr == "0x0102"
    # Проверяем отладочный вывод
    assert repr(ptr) == "0x0102"


@pytest.mark.parametrize(
    "byte_data, expected_value, expected_str",
    [
        (b'\x00\x01', 1, "0x0001"),
        (b'\x00\x0F', 15, "0x000F"),
        (b'\x00\x10', 16, "0x0010"),
        (b'\x0A\x00', 0x0A00, "0x0A00"),
    ],
)
def test_ptr_padding_and_cases(byte_data, expected_value, expected_str):
    """Параметризованный тест для проверки дополнения нулями (padding) в hex."""
    ptr = PTR(byte_data)
    assert ptr.value == expected_value
    assert ptr.hexptr == expected_str


def test_ptr_buffer_slicing(dirty_buffer):
    """Проверка, что PTR жестко ограничивает размер буфера до 2 байт и не читает лишнего."""
    ptr = PTR(dirty_buffer)
    assert ptr.value == 0x0A0B  # Прочитались только первые 2 байта
    assert len(ptr._raw) == 2


def test_ptr_slots():
    """Проверка, что у класса PTR корректно работают __slots__ и не создается __dict__."""
    ptr = PTR(b'\x01\x02')
    assert not hasattr(ptr, '__dict__')
    
    # Попытка динамически добавить атрибут должна вызывать ошибку памяти
    with pytest.raises(AttributeError):
        ptr.custom_field = 42
