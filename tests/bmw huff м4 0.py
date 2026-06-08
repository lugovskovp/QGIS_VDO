"""
bmw  //1Dp3  =2/4/0/11a/0/3  'tail_07154f 02.bin'  # noqa

unpack vertexes

c:\DIY\VDO\db_src\bmw34-2010\DB\DB_0
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
0000 00A4 400d9206  387EEDF5 1AF37D90  0000 050C
start_vrtx_num = 4
0518 00B4 400cd65c  3F579717 18395941  0000 050C
start_vrtx_num = 273
0518 04E8 400cd65c  3F579717 18395941  0000 0510
start_vrtx_num = 276
0518 04F4 400cd65c  3F579717 18395941  0000 0514
start_vrtx_num = 282
0000 050C 00000000  00000000 00000000  0000 0518
tail_07154f 02.bin

more laptevykh
vostochno sibirskoe more
kolymskiy zaliv
vostochno sibirskoe more
vostochno sibirskoe more
beringovo more

0518 1500 0518 1500 0518 1500 

00 c10c 10 c10c 10 c10c 1f  

---
07153803 =1dp4 =3/8/0/157/0/5
beringovo more
07154103 =1dp
====================================
07152605 -1dp6 =2/6/0/276/0/6
    c:\DIY\VDO\db_src\bmw34-2010\DB\DB_0
    071526 05  BlockType.MAP__10k400: 0x1d

    Max PTR bites: 12
    cat 0034:0002 cnt:2     next ptr: 0040
    shp 0040:0006 cnt:6     next ptr: 00CC
    lin 0000:0000 cnt:0 
    poi 0000:0000 cnt:0 
    vrt 00CC:0276 cnt:630   next ptr: 0AA4
    tst 0AA4:0006 cnt:6     next ptr: 0ABC
    strs from 0ABC
    begin word = 0500:0900
    Map_hex: 39 6D 90 00 16 7A 50 00  3C 6D 90 00 19 7A 50 00   00 01 00 0A  

    08 00 00 40  
    01 00 00 90  
    00 00 00 B8  
    start_vrtx_num = 0
    0ABC 00CC 4000fe16  38E36D50 185E9801  0000 0AA4
    start_vrtx_num = 14
    0ACD 0104 400115b9  3B5F7665 18D56E99  0000 0AA8
    start_vrtx_num = 155
    0ADB 0338 400249cb  3814139D 18EBAC33  0000 0AAC
    start_vrtx_num = 202
    0ADB 03F4 400249cb  3814139D 18EBAC33  0000 0AB0
    start_vrtx_num = 210
    0AE5 0414 261c15b1  3B69E4D5 17C12652  0000 0AB4
    start_vrtx_num = 254
    0AF3 04C4 400cd65c  3F579717 18395941  0000 0AB8
    start_vrtx_num = 630
    0000 0AA4 00000000  00000000 00000000  0000 0ABC
    tail_071526 05.bin
    SHAPE ISLAND[4] :0x40
    SHAPE WATER[2] :0x90
"""
import binascii
from vdo.test_vdo import vdobmv as vdo
from vdo.datatypes import BYTESTRUCT


