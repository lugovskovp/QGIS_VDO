""" Типы данных для карт - БЛОКОВ
    bmw ee bnl:  00 16 15 1c 14 1d 1e
        future: MAP_AREA(BYTESTRUCT):
        future: POI_CATEGORY
GEO_CATEGORY
GEO_SHAPE

COORD
functions:
    hex2COORD
    float2COORD
    str2COORD
    normLatLng
"""
from __future__ import annotations  # Обязательно на самой первой строчке файла

import ctypes
# import re
import struct

from typing import TYPE_CHECKING

if TYPE_CHECKING:                   # pragma: no cover
    # Этот блок видит только Pylance, интерпретатор Python его игнорирует
    from _typeshed import ReadableBuffer
else:
    # Запасной вариант для рантайма, чтобы не было NameError
    ReadableBuffer = bytes

from QGIS_VDO.vdo.datatypes import BYTESTRUCT, FAR_LIST, VDO_FILE
from QGIS_VDO.vdo.datatypes import DOUBLE_BYTES_CNT
from QGIS_VDO.vdo.consts import struct_UINT, struct_2UINT
from QGIS_VDO.vdo.enums import en_GEO_CATEGORY, en_DRAW_TYPE, en_CARINET_LANGUAGE, en_POI_CAT  # noqa

# use: (cat, draw, ptr, next_ptr) = GEO_CATEGORY_struct.unpack(buf)
GEO_CATEGORY_struct = struct.Struct(">bbHxbH")

# use: (ptr_str, ptr_vrtx, id, ptr_tstr, next_ptr_vrtx) = GEO_SHAPE_struct.unpack(buf)
GEO_SHAPE_struct = struct.Struct(">HHL8x2xHxxH16x")

# use: (   prt_str, ptr_vrtx, id, ptr_linesign, ptr_unk2, ptr_tstr, ptr_unk3,
#           next_ptr_vrtx) = GEO_LINE_struct.unpack(buf)
GEO_LINE_struct = struct.Struct(">HHLHHHHxxH12x")

# use: (x, y) = VERTEX_struct.unpack(buf)
VERTEX_struct = struct.Struct(">HH")

TSTR_struct = struct.Struct(">Hbb")

# на столько делится 1°00′
# 1 градус экватора = 111362м / 5555554 = 0,02м - цена меньшего бита 2cm
MULCOORD = 0x54C562     # was 54C563     # dec 5555555 - волшебный коэффициент перевода.

MOST_SIGNIFICANT_BIT = 0x80000000  # hi bit =1 -> minus val.

# FFFFFFF = 268435455, / 180 = 1degree = 1491308 (16C16C)=
# MULCOORD = 0x54C563 # dec 5555554;
# *90 = 2FAF07B0, *180 = 5F5E0F60,  *180=BEBC1EC0
# 1 градус экватора = 111362м / 5555554 = 0,02м - цена меньшего бита 2cm
# 5555554 / 111362м = 49,88734038540974 - в одном метре


