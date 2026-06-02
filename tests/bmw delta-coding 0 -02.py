"""
bmw  //1Dp3  =2/4/0/11a/0/3  'tail_07154f 02.bin'  # noqa

unpack vertexes
"""

import math
from bitarray import bitarray
from bitarray.util import ba2int

from vdo.test_vdo import vdobmv as vdo
from vdo.datatypes import BYTESTRUCT

class PointsDecoder:
    def __init__(self, data: bytes, base_x: int, base_y: int, max_x_y: int):
        """
        Инициализация декодера.
        :param data: Байты сжатого битового потока (Bitstream).
        :param base_x: Абсолютная стартовая координата X0 из заголовка тайла.
        :param base_y: Абсолютная стартовая координата Y0 из заголовка тайла.
        """
        # bit_string = "".join(f"{byte:08b}" for byte in binary_data)
        # bit_iterator = iter(bit_string)
        # данные - в bitarray
        self.buffer = bitarray(buffer=data, endian='big').copy()

        self.bit_offset = 0
        self.total_bits = len(data) * 8
        # Начальная точка геометрии (текущее положение)
        self.current_x = base_x
        self.current_y = base_y
        self.max_x_y = max_x_y
        
        pass

    @property
    def av_head(self):
        """ debug: первые 40 битов """
        res = self._touch(40).to01()
        return res

    def _pop(self, qty_bits: int) -> bitarray:
        '''pop qty_bits from begin (left) buffer qty bites'''
        if qty_bits > len(self.buffer):
            raise EOFError("Попытка чтения за пределами битового потока")
        val = self.buffer[:qty_bits]
        del self.buffer[:qty_bits]
        return val
    
    def _touch(self, qty_bits: int, start: int = 0) -> bitarray:
        ''' Return qty bits from start Without deleting'''
        val = self.buffer[start:start + qty_bits].copy()
        return val

    def _read_bits(self, count: int) -> int:
        """Читает последовательность бит заданной длины из байтового массива."""
        if self.bit_offset + count > self.total_bits:
            raise EOFError("Попытка чтения за пределами битового потока")
        value = ba2int(self._pop(count))
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
        # --- Шаг 1:  РАСЧЕТ ПРЕФИКСА - СКОЛЬКО БАЙТ ЧИТАТЬ
        # - control prefix? если координата не меняется. Самый длинный 111? 
        BtR = {                 # bytes to read
                '0': 9,         # Префикс '0' -> Микро-смещение (4 бита)
                '10': 13,        # Префикс '10' -> Малое смещение (8 бит)
                '11': 16        # считать все 16 бит, как значение. []
                # '110': 13,      # Префикс '110' -> Среднее смещение (12 бит) :на первом шаге 14 валит в -?
                # '111': 16       # Префикс '111' -> Макси-смещение / Прыжок (16 бит)
                                # TODO а 1110/1111 - не загрузка ли следующих 16 бит в координату???
                                # TODO или "оставить значение"?
                }
        bits_to_read = 0            # обнуляем кво битов для чтения
        str_prefix = self._pop(1)             # берём самый первый
        while bits_to_read == 0:
            if str_prefix.to01() in BtR:
                bits_to_read = BtR[str_prefix.to01()]
                continue
            str_prefix += self._pop(1)

        # Шаг 2: Считываем само закодированное значение
        bi_toread = self._touch(bits_to_read).to01()
        bi_ttafter = self._touch(18, len(bi_toread)).to01()
        bi_z = str_prefix.to01() + " " + bi_toread + " " + bi_ttafter
        if str_prefix.to01() == '11':
            mode = 'load'
        else:
            mode = 'delta'
        encoded_val = self._read_bits(bits_to_read)
        
        # Шаг 3: Декодируем из ZigZag обратно в знаковое число
        if mode != 'load':
            zz = self._decode_zigzag(encoded_val)
        else:
            zz = encoded_val

        return zz, mode

    def decode_polygon(self, count_vertices: int) -> list:
        """
        Декодирует цепочку вершин полигона.
        :param count_vertices: Количество следующих точек (пар X, Y) для чтения.
        :return: Список абсолютных координат [(x0, y0), (x1, y1), ...]

        c0 00 39 5f 90 03
        07154d02
            c000 95f9  0089 c000  c000 c000
            0000 2a82  1145 2621  1131 2533  0f47 2508
        """
        # Первая точка всегда абсолютная (из заголовка тайла)
        vertices = [(self.current_x, self.current_y)]
        
        for _ in range(count_vertices):
            # Последовательно извлекаем дельту для X и для Y
            delta_x, mode = self._read_delta()
            if mode == 'load':
                self.current_x = delta_x
            else:
                # Прибавляем смещения к текущему положению (аккумулятор координат)
                self.current_x += delta_x
            delta_y, mode = self._read_delta()
            if mode == 'load':
                self.current_y = delta_y
            else:
                # Прибавляем смещения к текущему положению (аккумулятор координат)
                self.current_y += delta_y

            # if delta_x == delta_y == 0:
            #     # raise ValueError(f"ZERO delta_x: {delta_x} and delta_y: {delta_y}")
            #     print(f"ZERO delta_x: {delta_x} and delta_y: {delta_y}")
            
            # Прибавляем смещения к текущему положению (аккумулятор координат)
            # self.current_x += delta_x
            # self.current_y += delta_y

            # curr_point = f"{self.current_x:04x} {self.current_y:04x}"   # debug

            if self.current_x > self.max_x_y:
                raise ValueError(self.current_x, f"X: too big {self.current_x:04X} > {self.max_x_y:04X}")
            if self.current_y > self.max_x_y:
                raise ValueError(self.current_y, f"Y: too big {self.current_y:04X} > {self.max_x_y:04X}")
            if self.current_x < 0:
                raise ValueError(self.current_x, f"X: less zero: {self.current_x:04X} ")
            if self.current_y < 0:
                raise ValueError(self.current_y, f"Y: less zero: {self.current_y:04X} ")
            
            vertices.append((self.current_x, self.current_y))
            print(f"({self.current_x:04x}, {self.current_y:04x})  ={delta_x}={delta_y}=")
            
        return vertices