def decode_psf_adaptive_context(binary_data, lookup_table, total_points=516):
    """
    Адаптивный ГИС-декодер.
    Обрабатывает связку 0x0B -> 0x19 как команду переключения контекста разрядности.
    """
    # 1. Разворачиваем HEX Зоны 1 в битовую ленту
    # binary_data = binascii.unhexlify(zone1_hex_data.replace(" ", "").replace("\n", ""))
    bit_string = "".join(f"{byte:08b}" for byte in binary_data)
    bit_iterator = iter(bit_string)

    
    # unpacked_coordinates = []
    unpacked_bytes = []
    current_bits = ""
    
    # bitarray('0010101111011010000110110010111010010101')
    #from vdo.constants import canonical_lookup
    #lookup_table = canonical_lookup

    # Системные константы овкодов из заголовка карты
    OPCODE_CONTEXT_SWITCH = 0x0B
    
    bitt_t = bit_string

    try:
        for bit in bit_iterator:
            current_bits += bit
            bitt_t = bitt_t[1:]
            
            if current_bits in lookup_table:
                token = lookup_table[current_bits]
                current_bits = ""
                
                if token == OPCODE_CONTEXT_SWITCH and False:
                    # ШАГ 1: Поймали триггер 0x0B. Нам нужно декодировать СЛЕДУЮЩИЙ токен как селектор
                    selector_bits = ""
                    selector_token = None
                    
                    # Ищем следующий валидный токен в битовой ленте
                    for sub_bit in bit_iterator:
                        selector_bits += sub_bit
                        if selector_bits in lookup_table:
                            selector_token = lookup_table[selector_bits]
                            if selector_token in [0x19, 0x17]:
                                print(len(unpacked_bytes))
                                """
                                2064 байт (516 точек × 4 байта)
                                4 независимых полигона воды (126, 43, 267 и 80 точек)
                                 (126*4=504, 43*4=172+504=676, 267 и 80 точек)
                                """
                                pass
                            break
                            
                    print(f"[ГИС-Контекст] Сработал опкод 0x0B. Считан селектор разрядности: 0x{selector_token:02X}")
                    
                    # '101': 25 - 0x19, '110': 23 - 0x17,
                    # ШАГ 2: Анализируем селектор разрядности (например, ваш токен 0x19)
                    if selector_token == 0x19:
                        # Селектор 0x19 активирует режим чтения абсолютных 16-битных координат (Raw UInt16)
                        # Извлекаем из итератора 32 бита напрямую (16 бит на X + 16 бит на Y)
                        x_high_bits = "".join(next(bit_iterator) for _ in range(8))
                        x_low_bits  = "".join(next(bit_iterator) for _ in range(8))
                        y_high_bits = "".join(next(bit_iterator) for _ in range(8))
                        y_low_bits  = "".join(next(bit_iterator) for _ in range(8))
                        
                        # Собираем абсолютные двухбайтовые координаты
                        # x_abs = (int(x_high_bits, 2) << 8) | int(x_low_bits, 2)
                        # y_abs = (int(y_high_bits, 2) << 8) | int(y_low_bits, 2)
                        
                        # unpacked_coordinates.append((x_abs, y_abs))

                        unpacked_bytes.append(int(x_high_bits, 2))
                        unpacked_bytes.append(int(x_low_bits, 2))
                        unpacked_bytes.append(int(y_high_bits, 2))
                        unpacked_bytes.append(int(y_low_bits, 2))
                    
                        
                    elif selector_token == 0x17: # Пример другого гипотетического селектора
                        # Режим Raw 8-bit дельт (читаем 16 бит: 8 бит на dX + 8 бит на dY)
                        dx_bits = "".join(next(bit_iterator) for _ in range(8))
                        dy_bits = "".join(next(bit_iterator) for _ in range(8))
                        # ... логика накопления дельт координат ...
                        # Извлекаем WORD (16 бит -> 2 байта последовательно)
                        w_bits_high = "".join(next(bit_iterator) for _ in range(8))
                        w_bits_low = "".join(next(bit_iterator) for _ in range(8))
                        
                        unpacked_bytes.append(int(w_bits_high, 2))
                        unpacked_bytes.append(int(w_bits_low, 2))
                        
                else:
                    # Обычный токен (если поток находится в стандартном режиме Хаффмана)
                    # (Например, мелкая дельта, уложенная напрямую в дерево весов)
                    unpacked_bytes.append(token)
                    pass
                
                # Завершаем чтение, как только собрали все 516 *4 = 2064 географических точек
                if len(unpacked_bytes) >= total_points * 4:
                    break
                    
    except StopIteration:
        # Поток бит успешно считан до конца
        pass
    
    # ''110011001000001010011101101010011000001111110110000011000000010010001110100000001000010101001001000101001010100000011000000111010001111000000001101111110000000000000011010010110110001111101111011110011110001100010111100000000000000001001011000000000001100011000110000101010110111000010110111000111010000100000110000000100000100001100110110010000110000010000010110010001101101000110001010011000000001100000100001100000100001100000100001100000100001100000100001100000111111011010111010001011011111110001110011101101011110000010010100111100010101000110010011110101110111001100001111011011011101100010111000010110000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000110100011000100010101100000000000101000011010100001101010001000101000101010100011000000000000000000000000000000000000000'11001000001010011101101010011000001111110110000011000000010010001110100000001000010101001001000101001010100000011000000111010001111000000001101111110000000000000011010010110110001111101111011110011110001100010111100000000000000001001011000000000001100011000110000101010110111000010110111000111010000100000110000000100000100001100110110010000110000010000010110010001101101000110001010011000000001100000100001100000100001100000100001100000100001100000100001100000111111011010111010001011011111110001110011101101011110000010010100111100010101000110010011110101110111001100001111011011011101100010111000010110000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000110100011000100010101100000000000101000011010100001101010001000101000101010100011000000000000000000000000000000000000000'
    btt = bitt_t.tobytes()
    lesser = ''
    try:
        for bit in bit_iterator:
            lesser += bit
    except StopIteration:
        # Поток бит успешно считан до конца
        
        pass
    
    # bb = bitarray.bitarray(lesser)
    # bc = bb.tobytes()
    #st = " ".join(f"{k:02x}" for k in bc)
    
    # 01 '53 d1 fa f4 3a 5d 17 e8 56 9f 68 24 cd 69 a4 fb 07 be 91 53 d7 73 0f 6d d8 b8 60 
    # 08 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 06 30 22 b0 63 4c c7 29 8f 62 2c 45 a8 b9 17 a3 00 00 00 00 00 00 00'
    # 02 'b0 8e 07 47 59 32 02 90 45 55 0a 3a 42 99 7b 18 63 b5 6e 1f 8a 52 d2 78 c0 50 2e 
    # 72 cb 59 b7 1a 83 00 03 c0 00 f0 00 00 0d e1 c7 83 04 30 43 04 30 43 04 30 7f 22 c9 
    # eb a7 e6 1f a1 5a 7d 9e 5f 5f 10 87 8b eb eb 9d da 1e b9 8f c8 7f 6d d8 c2 a3 e0 a7 
    # ed f9 f5 cd c2 c0 40 00 00 00 00 00 00 00 00 00 00 00 00 00 3b c2 2b 07 7f 1e 20 6e 
    # 5b a6 ed bc 00 00 00 00 00'
    print("final: ", len(unpacked_bytes), len(bit_string)/8)
    return unpacked_bytes

