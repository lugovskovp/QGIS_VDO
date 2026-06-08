import binascii
# flake8: noqa: w291
from bitarray import bitarray   # https://pypi.org/project/bitarray/
# https://github.com/ilanschnell/bitarray/blob/master/doc/buffer.rst
from bitarray.util import ba2int, ba2hex

# import heapq
from vdo.constants import weights_chars, weights_adas, weights_digits, weights_punctuation1, weights_punctuation2, weights_system
from vdo.constants import build_canonical_huffman_lookup, build_original_huffman_lookup, print_lookup
from vdo.constants import huffman_bytes_weights_table

#  flake8: noqa: F401

def decode_hex_to_string(hex_string, lookup_table):
    # Очищаем и преобразуем в биты
    clean_hex = hex_string.replace(" ", "").replace("0x", "")
    
    # Пропускаем стартовые нулевые байты выравнивания, если они есть
    while clean_hex.startswith("0000"):
        clean_hex = clean_hex[4:]
        
    binary_data = binascii.unhexlify(clean_hex)
    bit_string = "".join(f"{byte:08b}" for byte in binary_data)
    
    decoded_chars = []
    current_bits = ""
    
    # Побитовый разбор
    # Первые 11 бит складываются в код, возвращающий байт 0x4B \(\rightarrow \) K
    # '1011100': 0x4b=75 ('K')
    # '11101101101': 0x6b=107 ('k') '100010': 0x33=51 ('3') '11110100011': 0xa3=163
    # '0000011000110000001000101011000001100011010011001100011100101001100011110110001000101100010001011010100010111001000101111010001100000000'
    for bit in bit_string:
        current_bits += bit
        if current_bits in lookup_table:
            byte_val = lookup_table[current_bits]
            
            # Если байт попадает в печатный ASCII диапазон
            if 32 <= byte_val <= 126:
                decoded_chars.append(chr(byte_val))
            else:
                decoded_chars.append(f"[0x{byte_val:02X}]")
                
            current_bits = ""
            
    return "".join(decoded_chars)


# распаковка хвоста от ру34: 
# bla_bl = BLADDR(vdo.read(0xE2A2A00, 4), vdo)    # @ 07151504 1d 0105 [1D:MAP__10k400]
# ..NEXT BLOCK

"""
обрезать лидирующие 0
строку побитово сдвигать - 8 раз 15 ???

варианты - каноническое дерево хафмана
1. для полной таблицы весов
2. для таблицы, где только буквы
3. буквы + цифры
4. буквы + цифры + символы

= binaskii -> bitarray
"""


def prepare_bytes(hex_string) -> bytes:
    # Очищаем и преобразуем в байты "00 00 06 30 22 b0 63 4c
    clean_hex = hex_string.replace(" ", "").replace("0x", "")
    # Пропускаем стартовые нулевые байты выравнивания, если они есть
    print(clean_hex)
    while clean_hex.startswith("000000"):  # not 0000 - еще битами крутить
        clean_hex = clean_hex[4:]
    print(clean_hex)
    
    binary_data = binascii.unhexlify(clean_hex)
    return binary_data


def decode_to_string(bit_string, weights: dict) -> str:
    """ строит каноническое дерево из весов, и распаковывает строку битов """
    # huffman tree
    lookup_table = build_canonical_huffman_lookup(weights)

    # decode
    decoded_chars = []
    current_bits = ""
    
    # Побитовый разбор
    # Первые 11 бит складываются в код, возвращающий байт 0x4B \(\rightarrow \) K
    # '1011100': 0x4b=75 ('K')
    # '11101101101': 0x6b=107 ('k') '100010': 0x33=51 ('3') '11110100011': 0xa3=163
    # '0000011000110000001000101011000001100011010011001100011100101001100011110110001000101100010001011010100010111001000101111010001100000000'
    btstr = bit_string.to01()
    for bit in btstr:
        current_bits += bit
        if current_bits in lookup_table:
            byte_val = lookup_table[current_bits]
            
            # Если байт попадает в печатный ASCII диапазон
            if 32 <= byte_val <= 126:
                decoded_chars.append(chr(byte_val))
            else:
                decoded_chars.append(f"[0x{byte_val:02X}]")
                
            current_bits = ""
            
    return "".join(decoded_chars)

# ===========================================
# Тестируемая строка - 'kolym...?' 'laptev...?'
target_hex = "00 00 00 00 00 06 30 22 b0 63 4c c7 29 8f 62 2c 45 a8 b9 17 a3 00"   # @ 07151504 1d 0105 [1D:MAP__10k400] # noqa


weights_4_canonical_map = huffman_bytes_weights_table
map = weights_chars
map.update(weights_punctuation2)
map.update(weights_punctuation1)
map.update(weights_digits)

map = weights_chars
map.update(weights_digits)
map.update(weights_punctuation1)

map = weights_chars
map.update(weights_adas)
map.update(weights_digits)
map.update(weights_punctuation1)
map.update(weights_punctuation2)

map = weights_chars
map.update(weights_digits)
map.update(weights_punctuation1)
map.update(weights_punctuation2)
map.update(weights_system)
map.update(weights_adas)

weights_4_canonical_map = map
#

binary_data = prepare_bytes(target_hex)

# 
bit_string = bitarray(buffer=binary_data, endian='big')

print("=== ТЕСТ РАСПАКОВКИ СТРОКИ ===")
for i in range(16):
    target_hex = ba2hex(bit_string)
    result_text = decode_to_string(bit_string, weights_4_canonical_map)
    print(f"{i:02}:  {target_hex[:11]}... -> {result_text}")
    res = bit_string << 1
    bit_string = res
    
pass






