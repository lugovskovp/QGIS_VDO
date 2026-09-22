"""
Константы проекта
"""

import struct

from qgis.core import Qgis
from qgis.PyQt.QtCore import Qt, QMetaType


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
NAME_LAYER_LINES = 'Ways'

# Словари для безопасной конвертации строк в enum-ы Qt
PEN_STYLES = {
    'solid': Qt.SolidLine,
    'dash': Qt.DashLine,
    'dot': Qt.DotLine,
    'dash dot': Qt.DashDotLine,
    'no': Qt.NoPen
}

FILL_STYLES = {
    'solid': Qt.SolidPattern,
    'no': Qt.NoBrush,
    'dense1': Qt.Dense1Pattern,
    'horizontal': Qt.HorPattern,
    'vertical': Qt.VerPattern
}


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
        'attributes': [('name', QMetaType.Type.QString), ('variant', QMetaType.Type.QString)],
        'styles': [
            {
                'name': 'map',
                'style': {
                    'fill_color': '#FFE5B464',
                    'outline_color': '#FFE500FF',
                    'outline_width': '0.4',
                    'fill_style': 'solid',
                    'outline_style': 'dot'
                }
            },
            {
                'name': 'layout',
                'style': {
                    'fill_color': '#FFE5B40A',  #
                    'outline_color': '#FF8150FF',  #
                    'outline_width': '0.6',
                    'fill_style': 'solid',
                    'outline_style': 'dash'
                }
            }
        ]
    },
    {
        'name': NAME_LAYER_GLOBAL_BOUNDS,
        'geometry': 'Polygon',
        'attributes': [('name', QMetaType.Type.QString)],
        'place': -1,
        'styles': [
            {
                'name': 'bounds',
                'style': {
                    'fill_color': '#78DC7850',     # green
                    'outline_color': '#0032C8FF',    # Яркая синяя граница
                    'outline_width': '0.4',
                    'fill_style': 'solid',
                    'outline_style': 'dot'
                }
            },
        ]
    },
    {
        'name': NAME_LAYER_SHAPES,
        'geometry': 'Polygon',
        'attributes': [('variant', QMetaType.Type.QString),   # отображение, cat.name
                       ('render_order', QMetaType.Type.Int),   # порядок отрисовки symbol в слое
                       ('name', QMetaType.Type.QString),
                       ('id', QMetaType.Type.Int),
                       ('block', QMetaType.Type.QString),
                       ('coord', QMetaType.Type.QString),
                       ],
        'styles': [
            {
                'name': 'SPORTS_COMPLEX',
                'style': [{
                    'fill_color': '#23FF35C8',
                    'outline_color': '#23FF23FF',
                    'outline_width': '0.4',
                    'fill_style': 'cross',
                    'outline_style': 'solid'
                }]
            },
            {
                'name': 'MILITARY_AREA',
                'style': [{
                    'fill_color': '#FF2335C8',
                    'outline_color': '#FF2323FF',
                    'outline_width': '0.4',
                    'fill_style': 'cross',
                    'outline_style': 'solid'
                }]
            },
            {
                'name': 'UNIVERSITY_CAMPUS',
                'style': [{
                    'fill_color': '#3523FFC8',
                    'outline_color': '#3523FFFF',
                    'outline_width': '0.4',
                    'fill_style': 'cross',
                    'outline_style': 'solid'
                }]
            },
            {
                'name': 'HOSPITAL_GROUND',
                'style': [{
                    'fill_color': '#E56E78C8',
                    'outline_color': '#FFBEBEFF',
                    'outline_width': '0.4',
                    'fill_style': 'solid',
                    'outline_style': 'solid'
                }]
            },
            {
                'name': 'CEMETERY',
                'style': [{
                    'fill_color': '#6EE57864',
                    'outline_color': '#003200FF',      # Яркая зелёная граница
                    'outline_width': '0.4',
                    'fill_style': 'cross',
                    'outline_style': 'solid'
                }]
            },
            {
                'name': 'GOLF_COURSE',
                'style': [{
                    'fill_color': '#6EE57864',
                    'outline_color': '#003200FF',      # Яркая зелёная граница
                    'outline_width': '0.4',
                    'fill_style': 'b_diagonal',
                    'outline_style': 'solid'
                }]
            },
            {
                'name': 'AMUSEMENT_PARK',
                'style': [{
                    'fill_color': '#6EE57864',
                    'outline_color': '#003200FF ',      # Яркая зелёная граница
                    'outline_width': '0.4',
                    'fill_style': 'solid',
                    'outline_style': 'solid'
                }]
            },
            {
                'name': 'ISLAND',
                'style': [{
                    'fill_color': '#FFE5B4FF',
                    'outline_color': '#FFE500FF',
                    'outline_width': '0.4',
                    'fill_style': 'solid',
                    'outline_style': 'solid'
                }],
                'label_style': {
                    'font_family': 'Arial',
                    'font_size': 10,
                    'color': '#966100',         # Желтая "#ffdd00"
                    'bold': False,
                    'italic': True,
                    # 'buffer_enabled': True,     # Включаем обводку
                    # 'buffer_color': "#966100",  #  обводка
                    # 'buffer_size': 1.1,
                    'label_min_size': 3.0,  # Скрывать подпись, если полигон на экране меньше 15 мм,
                    "remove_duplicates": True,
                }
            },
            {
                'name': 'WATER',
                'style': [{
                    'fill_color': '#6496FF64',         # Полупрозрачная синяя заливка
                    'outline_color': '#0032C8FF',    # Яркая синяя граница
                    'outline_width': '0.1',
                    'fill_style': 'solid',
                    'outline_style': 'solid',
                }],
                'label_style': {
                    'font_family': 'Arial',
                    'font_size': 10,
                    'color': '#1f78b4',         # Красивый синий
                    'bold': True,
                    'italic': True,
                    'buffer_enabled': True,     # Включаем обводку
                    'buffer_color': '#ffffff',  # Белая обводка
                    'buffer_size': 0.5,
                    'label_min_size': 5.0,  # Скрывать подпись, если полигон на экране меньше 5 мм,
                    "remove_duplicates": True,
                }
            },
            {
                'name': 'AIRPORT_GROUND',
                'style': [{
                    'fill_color': '#BEBEBE64',         # Полупрозрачная темно серая заливка
                    'outline_color': "#B70000FF",      # серая граница
                    'outline_width': '0.1',
                    'fill_style': 'solid',
                    'outline_style': 'solid'
                }]
            },
            {
                'name': 'INDUSTRIAL',
                'style': [{
                    'fill_color': '#5A5A5A64',         # Полупрозрачная темно серая заливка
                    'outline_color': '#323232FF',      # серая граница
                    'outline_width': '0.1',
                    'fill_style': 'solid',
                    'outline_style': 'solid'
                }]
            },
            {
                'name': 'CITY',
                'style': [{
                    'fill_color': '#96969664',         # Полупрозрачная серая заливка
                    'outline_color': '#C8C8C8FF',      # светлая серая граница
                    'outline_width': '0.1',
                    'fill_style': 'solid',
                    'outline_style': 'solid'
                }],
                'label_style': {
                    'font_family': 'Arial',
                    'font_size': 1000,
                    'size_in_meters' : True,
                    'color': "#ffffff",         # Белая
                    'bold': True,
                    'buffer_enabled': True,     # Включаем обводку
                    'buffer_color': "#020000",  # Черная обводка
                    'buffer_size': 0.5,
                    'label_min_size': 0.5,  # Скрывать подпись, если полигон на экране меньше 5 мм,
                    # "remove_duplicates": True,
                }
            },
            {
                'name': 'NATIONAL_PARK',
                'style': [{
                    'fill_color': '#23C82364',         # Полупрозрачная зелёная заливка
                    'outline_color': "#005F00FF",      # Яркая зелёная граница
                    'outline_width': '0.1',
                    'fill_style': 'solid',
                    'outline_style': 'solid'
                }]
            },
            {
                'name': 'FOREST',
                'style': [{
                    'fill_color': "#00820063",         # Полупрозрачная зелёная заливка
                    'outline_color': "#005F00FF",      # Яркая зелёная граница
                    'outline_width': '0.1',
                    'fill_style': 'solid',
                    'outline_style': 'solid'
                }]
            },
            {
                'name': 'SEA_OCEAN',
                'style': [{
                    'fill_color': '#6496FF64',         # Полупрозрачная синяя заливка
                    'outline_color': '#0032C8FF',    # Яркая синяя граница
                    'outline_width': '0.1',
                    'fill_style': 'solid',
                    'outline_style': 'no',
                }],
            },
        ]
    },
    {
        'name': NAME_LAYER_LINES,
        'geometry': 'LineString',
        'attributes': [('variant', QMetaType.Type.QString),   # отображение, cat.name
                       ('render_order', QMetaType.Type.Int),   # порядок отрисовки symbol в слое
                       ('name', QMetaType.Type.QString),
                       ('id', QMetaType.Type.Int),
                       ('block', QMetaType.Type.QString),
                       # непонятные WORD
                       ('c_p_line_sign', QMetaType.Type.QString),   # noqa TSTR? in 30 - все показывают на первый tstr.
                       ('c_b_or_c', QMetaType.Type.QString),    # noqa  hex? in 30 - все = 0
                       ('c_pp_str_name', QMetaType.Type.QString),   # noqa to TSTR, который на имя
                       ('c_38_or_0b_country', QMetaType.Type.QString),   # noqa  hex?- WORD неясной природы
                       ],
        'labels' : [        # rule based labels
            {'description' : 'Roads E', 'color': "#ffffff", 'background': "#00c300", 'label_min_size': 10.0,
             'condition' : "variant ~ '^ROAD_' and name ~ '^E'", 'placement' : Qgis.LabelPlacement.Horizontal,
             'font_family': 'Arial', 'font_size': 10, 'bold': True, 'label_space': True, },
            {'description' : 'Roads 0-9', 'color': "#000000", 'background': "#ffdc32", 'label_min_size': 10.0,
             'condition' : "variant ~ '^ROAD_' and name ~ '^[0-9]'", 'placement' : Qgis.LabelPlacement.Horizontal,
             'font_family': 'Arial', 'font_size': 8, 'bold': True, 'label_space': True, },
            {'description' : 'Roads M', 'color': "#ffffff", 'background': "#ff0707", 'label_min_size': 10.0,
             'condition' : "variant ~ '^ROAD_' and name ~ '^M'", 'placement' : Qgis.LabelPlacement.Horizontal,
             'font_family': 'Arial', 'font_size': 10, 'bold': True, 'label_space': True, },
            {'description' : 'Roads P', 'color': "#000000", 'background': "#ffdc32", 'label_min_size': 10.0,
             'condition' : "variant ~ '^ROAD_' and name ~ '^P'", 'placement' : Qgis.LabelPlacement.Horizontal,
             'font_family': 'Arial', 'font_size': 8, 'bold': True, 'label_space': True, },
            {'description' : 'Roads A', 'color': "#ffffff", 'background': "#3232ff", 'label_min_size': 10.0,
             'condition' : "variant ~ '^ROAD_' and name ~ '^A'", 'placement' : Qgis.LabelPlacement.Horizontal,
             'font_family': 'Arial', 'font_size': 8, 'bold': True, 'label_space': True, },
            #  'label_space': True, - добавить вертикального и горизонтального фонеа таблички
            {'description' : 'ROAD_LOCAL', 'color': "#9c7c5d", 'label_min_size': 10.0,
             'condition' : "variant = 'ROAD_LOCAL'",
             'font_family': 'Arial', 'font_size': 8, 'bold': True, },
            {'description' : 'ROAD_UNPAVED', 'color': "#9c7c5d", 'label_min_size': 10.0,
             'condition' : "variant = 'ROAD_UNPAVED'",
             'font_family': 'Arial', 'font_size': 8, 'bold': True, },
            {'description' : 'CANAL', 'color': "#4400FF", 'label_min_size': 10.0,
             'condition' : "variant = 'CANAL'",
             'font_family': 'Arial', 'font_size': 8, 'bold': True, },
            {'description' : 'RIVER_STREAM', 'color': "#4400FF", 'label_min_size': 10.0,
             'condition' : "variant = 'RIVER_STREAM'",
             'font_family': 'Arial', 'font_size': 7, 'bold': True, },
            {'description' : 'RIVER_MAJOR', 'color': "#4400FF", 'label_min_size': 10.0,
             'condition' : "variant = 'RIVER_MAJOR'", 'placement' : Qgis.LabelPlacement.Curved,
             'font_family': 'Arial', 'font_size': 9, 'bold': True, },

        ],
        'styles': [
            {
                'name': 'ROAD_HIGHWAY',
                'style': [
                    {"color": "#e15a1f", "width": 1.2, "pen_style": "solid"},
                    {"color": "#fff888", "width": 0.6, "pen_style": "solid"}
                ],
            },
            {
                'name': 'ROAD_PRIME',
                'style': [
                    {"color": "#e15a1f", "width": 0.8, "pen_style": "solid"},
                ],
            },
            {
                'name': 'ROAD_MINOR',
                'style': [
                    {"color": "#e15a1f", "width": 0.5, "pen_style": "solid"},
                ],
            },
            {
                'name': 'ROAD_LOCAL',   # Внутриквартальные
                'style': [
                    {"color": "#fff888", "width": 0.5, "pen_style": "solid"},
                ],
            },
            {
                'name': 'ROAD_UNPAVED',     # Грунтовки
                'style': [
                    {"color": "#9c7c5d", "width": 0.5, "pen_style": "solid"},
                ],
            },
            {
                'name': 'ROAD_SLIP',    # Съезды
                'style': [
                    {"color": "#fcd05b", "width": 0.5, "pen_style": "solid"},
                ],
            },
            {
                'name': 'ROAD_ROUNDABOUT',    # Кольца
                'style': [
                    {"color": "#f49c14", "width": 0.5, "pen_style": "solid"},
                ],
            },

            {
                'name': 'RAILWAY',
                'style': [
                    {"color": "#ffffff", "width": 0.8, "pen_style": "solid"},   # Подложка
                    {"color": "#000000", "width": 0.5, "pen_style": "dot"}     # Пунктир сверху
                ],
            },
            {
                'name': 'BORDER',
                'style': [
                    {"color": "#ff0707", "width": 0.9, "custom_dash": [4.0, 4.0]},
                    {"color": "#00c300", "width": 0.6, "custom_dash": [4.0, 4.0], "dash_offset": 4.0},
                ],
            },
            {
                'name': 'CANAL',    #
                'style': [
                    {"color": "#1d70b8", "width": 0.6, "pen_style": "solid"},
                ],
            },
            {
                'name': 'RIVER_STREAM',    #
                'style': [
                    {"color": "#a5d5f5", "width": 0.3, "pen_style": "solid"},
                ],
            },
            {
                'name': 'RIVER_MAJOR',    #
                'style': [
                    {"color": "#005ea5", "width": 0.8, "pen_style": "solid",
                     'min_size': 5.0,  # Скрывать, если на экране меньше 5 мм,  TODO:
                     },
                ],
            },
            {
                'name': 'PEDESTRIAN_ZONE',    #
                'style': [
                    {"color": "#808080", "width": 0.3, "pen_style": "dot"},
                ],
            },
            {
                'name': 'FERRY_CONNECTION',    # паром?
                'style': [
                    {"color": "#a500a2", "width": 0.4, "pen_style": "dot"},
                ],
            },
        ],
    },
]