class COORD(BYTESTRUCT):
    """ coordinates, 2 dwords: lon lat """
    #_lon: float         # double lon = ((1.0f * hlon )/ MULCOORD) - 30.0;
    #_lat: float         # double lat = 1.0f * hlat / MULCOORD;
    
    # Регистрируем новые атрибуты экземпляра. Память теперь идеальна, __dict__ нет.
    __slots__ = ('_hlon', '_hlat')
    
    size: int = DOUBLE_BYTES_CNT

    def __init__(self, lo: ReadableBuffer | int | float, la: int | float | None = None) -> None:
        """ Координаты
        Долгота (Lng) E/W - x - lo
        Широта (Lat) N/S - y - la
        """
        # Сценарий A: На входе сырые байты (ReadableBuffer) из vdo
        if isinstance(lo, ReadableBuffer) or isinstance(lo, memoryview) or isinstance(lo, bytearray):
            # Обрезаем буфер строго до 8 байт и передаем в базовый BYTESTRUCT
            if isinstance(lo, memoryview):
                super().__init__(lo[:DOUBLE_BYTES_CNT])   # type: ignore
            else:
                super().__init__(memoryview(lo)[:DOUBLE_BYTES_CNT])   # type: ignore
            
            # Быстро распаковываем сразу оба dword за один проход на Си
            self._hlon, self._hlat = struct_2UINT.unpack_from(self._raw, 0)
            return

        # Сценарий B: На входе два целых числа (hlon, hlat)
        elif isinstance(lo, int) and isinstance(la, int):
            # Маскируем под unsigned dword (в Python это делается через & 0xFFFFFFFF)
            self._hlon = lo & 0xFFFFFFFF
            self._hlat = la & 0xFFFFFFFF
            
            # Упаковываем сразу 8 байт
            coo_bytes = struct_2UINT.pack(self._hlon, self._hlat)
            super().__init__(coo_bytes)
            return

        # Сценарий C: На входе две координаты float (в градусах)
        elif isinstance(lo, float) and isinstance(la, float):
            # Пересчитываем в целые числа
            hlongtitude = int((30 + lo) * MULCOORD) & 0xFFFFFFFF
            hlatitude = int(la * MULCOORD) & 0xFFFFFFFF
            
            self._hlon = hlongtitude
            self._hlat = hlatitude
            
            coo_bytes = struct_2UINT.pack(hlongtitude, hlatitude)
            super().__init__(coo_bytes)
            return

        else:
            raise ValueError(f"Неверные типы аргументов для COORD: lo={type(lo)}, la={type(la)}")

    @property
    def _hlongtitude(self) -> int:
        """ Получение знакового (signed) int из беззнакового _hlon """
        if self._hlon & MOST_SIGNIFICANT_BIT:
            return self._hlon - 0x100000000  # Эквивалентно 2**32, но работает быстрее
        return self._hlon

    @property
    def _hlatitude(self) -> int:
        """ Получение знакового (signed) int из беззнакового _hlat """
        if self._hlat & MOST_SIGNIFICANT_BIT:
            return self._hlat - 0x100000000
        return self._hlat

    @property
    def lon(self) -> float:
        """ Longtitude, x, w|e """
        return (self._hlongtitude / MULCOORD) - 30

    @property
    def lat(self) -> float:
        """ Latitude, y, n/s """
        return self._hlatitude / MULCOORD

    def as_tuple(self) -> tuple[float, float]:
        """ Быстрый экспорт в формате (lon, lat) для QGIS (например, для QgsPointXY) """
        return (self.lon, self.lat)

    def __repr__(self) -> str:
        ch_lat = 'N' if self.lat >= 0 else 'S'
        ch_lon = 'E' if self.lon >= 0 else 'W'
        return f"{abs(self.lat):02.6f}{ch_lat} {abs(self.lon):02.6f}{ch_lon}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, COORD):
            return NotImplemented
        return self._hlat == other._hlat and self._hlon == other._hlon

    def delta(self, other: object) -> str:
        if not isinstance(other, COORD):
            return NotImplemented
        d_lat = self.lat - other.lat
        d_lon = self.lon - other.lon
        return f"lat:{d_lat:.2f}° x lon:{d_lon:.2f}°"


