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
NAME_LAYER_SHAPES = 'Contours'
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
                    'color': '120,220,120,80',     # green
                    'outline_color': '0,50,200,255',    # Яркая синяя граница
                    'outline_width': '0.4',
                    'style': 'solid',
                    'outline_style': 'dot'
                }
            },
        ]
    },
    {
        'name': NAME_LAYER_SHAPES,
        'geometry': 'Polygon',
        'atributes': [('name', QMetaType.Type.QString),
                      ('variant', QMetaType.Type.QString),
                      ('id', QMetaType.Type.QString),
                      ('block', QMetaType.Type.QString),
                      ('lat', QMetaType.Type.QString),
                      ('lon', QMetaType.Type.QString),
                      #('cat', QMetaType.Type.QString)],     # digit cat.id
                      ],
        'styles': [
            {
                'name': 'SPORTS_COMPLEX',
                'style': {
                    'color': '35, 255, 53, 200',
                    'outline_color': '35,255,35,255',
                    'outline_width': '0.4',
                    'style': 'cross',
                    'outline_style': 'solid'
                }
            },
            {
                'name': 'MILITARY_AREA',
                'style': {
                    'color': '255, 35, 53, 200',
                    'outline_color': '255,35,35,255',
                    'outline_width': '0.4',
                    'style': 'cross',
                    'outline_style': 'solid'
                }
            },
            {
                'name': 'UNIVERSITY_CAMPUS',
                'style': {
                    'color': '53, 35, 255, 200',
                    'outline_color': '53,35,255,255',
                    'outline_width': '0.4',
                    'style': 'cross',
                    'outline_style': 'solid'
                }
            },
            {
                'name': 'HOSPITAL_GROUND',
                'style': {
                    'color': '229, 110, 120, 200',
                    'outline_color': '255,190,190,255',
                    'outline_width': '0.4',
                    'style': 'solid',
                    'outline_style': 'solid'
                }
            },
            {
                'name': 'CEMETERY',
                'style': {
                    'color': '110, 229, 120, 100',
                    'outline_color': '0,50,0,255',      # Яркая зелёная граница
                    'outline_width': '0.4',
                    'style': 'cross',
                    'outline_style': 'solid'
                }
            },
            {
                'name': 'GOLF_COURSE',
                'style': {
                    'color': '110, 229, 120, 100',
                    'outline_color': '0,50,0,255',      # Яркая зелёная граница
                    'outline_width': '0.4',
                    'style': 'b_diagonal',
                    'outline_style': 'solid'
                }
            },
            {
                'name': 'AMUSEMENT_PARK',
                'style': {
                    'color': '110, 229, 120, 100',
                    'outline_color': '0,50,0,255',      # Яркая зелёная граница
                    'outline_width': '0.4',
                    'style': 'solid',
                    'outline_style': 'solid'
                }
            },
            {
                'name': 'ISLAND',
                'style': {
                    'color': '255, 229, 180, 200',
                    'outline_color': '255,229,0,255',
                    'outline_width': '0.4',
                    'style': 'solid',
                    'outline_style': 'solid'
                }
            },
            {
                'name': 'AIRPORT_GROUND',
                'style': {
                    'color': '190,190,190,100',         # Полупрозрачная темно серая заливка
                    'outline_color': '150,150,150,255',      # серая граница
                    'outline_width': '0.1',
                    'style': 'solid',
                    'outline_style': 'solid'
                }
            },
            {
                'name': 'INDUSTRIAL',
                'style': {
                    'color': '90,90,90,100',         # Полупрозрачная темно серая заливка
                    'outline_color': '50,50,50,255',      # серая граница
                    'outline_width': '0.1',
                    'style': 'solid',
                    'outline_style': 'solid'
                }
            },
            {
                'name': 'CITY',
                'style': {
                    'color': '150,150,150,100',         # Полупрозрачная серая заливка
                    'outline_color': '200,200,200,255',      # светлая серая граница
                    'outline_width': '0.1',
                    'style': 'solid',
                    'outline_style': 'solid'
                }
            },
            {
                'name': 'NATIONAL_PARK',
                'style': {
                    'color': '35,200,35,100',         # Полупрозрачная зелёная заливка
                    'outline_color': '0,50,0,255',      # Яркая зелёная граница
                    'outline_width': '0.1',
                    'style': 'solid',
                    'outline_style': 'solid'
                }
            },
            {
                'name': 'FOREST',
                'style': {
                    'color': '65,177,65,100',         # Полупрозрачная зелёная заливка
                    'outline_color': '0,50,0,255',      # Яркая зелёная граница
                    'outline_width': '0.1',
                    'style': 'solid',
                    'outline_style': 'solid'
                }
            },
            {
                'name': 'SEA_OCEAN',
                'style': {
                    'color': '100,150,255,100',         # Полупрозрачная синяя заливка
                    'outline_color': '0,50,200,255',    # Яркая синяя граница
                    'outline_width': '0.1',
                    'style': 'solid',
                    'outline_style': 'no'
                }
            },
            {
                'name': 'WATER',
                'style': {
                    'color': '100,150,255,100',         # Полупрозрачная синяя заливка
                    'outline_color': '0,50,200,255',    # Яркая синяя граница
                    'outline_width': '0.1',
                    'style': 'solid',
                    'outline_style': 'solid'
                }
            },
        ]
    },
]

"""
EMPTY = 0x00              # Пустая область / базовый фон суши
*WATER = 0x01              # Внутренние воды (озера, водохранилища, заливы)
*SEA_OCEAN = 0x02          # Моря и океаны
*FOREST = 0x03             # Леса, лесные массивы, густая растительность
*NATIONAL_PARK = 0x04      # Заповедники, национальные парки и заказники
*CITY = 0x05               # Полигон общей жилой застройки города / населенного пункта
*INDUSTRIAL = 0x06         # Промышленные зоны, заводы, склады, порты
*AIRPORT_GROUND = 0x07     # Территория аэропортов (взлетные полосы, терминалы)
*ISLAND = 0x08             # Остров (инвертированный полигон суши внутри воды)
*AMUSEMENT_PARK = 0x09     # Парки развлечений, аттракционы, зоопарки
*GOLF_COURSE = 0x0A        # Поля для гольфа
*CEMETERY = 0x0B           # Кладбища
*HOSPITAL_GROUND = 0x0C    # Территория больниц и медицинских комплексов
*UNIVERSITY_CAMPUS = 0x0D  # Студенческие городки, кампусы вузов
*MILITARY_AREA = 0x0E      # Закрытые военные объекты и полигоны
*SPORTS_COMPLEX = 0x0F     # Спортивные комплексы, открытые стадионы
"""
