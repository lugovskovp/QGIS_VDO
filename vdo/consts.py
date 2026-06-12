"""

"""

import struct

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
struct_WORD = struct.Struct(">H")
struct_WORD_TWICE = struct.Struct(">HH")
struct_UINT = struct.Struct(">L")

#
ZERO_DWORD = b'\x00\x00\x00\x00'

#
LOOKUP_CHARS = {'000': 'a',
                '001': 'e',
                '0100': 's',
                '0101': 't',
                '0110': 'r',
                '0111': '\x00',
                '10000': ' ',
                '10001': 'd',
                '10010': 'g',
                '10011': 'h',
                '10100': 'i',
                '10101': 'l',
                '10110': 'n',
                '10111': 'o'
                }