class MAP_AREA(BYTESTRUCT):
    ''' Near offs 0x20 - координаты нижнего левого и верхнего правого, 0x32 - масштаб '''  # noqa: E501
    
    # Регистрируем атрибуты экземпляра для оптимизации памяти и C-style быстродействия
    __slots__ = ('left_bottom', 'right_top', '_scale')
    
    size: int = 20

    def __init__(self, buffer: bytearray) -> None:
        super().__init__(buffer[:self.size])
        self.left_bottom = COORD(self._raw[0:COORD.size])
        self.right_top = COORD(self._raw[COORD.size:(COORD.size * 2)])
        self._scale = self.ushort(0x12)    # 2**scale, на сколько сдвигать влево ху вертекса чтобы получить координаты   # noqa: E501
    
    def __repr__(self):
        ''' View while debug value '''
        val = "{:s}  {:s}".format(self.left_bottom.__repr__(), self.right_top.__repr__())   # noqa: E501
        return val
    
    @property
    def dimentions(self) -> str:
        ''' Размеры в точках и км.'''
        '''111,134861111 км в одном градусе, делим на 60 минут:
           1,85224768519 км в одной минуте, делим на 60 секунд:
         0,0308707947531 км (30,8707947531 м) в одной секунде.'''
        KM_IN_DEGREE = 111.134861111
        grad = (KM_IN_DEGREE * (self.right_top._hlon - self.left_bottom._hlon)) / MULCOORD      # mul = 5555555 # noqa: E501
        val = '{:x}*{:x} ({:0.3f}km)'.format((self.right_top._hlat - self.left_bottom._hlat),   # noqa: E501
                                             (self.right_top._hlon - self.left_bottom._hlon),   # noqa: E501
                                             grad)          # noqa: E501
        return val
       
    @property
    def max_vrt_val(self) -> str:
        ''' Максимально возможное значение Х или Y вертекса'''
        max_x = (self.right_top._hlon - self.left_bottom._hlon) >> self._scale
        max_y = (self.right_top._hlat - self.left_bottom._hlat) >> self._scale
        return "{:04X} {:04X}".format(max_x, max_y)


# -------------------------------------------------------------------------
# прототипы

# ----
class GEO_CATEGORY(BYTESTRUCT):
    '''GEO CATEGORY портотип?, используемый класс - дочерний'''
    
    # Жестко резервируем память под атрибуты экземпляра. __dict__ отсутствует.
    __slots__ = ('category', 'draw', 'obj_size', 'cnt', 'ptr')
    
    size: int = 4  # b b w

    def __init__(self, buffer: bytearray | bytes | memoryview) -> None:
        """
        Принимает буфер (минимум 8 байт для GEO_CATEGORY_struct),
        но сохраняет в базовый класс только свои 4 байта.
        """
        # Распаковываем данные (требуется 8 байт из-за структуры GEO_CATEGORY_struct)
        (cat, draw, ptr, next_draw, next_ptr) = GEO_CATEGORY_struct.unpack(buffer[:8])
        
        # Передаем базовому классу строго его 4 байта
        super().__init__(buffer[:self.size])
        
        self.category = en_GEO_CATEGORY(cat)
        self.draw = en_DRAW_TYPE(draw)
        self.obj_size = 0x10 if draw else 0x14  # 0x10 if POLILINE else 0x14
        
        # Вычисляем количество элементов
        self.cnt = int((next_ptr - ptr) / self.obj_size)
        
        # Корректировка для последнего полигона
        if not draw and next_draw:  # draw == 0 (SHAPE) и next_draw == 1 (POLILINE)
            self.cnt -= 1
            
        self.ptr = ptr

    def __repr__(self) -> str:
        ''' View while debug value'''
        name = self.draw.name if self.draw else 'NOT DEFINED'
        return f"{name} {self.category.name}[{self.cnt}] :0x{self.ptr:02x}"
    
    def __str__(self) -> str:
        return self.__repr__()


