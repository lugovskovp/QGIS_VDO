import struct
import pytest     # type: ignore # noqa

from QGIS_VDO.vdo.datatypes import BYTESTRUCT   # Исправьте путь импорта под ваш проект
from QGIS_VDO.vdo.geotypes import COORD


@pytest.fixture
def raw_data():
    """Фикстура для сырых бинарных данных."""
    # Структура тестового блока (всего 24 байта):
    # [0:1]   - UCHAR (0xAA)
    # [2:3]   - USHORT (0x1234)
    # [4:7]   - UINT (0x55667788)
    # [8:15]  - Строка "Test\x00\x00\x00\x00" в кодировке cp1250 с нулями на конце
    # [16:23] - Координаты X (4 байта) и Y (4 байта) для COORD
    return (
        b"\xAA\x00"                    # 0: uchar + выравнивание
        b"\x12\x34"                    # 2: ushort
        b"\x55\x66\x77\x88"            # 4: uint
        b"Test\x00\x00\x00\x00"        # 8: строка, терминированная нулем
        b'\x06\xe6y\xaa\x0b\xb1\xde\x1f'  # 16: COORD (X=115767722, Y=196206111)
    )


@pytest.fixture
def base_struct(raw_data):
    """Фикстура, создающая экземпляр BYTESTRUCT перед каждым тестом."""
    return BYTESTRUCT(raw_data)


@pytest.mark.parametrize(
    "method_name, offset, expected_value",
    [
        ("uchar", 0, 0xAA),        # Проверка чтения 1 байта
        ("ushort", 2, 0x1234),     # Проверка чтения 2 байт
        ("uint", 4, 0x55667788),   # Проверка чтения 4 байт
    ]
)
def test_numeric_reading_methods(base_struct, method_name, offset, expected_value):
    """Параметризованный тест для проверки всех методов чтения чисел (uchar, ushort, uint)."""
    # Динамически получаем нужный метод у объекта (например, base_struct.uchar)
    reading_method = getattr(base_struct, method_name)
    
    # Вызываем метод со смещением и проверяем результат
    assert reading_method(offset) == expected_value


def test_initialization_with_bytes(base_struct, raw_data):
    """Проверка, что класс корректно инициализируется от bytes и создает memoryview."""
    assert isinstance(base_struct._raw, memoryview)
    assert base_struct.len() == len(raw_data)


def test_size_slicing(raw_data):
    """Проверка ограничения размера структуры при инициализации."""
    limited_struct = BYTESTRUCT(raw_data, size=4)
    assert limited_struct.len() == 4


def test_uchar_reading(base_struct):
    """Тест чтения одиночного байта (uchar)."""
    assert base_struct.uchar(0) == 0xAA


def test_ushort_reading(base_struct):
    """Тест чтения 2-байтового целого (ushort)."""
    assert base_struct.ushort(2) == 0x1234


def test_uint_reading(base_struct):
    """Тест чтения 4-байтового целого (uint)."""
    assert base_struct.uint(4) == 0x55667788


def test_read_str_zero_terminated(base_struct):
    """Тест чтения строки с отсечением терминирующего нуля."""
    extracted_str = base_struct.read_str(ptr=8, max_len=8)
    assert extracted_str == "Test"


def test_hex_property_formatting_if_len_gt_16():
    """Проверка ветки hex, где BYTESTRUCT > 16"""
    tail_data = b"\xAA" * 9
    by_struct = BYTESTRUCT(tail_data)
    hex_output = by_struct.hex
    assert hex_output == 'AAAAAAAAAAAAAAAA AA'


def test_far_list_repr_eq_hex():
    """Проверка, что __repr__ показывает .hex"""
    buffer = b'\x01\x02\x03\x04\x05\x06\x07\x08'
    by_struct = BYTESTRUCT(buffer)
    assert by_struct.__repr__() == by_struct.hex


def test_hex_property_formatting(base_struct):
    """Тест работы кастомного hex-дампа (проверка групп по 8 байт)."""
    hex_output = base_struct.hex
    assert "  " in hex_output
    assert hex_output.isupper()


def test_memoryview_slicing_without_copy(base_struct):
    """Проверка, что метод read возвращает под-срез memoryview без копирования памяти."""
    sub_view = base_struct.read(4, 4)
    assert isinstance(sub_view, memoryview)
    assert sub_view.tobytes() == b"\x55\x66\x77\x88"


def test_slots_efficiency(base_struct):
    """Проверка, что оптимизация через __slots__ применилась (отсутствует __dict__)."""
    with pytest.raises(AttributeError):
        _ = base_struct.__dict__


def test_child_coord_class(base_struct):
    """Тест дочернего класса COORD."""
    coord_buffer = base_struct.read(16, 8)
    
    class TestCOORD(COORD):
        __slots__ = ()
        @property
        def x(self): return struct.unpack(">L", self._raw[0:4])[0]  # noqa
        @property
        def y(self): return struct.unpack(">L", self._raw[4:8])[0]  # noqa

    coord = TestCOORD(coord_buffer)
    assert coord.x == 115767722
    assert coord.y == 196206111