"""
07154f 02  BlockType.MAP__10k400: 0x1d

    Max PTR bites: 11
    cat 0034:0002 cnt:2     next ptr: 0040
    shp 0040:0004 cnt:4     next ptr: 00A4
    lin 0000:0000 cnt:0 
    poi 0000:0000 cnt:0 
    vrt 00A4:011A cnt:282   next ptr: 050C
    tst 050C:0003 cnt:3     next ptr: 0518
    strs from 0518 
    begin word = 0500:0900
    Map_hex: 42 6D 90 00 16 7A 50 00  45 6D 90 00 19 7A 50 00   00 01 00 0A  

    01 00 00 40  
    01 00 00 54  
    00 00 00 90  
    start_vrtx_num = 0
    0000 00A4 400d9206  387EEDF5 1AF37D90  0000 050C  - первый полигон 4 точки
    0518 00B4 400cd65c  3F579717 18395941  0000 050C    start_vrtx_num = 4
    0518 04E8 400cd65c  3F579717 18395941  0000 0510    start_vrtx_num = 273
    0518 04F4 400cd65c  3F579717 18395941  0000 0514    start_vrtx_num = 276
    0000 050C 00000000  00000000 00000000  0000 0518    start_vrtx_num = 282
    tail_07154f 02.bin

    more laptevykh
    vostochno sibirskoe more

    07152401
    0000 aacf  c000 aacf  c000 0e0b  0000 0c2f
    0000 15dc  c000 13f4  c000 0000  0000 0000

    07152501
    0000 aacf  c000 aacf  c000 0fe7  0000 0e0b

    07154d02
    c000 95f9  0089 c000  c000 c000
    0000 2a82  1145 2621  1131 2533  0f47 2508

    07155101
    0000 aacf  c000 aacf  c000 0000  0089 0000
    0000 001e  0000 06cb  2153 0000  0000 0000
"""
# ==========================================
# ПРИМЕР РАБОТЫ ДЕКОДЕРА
# ==========================================
if __name__ == "__main__":
    #
    ftail = '_tail_07154f 02.bin'
    # ftail = '_tail_071526 05.bin'
    with open(ftail, "rb") as f:
        compressed_bitstream = f.read()
    
    # Симулируем бинарный поток, который мы разобрали в прошлом шаге:
    # Для X: дельта -1 -> ZigZag = 1 -> префикс '0' + '0001' -> биты '00001'
    # Для Y: дельта  3 -> ZigZag = 6 -> префикс '0' + '0110' -> биты '00110'
    # Объединяем X и Y дельты первой точки: '0000100110' -> дополняем нулями до байта -> 00001001 10000000
    # В шестнадцатеричном виде это: 0x09, 0x80
    
    # compressed_bitstream = bytes([0x09, 0x80]) 

    # Стартовые абсолютные координаты тайла (например, центр города в локальной сетке)
    # - или 0, 0
    # - или первое значение в потоке 
    # - NO! beg A, B,  !!! rus34, 0x08a06b02 begAB=0e00 0900, но макс ХУ = 0хс000 
    # для одинаковых значений нет проблем с очередностью

    TILE_BASE_X = 0x500
    TILE_BASE_Y = 0x900

    import struct

    # а если первые 4 байта - незапакованная координата?
    TILE_BASE_X = struct.unpack(">H", compressed_bitstream[0:2])[0]
    TILE_BASE_Y = struct.unpack(">H", compressed_bitstream[2:4])[0]
    compressed_bitstream = compressed_bitstream[4:]

    MAX_XY_VAL = 0xC000
    # TILE_BASE_X = 0
    # TILE_BASE_Y = 0

    # Инициализируем низкоуровневый декодер
    print(f"({TILE_BASE_X:04x}, {TILE_BASE_Y:04x})")
    decoder = PointsDecoder(compressed_bitstream, TILE_BASE_X, TILE_BASE_Y, MAX_XY_VAL)

    #  decoder2 = PointsDecoder(compressed_bitstream, TILE_BASE_Y, TILE_BASE_X, MAX_XY_VAL)
    

    # Декодируем следующие вершины
    # 07154d02
    # c000 95f9  0089 c000  c000 c000
    # 0000 2a82  1145 2621  1131 2533  0f47 2508
    polyline = decoder.decode_polygon(count_vertices=4)
    print()
    
    
    # print("--- Результат декодирования ---")
    # print(f"Стартовая точка P0: {polyline[0]}")
    # print(f"Декодированная точка P1: {polyline[1]}")
    # print(f"Ожидалось смещение (-1, +3): {polyline[1][0] - polyline[0][0] == -1 and polyline[1][1] - polyline[0][1] == 3}")
    
    pass