# ----
class GEO_SHAPE(BYTESTRUCT):
    '''
    Geo shape - closed, filled poligon
        2h - ptr2str/0;
        2h - ptr2vertexes (first=first vert)
        4h - id [0000 7685]
        8h - LON_LAT
        2h = 00 00 - aligment (??? or POI?)
        2h - ptr2 list strPtr
    '''
    
    # Жестко фиксируем память под все атрибуты экземпляра. __dict__ удален.
    __slots__ = (
        'p_str_name',
        'ptr_vrtx',
        'cnt_vrtx',
        'id',
        'coord',
        'ptr_tstr',
        'name',
        'cat'
    )
    
    size: int = 0x14  # 20 байт

    def __init__(self, buffer: ReadableBuffer, category: en_GEO_CATEGORY) -> None:
        OFFSET_COORD = 8
        VRTX_OBJ_SIZE = 4  # word x, word y
        
        # Оптимизация: берем срез memoryview один раз, чтобы не плодить объекты в цикле/парсере
        mem_buf = memoryview(buffer)
        
        # Для распаковки следующего ptr_vrtx нам нужно прочитать 2 структуры (self.size * 2)
        # Использование структуры GEO_SHAPE_struct.unpack_from эффективнее, так как не создает срез
        (p_str_name, ptr_vrtx, id, ptr_tstr, next_ptr_vrtx) = GEO_SHAPE_struct.unpack_from(mem_buf, 0)
        
        # Передаем базовому классу только его размер (0x14)
        super().__init__(mem_buf[:self.size])
        
        self.p_str_name = p_str_name  # begin zero-ended string
        self.ptr_vrtx = ptr_vrtx
        self.cnt_vrtx = int((next_ptr_vrtx - ptr_vrtx) / VRTX_OBJ_SIZE)
        self.id = id
        
        # Метод self.read() должен возвращать байты из self._raw
        self.coord = COORD(self.read(OFFSET_COORD, COORD.size))
        self.ptr_tstr = ptr_tstr
        self.name = "Proto shape. Need read from parent"
        self.cat = category

    def __repr__(self) -> str:
        ''' View while debug value '''
        name = self.cat.name if self.cat else "NOT DEFINED"
        return f"{name}:[{self.cnt_vrtx}] {self.name}"

    def __str__(self) -> str:
        return self.__repr__()

    # GEO_SHAPE


# ----

class GEO_LINE(BYTESTRUCT):
    '''
    Geo segment of line - poligon
        2h - PTR         p_str_name - ptr2str/0;    nullable
        2h - PTR         ptr_vrtx       p_vertexes_obj; ptr2vertexes
        4h - DWORD       id
        2h - PTR   tstr_regi      ptr_linesign, p_line_sign; // Or start pstr
        2h - WORD  or_b_or_c;   (??? lenght? time for drive???)
        2h - PTR   tstr_name         ptr_tstr   gbr border - 04  p_p_str_name; // ptr to GEO_OBJ_STR
        4h - WORD   or_38_or_0_b_country; ???en_country??? gbr border - 0
    '''
    
    # Резервируем память под все атрибуты экземпляра. Снижает потребление RAM и ускоряет доступ.
    __slots__ = (
        'p_str_name',
        'ptr_vrtx',
        'id',
        'POI_regi',
        'or_b_or_c',
        'tstr_name',
        'or_38_or_0_b_country',
        'cnt_vrtx',
        'name',
        'cat'
    )
    
    size: int = 0x10  # 16 байт

    def __init__(self, buffer: bytearray | bytes | memoryview, category: en_GEO_CATEGORY) -> None:
        VRTX_OBJ_SIZE = 4       # word x, word y
        
        # Оптимизация: создаем memoryview один раз для прямого чтения без создания копий буфера
        mem_buf = memoryview(buffer)
        
        # Используем unpack_from для чтения данных на Си-уровне без нарезки buffer[:size*2]
        (p_str_name,
         ptr_vrtx,
         id,
         POI_regi,
         or_b_or_c,
         tstr_name,
         or_38_or_0_b_country,
         next_ptr_vrtx) = GEO_LINE_struct.unpack_from(mem_buf, 0)
         
        # Передаем базовому классу первые 16 байт (size)
        super().__init__(mem_buf[:self.size])
        
        self.p_str_name = p_str_name           # begin zero-ended string
        self.ptr_vrtx = ptr_vrtx               # begin vertexes
        self.id = id
        self.POI_regi = POI_regi               # ptstr - but strange, unkn
        self.or_b_or_c = or_b_or_c             # estimated length or travel time
        self.tstr_name = tstr_name             # ptr to GEO_OBJ_STR
        self.or_38_or_0_b_country = or_38_or_0_b_country
        self.cnt_vrtx = int((next_ptr_vrtx - ptr_vrtx) / VRTX_OBJ_SIZE)
        self.name = "Proto line. Need read from parent"
        self.cat = category

    def __repr__(self) -> str:
        ''' View while debug value '''
        name = self.cat.name if self.cat else "NOT DEFINED"
        return f"{name}:[{self.cnt_vrtx}] {self.name}"

    def __str__(self) -> str:
        return self.__repr__()
    # GEO_LINE


