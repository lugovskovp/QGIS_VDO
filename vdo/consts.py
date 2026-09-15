"""
Константы проекта
"""

import struct
from qgis.PyQt.QtCore import QMetaType

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

# Имена слоёв в интерфейсе
NAME_LAYER_GLOBAL_BOUNDS = "Carindb bounds"
NAME_LAYER_ALMANACS = 'Almanac'
NAME_LAYER_POI = 'POIs'
NAME_LAYER_SHAPES = 'Shapes'
NAME_LAYER_LINES = 'Lines'

DEFAULT_SCALE = 4

# coordinate system
CRS_NAME = "WGS 84 / Custom Pacific Split -80"
CRS_PROJECTION_STRING = "PROJ4:+proj=longlat +lon_0=100 +datum=WGS84 +no_defs"

#
MOST_SIGNIFICANT_BIT = 0x80000000           # hi bit =1 -> minus val.

#
LAYERS_PROPERTY = [
    {
        'name': NAME_LAYER_ALMANACS,
        'geometry': 'Polygon',
        'atributes': [('name', QMetaType.Type.QString), ('variant', QMetaType.Type.QString)],
        'styles': [
            {
                'name': 'map',
                'style': {
                    'color': '255, 229, 180, 100',
                    'outline_color': '255,229,0,255',
                    'outline_width': '0.4',
                    'style': 'solid',
                    'outline_style': 'dot'
                }
            },
            {
                'name': 'layout',
                'style': {
                    'color': '255, 229, 180, 10',  #
                    'outline_color': '255, 129, 80, 255',  #
                    'outline_width': '0.6',
                    'style': 'solid',
                    'outline_style': 'dash'
                }
            }
        ]
    },
    {
        'name': NAME_LAYER_GLOBAL_BOUNDS,
        'geometry': 'Polygon',
        'atributes': [('name', QMetaType.Type.QString)],
        'place': -1,
        'styles': [
            {
                'name': 'bounds',
                'style': {
                    'color': '120,220,120,80',     # green '100,150,255,100', # Полупрозрачная синяя заливка
                    'outline_color': '0,50,200,255',    # Яркая синяя граница
                    'outline_width': '0.4',
                    'style': 'solid',
                    'outline_style': 'dot'
                }
            },
        ]
    },
]