# 
# --- ПОЛУЧЕНИЕ ТАБЛИЦЫ ВЕСОВ и построение Huffman tree lookup
weights = vdo.get_huffman_weights()
lookup = vdo.generate_canonical_lookup(weights)

# === Прочитать содержимое нераспакованного хвоста
ftail = '_tail_07154f 02.bin'
# ftail = '_tail_071526 05.bin'
with open(ftail, "rb") as f:
    tail = f.read()

vrtx_cnt = 282  # vrt 00A4:011A cnt:282  

# --- Подсчёт частотности символов
frequency = {}

for i in range(256):
    freq_i = 0
    for j in tail:
        if i == j:
            freq_i += 1
    frequency[i] = freq_i

# --- Собрать строку для вывода частот на печать
def print_values(frequency: dict) -> None:
    res_str = ""
    hex_cr = 0
    for(key, val) in frequency.items():
        res_str += f"{key:02X}: {val}\t"
        hex_cr += 1
        if hex_cr == 0x10:
            # every 16
            res_str += f"\n"
            hex_cr = 0

    print(f"{res_str}")

print_values(frequency)
"""
_tail_071526 05.bin
00: 45  01: 11  02: 12  03: 12  04: 9   05: 9   06: 2   07: 12  08: 14  09: 6   0A: 15  0B: 12  0C: 10  0D: 6   0E: 11  0F: 11
10: 13  11: 13  12: 5   13: 5   14: 12  15: 9   16: 8   17: 4   18: 11  19: 5   1A: 13  1B: 3   1C: 10  1D: 13  1E: 9   1F: 5
20: 12  21: 13  22: 8   23: 11  24: 9   25: 8   26: 8   27: 10  28: 9   29: 8   2A: 12  2B: 8   2C: 8   2D: 9   2E: 12  2F: 5
30: 20  31: 13  32: 8   33: 4   34: 5   35: 7   36: 12  37: 10  38: 15  39: 8   3A: 9   3B: 5   3C: 9   3D: 6   3E: 8   3F: 3
40: 7   41: 12  42: 7   43: 10  44: 11  45: 11  46: 11  47: 11  48: 10  49: 9   4A: 7   4B: 7   4C: 4   4D: 4   4E: 12  4F: 11
50: 6   51: 4   52: 6   53: 13  54: 7   55: 6   56: 8   57: 6   58: 5   59: 8   5A: 8   5B: 4   5C: 5   5D: 5   5E: 8   5F: 5
60: 5   61: 13  62: 9   63: 3   64: 10  65: 10  66: 11  67: 7   68: 4   69: 5   6A: 7   6B: 10  6C: 0   6D: 8   6E: 8   6F: 5
70: 11  71: 7   72: 5   73: 3   74: 8   75: 4   76: 11  77: 9   78: 14  79: 8   7A: 8   7B: 3   7C: 7   7D: 3   7E: 4   7F: 3
80: 20  81: 7   82: 11  83: 6   84: 13  85: 10  86: 7   87: 11  88: 8   89: 6   8A: 5   8B: 8   8C: 4   8D: 6   8E: 8   8F: 7
90: 16  91: 13  92: 8   93: 7   94: 6   95: 7   96: 5   97: 5   98: 10  99: 6   9A: 9   9B: 7   9C: 7   9D: 4   9E: 4   9F: 7
A0: 8   A1: 5   A2: 8   A3: 10  A4: 5   A5: 7   A6: 7   A7: 8   A8: 10  A9: 2   AA: 8   AB: 10  AC: 6   AD: 4   AE: 8   AF: 5
B0: 12  B1: 9   B2: 2   B3: 8   B4: 5   B5: 6   B6: 7   B7: 2   B8: 5   B9: 9   BA: 6   BB: 6   BC: 6   BD: 2   BE: 5   BF: 4
C0: 13  C1: 14  C2: 11  C3: 7   C4: 10  C5: 15  C6: 7   C7: 7   C8: 9   C9: 8   CA: 10  CB: 10  CC: 2   CD: 9   CE: 6   CF: 3
D0: 8   D1: 2   D2: 5   D3: 5   D4: 6   D5: 6   D6: 4   D7: 2   D8: 5   D9: 9   DA: 3   DB: 3   DC: 10  DD: 6   DE: 4   DF: 0
E0: 9   E1: 5   E2: 9   E3: 11  E4: 14  E5: 6   E6: 5   E7: 9   E8: 2   E9: 7   EA: 4   EB: 4   EC: 5   ED: 2   EE: 3   EF: 1
F0: 10  F1: 9   F2: 8   F3: 4   F4: 6   F5: 4   F6: 3   F7: 4   F8: 3   F9: 2   FA: 4   FB: 4   FC: 6   FD: 4   FE: 5   FF: 1

'_tail_07154f 02.bin'
00: 35  01: 7   02: 6   03: 9   04: 8   05: 12  06: 6   07: 5   08: 5   09: 3   0A: 3   0B: 1   0C: 5   0D: 3   0E: 5   0F: 4
10: 11  11: 4   12: 6   13: 1   14: 3   15: 2   16: 0   17: 1   18: 6   19: 2   1A: 1   1B: 5   1C: 0   1D: 2   1E: 1   1F: 4
20: 9   21: 8   22: 6   23: 10  24: 4   25: 3   26: 5   27: 3   28: 4   29: 2   2A: 2   2B: 2   2C: 1   2D: 2   2E: 5   2F: 2
30: 1   31: 6   32: 0   33: 6   34: 4   35: 4   36: 4   37: 3   38: 3   39: 5   3A: 2   3B: 5   3C: 6   3D: 1   3E: 2   3F: 1
40: 10  41: 7   42: 7   43: 2   44: 2   45: 8   46: 3   47: 7   48: 9   49: 4   4A: 4   4B: 3   4C: 5   4D: 4   4E: 5   4F: 5
50: 3   51: 2   52: 2   53: 2   54: 5   55: 1   56: 1   57: 4   58: 1   59: 6   5A: 4   5B: 4   5C: 4   5D: 2   5E: 3   5F: 2
60: 3   61: 2   62: 4   63: 5   64: 4   65: 4   66: 3   67: 1   68: 2   69: 2   6A: 3   6B: 3   6C: 1   6D: 1   6E: 3   6F: 3
70: 3   71: 4   72: 4   73: 2   74: 2   75: 0   76: 3   77: 3   78: 5   79: 1   7A: 1   7B: 3   7C: 2   7D: 2   7E: 4   7F: 3
80: 8   81: 3   82: 7   83: 3   84: 4   85: 4   86: 6   87: 2   88: 3   89: 3   8A: 2   8B: 0   8C: 5   8D: 1   8E: 5   8F: 2
90: 7   91: 1   92: 1   93: 3   94: 2   95: 3   96: 2   97: 2   98: 4   99: 0   9A: 1   9B: 3   9C: 3   9D: 3   9E: 5   9F: 5
A0: 9   A1: 1   A2: 2   A3: 2   A4: 3   A5: 6   A6: 4   A7: 3   A8: 5   A9: 2   AA: 2   AB: 2   AC: 6   AD: 4   AE: 2   AF: 5
B0: 1   B1: 7   B2: 3   B3: 3   B4: 0   B5: 3   B6: 2   B7: 2   B8: 3   B9: 2   BA: 2   BB: 1   BC: 2   BD: 4   BE: 2   BF: 0
C0: 11  C1: 6   C2: 2   C3: 2   C4: 5   C5: 5   C6: 5   C7: 1   C8: 2   C9: 0   CA: 2   CB: 8   CC: 0   CD: 0   CE: 0   CF: 1
D0: 2   D1: 4   D2: 5   D3: 0   D4: 4   D5: 0   D6: 1   D7: 5   D8: 5   D9: 4   DA: 1   DB: 0   DC: 5   DD: 4   DE: 2   DF: 2
E0: 6   E1: 2   E2: 2   E3: 4   E4: 2   E5: 2   E6: 4   E7: 2   E8: 3   E9: 2   EA: 3   EB: 1   EC: 4   ED: 1   EE: 2   EF: 3
F0: 5   F1: 4   F2: 3   F3: 1   F4: 4   F5: 1   F6: 2   F7: 2   F8: 5   F9: 1   FA: 0   FB: 3   FC: 3   FD: 1   FE: 2   FF: 1
"""