# STYLE_MAP = {
#     0x61: ("CANAL", "#1d70b8", 0.6, "solid"),
#     0x62: ("RIVER_STREAM", "#a5d5f5", 0.3, "solid"),
#     0x65: ("RIVER_MAJOR", "#005ea5", 0.8, "solid"),
#     # 0x66: ("RAILWAY", "#555555", 0.5, "dash"),
#     # 0x67: ("BORDER", "#850085", 0.4, "dash dot"),
#     0x70: ("PEDESTRIAN_ZONE", "#808080", 0.3, "dot"),
#     0x71: ("FERRY_CONNECTION", "#1d70b8", 0.4, "dot"),
    
#     # 0x68: ("ROAD_HIGHWAY", "#e15a1f", 1.0, "solid"),
#     # 0x69: ("ROAD_PRIME", "#f49c14", 0.8, "solid"),
#     # 0x6A: ("ROAD_MINOR", "#fcd05b", 0.6, "solid"),
#     # 0x6B: ("ROAD_LOCAL: Внутриквартальные", "#ffffff", 0.5, "solid"),
#     # 0x6C: ("ROAD_UNPAVED: Грунтовки", "#9c7c5d", 0.4, "dash"),
#     # 0x6D: ("ROAD_SLIP: Съезды", "#fcd05b", 0.5, "solid"),
#     # 0x6E: ("ROAD_ROUNDABOUT: Кольца", "#f49c14", 0.6, "solid"),
# }

"""
03 - 05 - 08 - 01
01 - 05 - 08

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