# ----
class VERTEX(BYTESTRUCT):
    '''' прототип класса вертекса - координаты ХY точек на map area карты'''
    
    # Фиксируем слоты для полей координат. __dict__ отсутствует.
    __slots__ = ('_x', '_y')
    
    size: int = 4   # размер элемента класса в байтах

    def __init__(self, buffer: bytearray | bytes | memoryview) -> None:
        mem_buf = memoryview(buffer)
        
        if len(mem_buf) < self.size:
            # Инициализируем родительский слот пустой памятью, чтобы не ломать архитектуру __slots__
            super().__init__(mem_buf[:0])
            self._x = None
            self._y = None
            return
            
        super().__init__(mem_buf[:self.size])
        # Распаковываем напрямую из memoryview без создания промежуточных объектов в RAM
        self._x, self._y = VERTEX_struct.unpack_from(mem_buf, 0)
    
    @property
    def x(self) -> int | None:        # координата х
        return self._x

    @property
    def y(self) -> int | None:        # координата y
        return self._y

    def getXY(self) -> tuple[int | None, int | None]:
        return (self._x, self._y)
    
    def __repr__(self) -> str:
        ''' View vertex hex val - debug value '''
        if self._x is None or self._y is None:
            return "INVALID VERTEX (EMPTY BUF)"
        return "{:04X} {:04X}".format(self._x, self._y)

    def __str__(self) -> str:
        return self.__repr__()
    
    # VERTEX_PROTO


# ----
class TSTR(BYTESTRUCT):
    """
    прототип TSTR - набора переводов/синонимов
            typedef struct{
        0    PTR p_str;
        2    en_LANGUAGE lang;
        3    en_GEO_OBJ_STR str_type;
            typedef enum <uchar>{
                __shape =   0,
                __alias =   2,
                __street =  8,
                __poliline =0x10
            }en_GEO_OBJ_STR
    """
    
    # Фиксируем слоты для всех полей экземпляра класса. __dict__ полностью удален.
    __slots__ = ('p_str', 'lang', 'geotype', 'name')
    
    size: int = 4   # размер элемента класса в байтах

    def __init__(self, buffer: bytearray | bytes | memoryview) -> None:
        # Сохраняем первые 4 байта в базовый класс
        super().__init__(buffer[:self.size])
        
        # Распаковываем данные из сохраненного memoryview (_raw)
        (p_str, lang, obj_type) = TSTR_struct.unpack(self._raw)
        
        self.p_str = p_str
        self.lang = en_CARINET_LANGUAGE(lang)
        self.geotype = hex(obj_type)
        self.name = "Proto. Name set where called"

    def __repr__(self) -> str:
        ''' View while debug value '''
        return f"{self.lang.value} {self.geotype}:[{self.lang.name}]: {self.name}"

    def __str__(self) -> str:
        return self.__repr__()

    # TSTR