'''
Стартовые абсолютные координаты тайла (например, центр города в локальной сетке)
    # - или 0, 0
    # - или первое значение в потоке
    # - or beg A, B ?
- 

from vdo_map_block_base

# noqa
00 - 00000000 ??? 0000 
10 - nex4x -> 
11 - next 4x -> xxxx 0000

0010101111011010000110110010111010010101001011001010100001011010010010100001000001000100010011000010110100010011001101011011100111001000001111111010111011111100100101001110101001001001111011100010101100011100111011110001100011110000011100011000010111111011
001010 1 111011010000110110010111010010101001011001010100001011010010010100001000001000100010011000010110100010011001101011011100111001000001111111010111011111100100101001110101001001001111011100010101100011100111011110001100011110000011100011000010111111011
00101011110110100 00110110010111010 01010100101100 10101000010110100100 10100001000001000100010011000010110100010011001101011011100111001000001111111010111011111100100101001110101001001001111011100010101100011100111011110001100011110000011100011000010111111011

Начало вертексов 0xe296c00 0x3e3 vertexes
001000011010011010110110011000011000100000000101000010010001101000111100011010001111000001100111010101101001001100100100
Начало вертексов 0xe295400 0x314 vertexes
001101010111101110010000101011000010010011100100010110010001001100010011110000101111100100010000110101011100001010010100
Начало вертексов 0xe29fa00 0x125 vertexes
001001000001110110110111010111111011010110100100000100011001101000111000001010011000000100010001010011110011001100000110
Начало вертексов 0xe293200 0xafe vertexes
000000000000000000100101000101010010000111010000110110011001011010010101100001110110110010010110010110001110010011010000
Начало вертексов 0xe292e00 0xf6 vertexes
000000000000000001010111111001110000100001010000101001000001001010001011010011011111110000001001011000101100010000110010
Начало вертексов 0xe2a3200 0x196 vertexes
010011101101111010101001100001110010111100000101010111001001010100101111111000001110100110110100000110110001001010000010

00000000000000000 01001010001010100 1000011101 00001101100110010 11010010101 1000011101 10110010010110010110001110010011010000
000000000 000000000 100101000101010010000111010000110110011001011010010101100001110110110010010110010110001110010011010000
000000000000000000100101000101010010000111010000110110011001011010010101100001110110110010010110010110001110010011010000

00000000000000000 10101111110011100001000010100001010010 00001001010001011010011011111110000001001011000101100010000110010
000000000000000001010111111001110000100001010000101001000001001010001011010011011111110000001001011000101100010000110010
        
                WORD x <--- 
                WORD y <---
                '''