# --- sort dict
sorted_freq = {k: v for k, v in sorted(frequency.items(), key=lambda item: item[1])}

# sorted_dict = {k: v for k, v in sorted(data.items(), key=lambda item: item[1])}
print_values(sorted_freq)
"""
_tail_071526 05.bin
6C: 0   DF: 0   EF: 1   FF: 1   06: 2   A9: 2   B2: 2   B7: 2   BD: 2   CC: 2   D1: 2   D7: 2   E8: 2   ED: 2   F9: 2   1B: 3
3F: 3   63: 3   73: 3   7B: 3   7D: 3   7F: 3   CF: 3   DA: 3   DB: 3   EE: 3   F6: 3   F8: 3   17: 4   33: 4   4C: 4   4D: 4
51: 4   5B: 4   68: 4   75: 4   7E: 4   8C: 4   9D: 4   9E: 4   AD: 4   BF: 4   D6: 4   DE: 4   EA: 4   EB: 4   F3: 4   F5: 4
F7: 4   FA: 4   FB: 4   FD: 4   12: 5   13: 5   19: 5   1F: 5   2F: 5   34: 5   3B: 5   58: 5   5C: 5   5D: 5   5F: 5   60: 5
69: 5   6F: 5   72: 5   8A: 5   96: 5   97: 5   A1: 5   A4: 5   AF: 5   B4: 5   B8: 5   BE: 5   D2: 5   D3: 5   D8: 5   E1: 5
E6: 5   EC: 5   FE: 5   09: 6   0D: 6   3D: 6   50: 6   52: 6   55: 6   57: 6   83: 6   89: 6   8D: 6   94: 6   99: 6   AC: 6
B5: 6   BA: 6   BB: 6   BC: 6   CE: 6   D4: 6   D5: 6   DD: 6   E5: 6   F4: 6   FC: 6   35: 7   40: 7   42: 7   4A: 7   4B: 7
54: 7   67: 7   6A: 7   71: 7   7C: 7   81: 7   86: 7   8F: 7   93: 7   95: 7   9B: 7   9C: 7   9F: 7   A5: 7   A6: 7   B6: 7
C3: 7   C6: 7   C7: 7   E9: 7   16: 8   22: 8   25: 8   26: 8   29: 8   2B: 8   2C: 8   32: 8   39: 8   3E: 8   56: 8   59: 8
5A: 8   5E: 8   6D: 8   6E: 8   74: 8   79: 8   7A: 8   88: 8   8B: 8   8E: 8   92: 8   A0: 8   A2: 8   A7: 8   AA: 8   AE: 8
B3: 8   C9: 8   D0: 8   F2: 8   04: 9   05: 9   15: 9   1E: 9   24: 9   28: 9   2D: 9   3A: 9   3C: 9   49: 9   62: 9   77: 9
9A: 9   B1: 9   B9: 9   C8: 9   CD: 9   D9: 9   E0: 9   E2: 9   E7: 9   F1: 9   0C: 10  1C: 10  27: 10  37: 10  43: 10  48: 10
64: 10  65: 10  6B: 10  85: 10  98: 10  A3: 10  A8: 10  AB: 10  C4: 10  CA: 10  CB: 10  DC: 10  F0: 10  01: 11  0E: 11  0F: 11
18: 11  23: 11  44: 11  45: 11  46: 11  47: 11  4F: 11  66: 11  70: 11  76: 11  82: 11  87: 11  C2: 11  E3: 11  02: 12  03: 12
07: 12  0B: 12  14: 12  20: 12  2A: 12  2E: 12  36: 12  41: 12  4E: 12  B0: 12  10: 13  11: 13  1A: 13  1D: 13  21: 13  31: 13
53: 13  61: 13  84: 13  91: 13  C0: 13  08: 14  78: 14  C1: 14  E4: 14  0A: 15  38: 15  C5: 15  90: 16  30: 20  80: 20  00: 45

'_tail_07154f 02.bin'
16: 0   1C: 0   32: 0   75: 0   8B: 0   99: 0   B4: 0   BF: 0   C9: 0   CC: 0   CD: 0   CE: 0   D3: 0   D5: 0   DB: 0   FA: 0
0B: 1   13: 1   17: 1   1A: 1   1E: 1   2C: 1   30: 1   3D: 1   3F: 1   55: 1   56: 1   58: 1   67: 1   6C: 1   6D: 1   79: 1
7A: 1   8D: 1   91: 1   92: 1   9A: 1   A1: 1   B0: 1   BB: 1   C7: 1   CF: 1   D6: 1   DA: 1   EB: 1   ED: 1   F3: 1   F5: 1
F9: 1   FD: 1   FF: 1   15: 2   19: 2   1D: 2   29: 2   2A: 2   2B: 2   2D: 2   2F: 2   3A: 2   3E: 2   43: 2   44: 2   51: 2
52: 2   53: 2   5D: 2   5F: 2   61: 2   68: 2   69: 2   73: 2   74: 2   7C: 2   7D: 2   87: 2   8A: 2   8F: 2   94: 2   96: 2
97: 2   A2: 2   A3: 2   A9: 2   AA: 2   AB: 2   AE: 2   B6: 2   B7: 2   B9: 2   BA: 2   BC: 2   BE: 2   C2: 2   C3: 2   C8: 2
CA: 2   D0: 2   DE: 2   DF: 2   E1: 2   E2: 2   E4: 2   E5: 2   E7: 2   E9: 2   EE: 2   F6: 2   F7: 2   FE: 2   09: 3   0A: 3
0D: 3   14: 3   25: 3   27: 3   37: 3   38: 3   46: 3   4B: 3   50: 3   5E: 3   60: 3   66: 3   6A: 3   6B: 3   6E: 3   6F: 3
70: 3   76: 3   77: 3   7B: 3   7F: 3   81: 3   83: 3   88: 3   89: 3   93: 3   95: 3   9B: 3   9C: 3   9D: 3   A4: 3   A7: 3
B2: 3   B3: 3   B5: 3   B8: 3   E8: 3   EA: 3   EF: 3   F2: 3   FB: 3   FC: 3   0F: 4   11: 4   1F: 4   24: 4   28: 4   34: 4
35: 4   36: 4   49: 4   4A: 4   4D: 4   57: 4   5A: 4   5B: 4   5C: 4   62: 4   64: 4   65: 4   71: 4   72: 4   7E: 4   84: 4
85: 4   98: 4   A6: 4   AD: 4   BD: 4   D1: 4   D4: 4   D9: 4   DD: 4   E3: 4   E6: 4   EC: 4   F1: 4   F4: 4   07: 5   08: 5
0C: 5   0E: 5   1B: 5   26: 5   2E: 5   39: 5   3B: 5   4C: 5   4E: 5   4F: 5   54: 5   63: 5   78: 5   8C: 5   8E: 5   9E: 5
9F: 5   A8: 5   AF: 5   C4: 5   C5: 5   C6: 5   D2: 5   D7: 5   D8: 5   DC: 5   F0: 5   F8: 5   02: 6   06: 6   12: 6   18: 6
22: 6   31: 6   33: 6   3C: 6   59: 6   86: 6   A5: 6   AC: 6   C1: 6   E0: 6   01: 7   41: 7   42: 7   47: 7   82: 7   90: 7
B1: 7   04: 8   21: 8   45: 8   80: 8   CB: 8   03: 9   20: 9   48: 9   A0: 9   23: 10  40: 10  10: 11  C0: 11  05: 12  00: 35
"""


tail_len = len(tail)
need_bytes = vrtx_cnt * 4

bs = BYTESTRUCT(tail[:0x30])

# Запуск адаптивной декомпрессии
restored_water_nodes = decode_psf_adaptive_context(tail, lookup, vrtx_cnt)

pass



