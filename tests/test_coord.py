import unittest
import struct
# from collections.abc import ReadableBuffer
# from vdo.bytestruct import BYTESTRUCT, COORD  # Настройте импорт под ваш проект
from QGIS_VDO.vdo.geotypes import COORD
from QGIS_VDO.vdo.datatypes import BYTESTRUCT

# Дублируем константы для сверки в тестах
MULCOORD = 5555554
DOUBLE_BYTES_CNT = 8


class TestCoord(unittest.TestCase):

    def test_init_from_bytes_positive(self):
        """Тест инициализации из байт (Big-Endian): положительные координаты (N, E)"""
        # Задаем численные значения
        hlon = int((30 + 37.6173) * MULCOORD)  # ~37.6173° E
        hlat = int(55.7558 * MULCOORD)         # ~55.7558° N
        
        # Упаковываем в Big-Endian (>LL)
        raw_bytes = struct.pack(">LL", hlon, hlat)
        
        coord = COORD(raw_bytes)
        
        # Проверяем точность восстановления градусов
        self.assertAlmostEqual(coord.lon, 37.6173, delta=0.0001)
        self.assertAlmostEqual(coord.lat, 55.7558, delta=0.0001)

    def test_vdo_reference_coordinates(self):
        """Проверка эталонных бинарных данных VDO на реальных координатах (Big-Endian)."""
        # 1. Задаем исходные эталонные байты VDO
        sa1 = b'\x06\xe6y\xaa\x0b\xb1\xde\x1f'
        sa2 = b'\nlvM\x10_\xf3\xf9'
        sa3 = b'\xf1\x190\x00\xbczP\x00'
        sa4 = b'Q\x190\x00\x1czP\x00'

        # 2. Инициализируем объекты COORD
        c1 = COORD(sa1)
        c2 = COORD(sa2)
        c3 = COORD(sa3)
        c4 = COORD(sa4)

        # Допустимая дельта для шестого знака после запятой (микроокругления)
        coord_delta = 0.000001

        # 3. Валидация c1 (Ожидается: 35.317104N 9.161808W)
        # Так как W — это западная долгота, c1.lon должен быть отрицательным
        self.assertAlmostEqual(c1.lat, 35.317104, delta=coord_delta)
        self.assertAlmostEqual(c1.lon, -9.161808, delta=coord_delta)
        self.assertEqual(repr(c1), "35.317104N 9.161808W")

        # 4. Валидация c2 (Ожидается: 49.450295N 1.478463E)
        self.assertAlmostEqual(c2.lat, 49.450295, delta=coord_delta)
        self.assertAlmostEqual(c2.lon, 1.478463, delta=coord_delta)
        self.assertEqual(repr(c2), "49.450295N 1.478463E")

        # 5. Валидация c3 (Ожидается: 203.910287S 75.001364W)
        # S и W — юг и запад, оба значения градусов в c3.lat и c3.lon отрицательные
        self.assertAlmostEqual(c3.lat, -203.910287, delta=coord_delta)
        self.assertAlmostEqual(c3.lon, -75.001364, delta=coord_delta)
        self.assertEqual(repr(c3), "203.910287S 75.001364W")

        # 6. Валидация c4 (Ожидается: 86.000034N 214.908958E)
        self.assertAlmostEqual(c4.lat, 86.000034, delta=coord_delta)
        self.assertAlmostEqual(c4.lon, 214.908958, delta=coord_delta)
        self.assertEqual(repr(c4), "86.000034N 214.908958E")

    def test_init_from_bytes_negative(self):
        """Тест инициализации из байт: отрицательные координаты (S, W)"""
        # Нью-Йорк: ~74.0060° W, ~40.7128° N
        # Долгота: (30 + (-74.0060)) * MULCOORD -> отрицательное число для знакового int
        hlon_signed = int((30 + (-74.0060)) * MULCOORD)
        hlat_signed = int(40.7128 * MULCOORD)
        
        # Переводим в беззнаковые dword для упаковки (& 0xFFFFFFFF)
        hlon_unsigned = hlon_signed & 0xFFFFFFFF
        hlat_unsigned = hlat_signed & 0xFFFFFFFF
        
        raw_bytes = struct.pack(">LL", hlon_unsigned, hlat_unsigned)
        coord = COORD(raw_bytes)
        
        self.assertAlmostEqual(coord.lon, -74.0060, delta=0.0001)
        self.assertAlmostEqual(coord.lat, 40.7128, delta=0.0001)

    def test_init_from_ints(self):
        """Тест инициализации через два целых числа (hlo, hla)"""
        # Передаем напрямую hlon и hlat
        coord = COORD(375555400, 310000000)
        
        self.assertEqual(coord._hlon, 375555400)
        self.assertEqual(coord._hlat, 310000000)
        # Проверяем, что базовый _raw тоже сформировался корректно (8 байт)
        self.assertEqual(len(coord._raw), DOUBLE_BYTES_CNT)

    def test_init_from_floats(self):
        """Тест инициализации через два float (градусы)"""
        lon_val = 27.5555
        lat_val = -53.3333
        
        coord = COORD(lon_val, lat_val)
        
        # Проверяем, что значения корректно вернулись обратно
        self.assertAlmostEqual(coord.lon, lon_val, places=6)
        self.assertAlmostEqual(coord.lat, lat_val, places=6)

    def test_repr_formatting(self):
        """Тест строкового отображения __repr__ для отладки"""
        coord_ne = COORD(10.5, 20.5)
        self.assertEqual(repr(coord_ne), "20.500000N 10.500000E")
        
        coord_sw = COORD(-10.5, -20.5)
        self.assertEqual(repr(coord_sw), "20.500000S 10.500000W")

    def test_equality(self):
        """Тест сравнения двух объектов COORD (__eq__)"""
        coord1 = COORD(12.3456, 65.4321)
        coord2 = COORD(12.3456, 65.4321)
        coord3 = COORD(12.0000, 65.0000)
        
        self.assertEqual(coord1, coord2)
        self.assertNotEqual(coord1, coord3)
        self.assertNotEqual(coord1, "not_a_coord_object")

    def test_child_coord_class(self):
        """Тест дочернего класса COORD: извлечение из общего буфера и расчет градусов."""
        # Задаем исходные тестовые координаты (в градусах)
        target_lon = 37.6173
        target_lat = 55.7558
        
        # Переводим в беззнаковые dword целые числа, как это делает формат VDO
        hlon = int((30 + target_lon) * MULCOORD) & 0xFFFFFFFF
        hlat = int(target_lat * MULCOORD) & 0xFFFFFFFF
        
        # Собираем эмуляцию большого бинарного файла (24 байта)
        # Координаты COORD (8 байт) будут лежать внутри него со смещения 16
        large_file_data = (
            b"\x00" * 16 +                   # [0:15]   - какие-то другие данные блока   # noqa
            struct.pack(">LL", hlon, hlat)   # [16:23]  - наши 2 dword структуры COORD (Big-Endian)
        )
        
        # Инициализируем базовый класс BYTESTRUCT всем файлом
        main_block = BYTESTRUCT(large_file_data)
        
        # Извлекаем срез памяти под координаты без копирования байт
        coord_buffer = main_block.read(16, COORD.size)
        
        # Инициализируем реальный дочерний класс COORD от полученного memoryview
        coord = COORD(coord_buffer)
        
        # Проверяем, что COORD корректно прочитал данные из среза и посчитал градусы
        self.assertIsInstance(coord._raw, memoryview)
        self.assertEqual(coord.len(), DOUBLE_BYTES_CNT)
        self.assertAlmostEqual(coord.lon, target_lon, delta=0.0001)
        self.assertAlmostEqual(coord.lat, target_lat, delta=0.0001)

    def test_delta(self):
        """Тест вычисления дельты между точками"""
        coord1 = COORD(10.0, 20.0)
        coord2 = COORD(12.5, 21.1)
        
        # Разница: lat = -1.1, lon = -2.5
        res = coord1.delta(coord2)
        self.assertEqual(res, "lat:-1.10° x lon:-2.50°")

    def test_slots_and_dict_absence(self):
        """Проверка жесткой оптимизации памяти через __slots__"""
        coord = COORD(0.0, 0.0)
        # У оптимизированного класса должен отсутствовать динамический словарь __dict__
        with self.assertRaises(AttributeError):
            _ = coord.__dict__

    def test_invalid_arguments_raise_error(self):
        """Проверка вызова исключения при передаче невалидных типов"""
        with self.assertRaises(ValueError):
            # Передаем строку вместо float/int во второй аргумент
            COORD(55.123, "строка")  # type: ignore


if __name__ == "__main__":
    unittest.main()