class POI_CATEGORY(BYTESTRUCT):
    """
    POI_CATEGORY 3*DWORD
        QWORD   POIs  FAR_LIST
        WORD    en_POI_CATEGORY - enum тип, категория POI
        WORD    reference_addr_start  В 0x0a - УКАЗЫВАЕТ НА НАЧАЛО СТРОКОВЫХ ДАННЫХ '''
    """
    bytescnt: int = 12  # 3*DWORD 0a 0c размер элемента класса в байтах

    def __init__(self, buffer: ReadableBuffer, parent_vdo: VDO_FILE) -> None:
        """ """
        super().__init__(memoryview(buffer)[:self.bytescnt])
        self.fl_POIs = FAR_LIST(self.read(0, FAR_LIST.size), parent_vdo)
        self.poi_type = en_POI_CAT(self.ushort(8))  # offs en_POI_CATEGORY - enum тип, категория POI # noqa
        self.p_str = self.ushort(10)
        self.name = "Proto. Name set where called"

    # @property
    # def fl_POIs(self):
    #     ''' QWORD   POIs  FAR_LIST '''
    #     res = FAR_LIST(self.read(0, FAR_LIST.bytescnt), )
    #     return res
    # @property
    # def poi_cat(self):
    #     ''' WORD    en_POI_CATEGORY - enum тип, категория POI '''
    #     res = self.read(FAR_LIST.bytescnt+1 , 1) # from FAR_LIST.bytescnt, zero, enum
    #     return en_POI_CATEGORY( struct.unpack('>B', res)[0] )
    # @property
    # def pname(self):
    #     ''' WORD    reference_addr_start  В 0X0a - УКАЗЫВАЕТ НА НАЧАЛО СТРОКОВЫХ ДАННЫХ ''' # noqa
    #     return self.ushort(0x0a)
    #     barr = self.read(10, 2)
    #     res = struct.unpack('>H', barr)[0]
    #     return res


# -------------------------------------------------------------------------
# functions

def hex2COORD(hex_longtude: int, hex_latitude: int) -> COORD:
    """
    Create COORD by hex_vdo values lo + la
        Args:
            # lon - x we, lat - y sn
        Returns:
            res: COORD
    """
    # to unsigned dword
    hex_latitude = ctypes.c_uint32(hex_latitude).value
    hex_longtude = ctypes.c_uint32(hex_longtude).value

    # to bytes
    coo_by = (struct_UINT.pack(hex_longtude)
              + struct_UINT.pack(hex_latitude))
    res = COORD(coo_by)
    return res
    """
    hex_latitude = 0xffffffff & hex_latitude    # to dword
    if hex_latitude < 0:                        # Negative val
        hex_latitude = 0x80000000 | (-hex_latitude)
       
    hex_longtude = 0xffffffff & hex_longtude    # to dword
    if hex_longtude < 0:                        # Negative val
        hex_longtude = 0x80000000 | (-hex_longtude)
    """


# def str2COORD(lon_lat: str) -> tuple:
#     '''Координаты по строке, lon где E|W, lat-N|S, exmpl: 73.920441N 54.297287E
#     Args:
#         lon_lat: str  # Широта, latitude и Долгота, longtitude  градусы
#     Returns:
#         coordinates: tuple(N_lat: hlat, E_lng: hlon)
#     '''
#     # lon_lat - типа 73.92N 54.30E, разделитель - пробел
#     # вычистить мусор

#     lon_lat = re.sub(r'\s+', ' ', lon_lat)      # remove multispaces
#     lon_lat = re.sub(r',\s', ' ', lon_lat)      # remove ', ' between digits
#     lon_lat = re.sub(r',', '.', lon_lat)        # . in digits instead ,
#     splted = lon_lat.split(' ')
#     # две части?
#     if len(splted) != 2:
#         raise TypeError(f"В строке {lon_lat} координаты не распознаны")
#     # разбираемся - где долгота, где широта
#     for k in splted:
#         if re.search(r'[NnSs]$', k):         # последняя буква - север или юг
#             lat = float(re.sub(r'[NnSs]$', '', k))
#             if re.search(r'[Ss]', k):
#                 lat = -lat
#         elif re.search(r'[EeWw]$', k):         # последняя буква - восток или запад
#             lon = float(re.sub(r'[EeWw]$', '', k))
#             if re.search(r'[Ww]', k):
#                 lon = -lon
#         else:
#             raise TypeError(f"В строке {lon_lat} должны быть N (или S) и E (или W)")
#     # вернуть координаты
#     res = float2COORD(lat, lon)
#     return res


