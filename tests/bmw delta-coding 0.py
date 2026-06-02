import math

class TeleAtlasDecoder:
    def __init__(self, data: bytes, base_x: int, base_y: int):
        """
        Инициализация декодера.
        :param data: Байты сжатого битового потока (Bitstream).
        :param base_x: Абсолютная стартовая координата X0 из заголовка тайла.
        :param base_y: Абсолютная стартовая координата Y0 из заголовка тайла.
        """
        self.data = data
        self.bit_offset = 0
        self.total_bits = len(data) * 8
        
        # Начальная точка геометрии (текущее положение)
        self.current_x = base_x
        self.current_y = base_y

    def _read_bits(self, count: int) -> int:
        """Читает последовательность бит заданной длины из байтового массива."""
        if self.bit_offset + count > self.total_bits:
            raise EOFError("Попытка чтения за пределами битового потока")
            
        value = 0
        for _ in range(count):
            byte_idx = self.bit_offset // 8
            bit_idx = 7 - (self.bit_offset % 8)  # Read MSB first (Big-endian подход)
            
            bit = (self.data[byte_idx] >> bit_idx) & 1
            value = (value << 1) | bit
            self.bit_offset += 1
            
        return value

    def _decode_zigzag(self, n: int) -> int:
        """Восстанавливает исходное знаковое число из беззнакового кода ZigZag."""
        # Если число нечетное — оно было отрицательным, если четное — положительным
        return (n >> 1) ^ -(n & 1)

    def _read_delta(self) -> int:
        """
        Декодирует одну дельту на основе префиксных флагов:
        '0'   -> 4 бита значения
        '10'  -> 8 бит значения
        '110' -> 12 бит значения
        '111' -> 16 бит значения
        """
        # Шаг 1: Читаем первый бит префикса
        bit1 = self._read_bits(1)
        if bit1 == 0:
            # Префикс '0' -> Микро-смещение (4 бита)
            bits_to_read = 4
        else:
            # Префикс начинается с '1', проверяем второй бит
            bit2 = self._read_bits(1)
            if bit2 == 0:
                # Префикс '10' -> Малое смещение (8 бит)
                bits_to_read = 8
            else:
                # Префикс начинается с '11', проверяем третий бит
                bit3 = self._read_bits(1)
                if bit3 == 0:
                    # Префикс '110' -> Среднее смещение (12 бит)
                    bits_to_read = 12
                else:
                    # Префикс '111' -> Макси-смещение / Прыжок (16 бит)
                    bits_to_read = 16

        # Шаг 2: Считываем само закодированное значение
        encoded_val = self._read_bits(bits_to_read)
        
        # Шаг 3: Декодируем из ZigZag обратно в знаковое число
        return self._decode_zigzag(encoded_val)

    def decode_polygon(self, count_vertices: int) -> list:
        """
        Декодирует цепочку вершин полигона.
        :param count_vertices: Количество следующих точек (пар X, Y) для чтения.
        :return: Список абсолютных координат [(x0, y0), (x1, y1), ...]
        """
        # Первая точка всегда абсолютная (из заголовка тайла)
        vertices = [(self.current_x, self.current_y)]
        
        for _ in range(count_vertices):
            # Последовательно извлекаем дельту для X и для Y
            delta_x = self._read_delta()
            delta_y = self._read_delta()
            
            # Прибавляем смещения к текущему положению (аккумулятор координат)
            self.current_x += delta_x
            self.current_y += delta_y
            
            vertices.append((self.current_x, self.current_y))
            
        return vertices

# ==========================================
# ПРИМЕР РАБОТЫ ДЕКОДЕРА
# ==========================================
if __name__ == "__main__":
    # Симулируем бинарный поток, который мы разобрали в прошлом шаге:
    # Для X: дельта -1 -> ZigZag = 1 -> префикс '0' + '0001' -> биты '00001'
    # Для Y: дельта  3 -> ZigZag = 6 -> префикс '0' + '0110' -> биты '00110'
    # Объединяем X и Y дельты первой точки: '0000100110' -> дополняем нулями до байта -> 00001001 10000000
    # В шестнадцатеричном виде это: 0x09, 0x80
    
    compressed_bitstream = bytes([0x09, 0x80]) 
    
    # Стартовые абсолютные координаты тайла (например, центр города в локальной сетке)
    TILE_BASE_X = 10000
    TILE_BASE_Y = 25000
    
    # Инициализируем низкоуровневый декодер
    decoder = TeleAtlasDecoder(compressed_bitstream, TILE_BASE_X, TILE_BASE_Y)
    
    # Декодируем 1 следующую вершину
    polyline = decoder.decode_polygon(count_vertices=1)
    
    print("--- Результат декодирования ---")
    print(f"Стартовая точка P0: {polyline[0]}")
    print(f"Декодированная точка P1: {polyline[1]}")
    print(f"Ожидалось смещение (-1, +3): {polyline[1][0] - polyline[0][0] == -1 and polyline[1][1] - polyline[0][1] == 3}")
