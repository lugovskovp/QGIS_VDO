"""
Константы проекта
"""

import struct

# from consts_layers import (

# )

# constants values
BITS_IN_ASCII = 7
BITS_IN_BYTE = 8
BITS_IN_WORD = 16
BITS_IN_UINT = 32

USHORT_BYTES_CNT = 2
UINT_BYTES_CNT = 4
DOUBLE_BYTES_CNT = 8

# const structures
struct_BYTE = struct.Struct(">c")
struct_4BYTES = struct.Struct(">BBBB")
struct_WORD = struct.Struct(">H")
struct_WORD_TWICE = struct.Struct(">HH")
struct_UINT = struct.Struct(">L")
struct_2UINT = struct.Struct(">LL")     # 2x Unsigned Long (8 байт для COORD)

# Бинарный DWORD 0
ZERO_DWORD = b'\x00' * 4
EMPTY_BUFFER = b''

# Дерево хаффмана для сжатого текста
LOOKUP_CHAR_BYTES = {'000': b'a',
                     '001': b'e',
                     '0100': b's',
                     '0101': b't',
                     '0110': b'r',
                     '0111': b'\x00',
                     '10000': b' ',
                     '10001': b'd',
                     '10010': b'g',
                     '10011': b'h',
                     '10100': b'i',
                     '10101': b'l',
                     '10110': b'n',
                     '10111': b'o'
                     }


DEFAULT_SCALE = 4

# coordinate system
CRS_NAME = "WGS 84 / Custom Pacific Split -80"
CRS_PROJECTION_STRING = "PROJ4:+proj=longlat +lon_0=100 +datum=WGS84 +no_defs"

#
MOST_SIGNIFICANT_BIT = 0x80000000           # hi bit =1 -> minus val.