# def float2COORD(n_latitude: float, e_longtude: float) -> tuple:
#     ''' Координаты в градусах (широта, долгота)
#     Args:
#         n_latitude: float   # Широта, S/N latitude градусы
#         e_longtude: float   # Долгота, E/W longtitude градусы
#     Returns:
#         coordinates: tuple(N_lat: hlat, E_lng: hlon)
#         '''
#     res: COORD
#     lat, lon = normLatLng(n_latitude, e_longtude)   # lon - x we, lat - y sn
#     hlon = int((lon + 30) * MULCOORD)   # self._lon = ( self._hlon / MULCOORD ) - 30
#     hlat = int(lat * MULCOORD)          # self._lat =   self._hlat / MULCOORD
#     res = hex2COORD(hlon, hlat)
#     return res


def normLatLng(n_latitude: float, e_longtude: float):
    ''' Нормализует координаты в градусах (широта, долгота)
        возвращает нормализованные (N_lat, E_lng)
    Args:
        n_latitude: float   # Широта, latitude градусы
        e_longtude: float   # Долгота, longtitude градусы
    Returns:
        coordinates: tuple(N_lat: float, E_lng: float)
    '''
    # избавление от кратности круга (370 = 10), КРОМЕ ЭТОГО ПЕРЕВОД В -110 % 360 = 250
    E_lng = float(e_longtude) % 360
    N_lat = float(n_latitude) % 360
    # При переходе в противоположное полушарие широты, долгота +=180
    if 90 < N_lat < 270:     # II and III quadrant.
        # 100N = 80N     # Долгота, longtitude 0 -> 90 -> 0-> -90 -> 0
        N_lat = 180 - n_latitude
        # перепрыг в иное полушарие
        E_lng += 180
    # избавление от кратности круга (370 = 10)
    N_lat = float(N_lat) % 360
    E_lng = float(E_lng) % 360
    # N-S, E-W
    E_lng = E_lng - 360 if E_lng > 180 else E_lng      # 270E = 90W = -90E; 190E = -170E
    N_lat = N_lat - 360 if N_lat > 180 else N_lat      # 350N = -10N
    return (N_lat, E_lng)

# -------------------------------------------------------------------------


if __name__ == '__main__':

    #
    sa1 = b'\x06\xe6y\xaa\x0b\xb1\xde\x1f'
    sa2 = b'\nlvM\x10_\xf3\xf9'
    sa3 = b'\xf1\x190\x00\xbczP\x00'
    sa4 = b'Q\x190\x00\x1czP\x00'

    c1 = COORD(sa1)  # 35.317104N 9.161808W
    c2 = COORD(sa2)  # 49.450295N 1.478463E
    c3 = COORD(sa3)  # 203.910287S 75.001364W
    c4 = COORD(sa4)  # 86.000034N 214.908958E

    coo1 = COORD(115767722, 196206111)

    buff = b'\xaa\x00\x124Ufw\x88Test\x00\x00\x00\x00\x06\xe6y\xaa\x0b\xb1\xde\x1f'
    co_bu = COORD(buff)

    base_struct = BYTESTRUCT(b'\xaa\x00\x124Ufw\x88Test\x00\x00\x00\x00\x06\xe6y\xaa\x0b\xb1\xde\x1f')
    coord_buffer = base_struct.read(16, 8)
    a = COORD(coord_buffer)
    
    # 203.910287S 75.001364W    b'\xf1\x190\x00\xbczP\x00'
    coo2longtitude = COORD(-250007552, -1132834816)
    coo2hlon = COORD(4044959744, 3162132480)
    eq2True = coo2hlon == coo2longtitude
    # lat -203.91028727102872 lon -75.0013638601364
    coo2degree = COORD(-75.0013638601364, -203.91028727102872)
    eq2tooTrue = coo2hlon == coo2degree

    # b'\x06\xe6y\xaa\x0b\xb1\xde\x1f'

    # import ctypes
    # dword_val = ctypes.c_int32(0xFFFFFFFF).value
    # print(dword_val)    # Выведет: -1
    pass

# import ctypes

# # Приведение к 32-битному знаковому целому
# dword_val = ctypes.c_int32(0xFFFFFFFF).value
# print(dword_val) # Выведет: -1


"""
# noqa: E501, W291


    

"""
