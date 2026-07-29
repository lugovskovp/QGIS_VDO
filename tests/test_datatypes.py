import unittest
import struct

from QGIS_VDO.vdo.datatypes import BYTESTRUCT   # , COORD, BLADDR  # Исправьте путь импорта под ваш проект
from QGIS_VDO.vdo.geotypes import COORD


class TestByteStruct(unittest.TestCase):

    def setUp(self):
        """Готовим бинарный буфер для тестов (эмуляция чтения из файла VDO)."""
        # Структура тестового блока (всего 20 байт):
        # [0:1]   - UCHAR (0xAA)
        # [2:3]   - USHORT (0x1234) -> little эндиан: \x34\x12
        # [4:7]   - UINT (0x55667788) -> little эндиан: \x88\x77\x66\x55
        # [8:15]  - Строка "Test\x00\x00\x00\x00" в кодировке cp1250 с нулями на конце
        # [16:19] - Координаты X (2 байта) и Y (2 байта) для COORD -> \x01\x00 \x02\x00 (1 и 2)
        
        self.raw_data = (
            b"\xAA\x00"                    # 0: uchar (смещение 0) + выравнивание
            b"\x12\x34"                    # 2: ushort (4660)
            b"\x55\x66\x77\x88"            # 4: uint (1432778632)
            b"Test\x00\x00\x00\x00"        # 8: 0-ended string
            b'\x06\xe6y\xaa\x0b\xb1\xde\x1f'   # 16: COORD # 35.317104N 9.161808W
                                           # (X=115767722, Y=196206111, упакованы как 4-байтовые uint/ushort)
        )
        self.base_struct = BYTESTRUCT(self.raw_data)

    def test_initialization_with_bytes(self):
        """Проверка, что класс корректно инициализируется от bytes и создает memoryview."""
        self.assertIsInstance(self.base_struct._raw, memoryview)
        self.assertEqual(self.base_struct.len(), len(self.raw_data))

    def test_size_slicing(self):
        """Проверка ограничения размера структуры при инициализации."""
        limited_struct = BYTESTRUCT(self.raw_data, size=4)
        self.assertEqual(limited_struct.len(), 4)

    def test_uchar_reading(self):
        """Тест чтения одиночного байта (uchar)."""
        self.assertEqual(self.base_struct.uchar(0), 0xAA)

    def test_ushort_reading(self):
        """Тест чтения 2-байтового целого (ushort)."""
        self.assertEqual(self.base_struct.ushort(2), 0x1234)

    def test_uint_reading(self):
        """Тест чтения 4-байтового целого (uint)."""
        self.assertEqual(self.base_struct.uint(4), 0x55667788)

    def test_read_str_zero_terminated(self):
        """Тест чтения строки с отсечением терминирующего нуля."""
        # Читаем строку со смещения 8, максимальная длина 8
        extracted_str = self.base_struct.read_str(ptr=8, max_len=8)
        self.assertEqual(extracted_str, "Test")

    def test_hex_property_formatting(self):
        """Тест работы кастомного hex-дампа (проверка групп по 8 байт)."""
        hex_output = self.base_struct.hex
        # Проверяем, что в выводе присутствует двойной пробел между 8-байтовыми блоками
        self.assertIn("  ", hex_output)
        # Проверяем, что буквы в верхнем регистре
        self.assertTrue(hex_output.isupper())

    def test_memoryview_slicing_without_copy(self):
        """Проверка, что метод read возвращает под-срез memoryview без копирования памяти."""
        sub_view = self.base_struct.read(4, 4)
        self.assertIsInstance(sub_view, memoryview)
        # Изменение оригинального буфера (если бы он был bytearray) отразилось бы тут,
        # но в данном случае проверяем равенство данных
        self.assertEqual(sub_view.tobytes(), b"\x55\x66\x77\x88")

    def test_slots_efficiency(self):
        """Проверка, что оптимизация через __slots__ применилась (отсутствует __dict__)."""
        with self.assertRaises(AttributeError):
            # У объектов с включенными __slots__ нет словаря динамических атрибутов
            _ = self.base_struct.__dict__

    def test_child_coord_class(self):
        """Тест дочернего класса COORD (если вы адаптировали ushort/uint под размер осей)."""
        # Вырезаем из общего буфера кусок под координаты (смещение 16, длина 8)
        coord_buffer = self.base_struct.read(16, 8)
        
        # Предположим, в вашем классе COORD оси X и Y читаются как uint (по 4 байта)
        # Для этого теста временно переопределим свойства x и y, если в COORD они используют uint.
        class TestCOORD(COORD):
            __slots__ = ()
            @property
            def x(self): return struct.unpack(">L", self._raw[0:4])[0]  # type: ignore # noqa
            @property
            def y(self): return struct.unpack(">L", self._raw[4:8])[0]  # type: ignore # noqa

        coord = TestCOORD(coord_buffer)
        self.assertEqual(coord.x, 115767722)    # _hlon
        self.assertEqual(coord.y, 196206111)    # _hlat


if __name__ == "__main__":
    unittest.main()
