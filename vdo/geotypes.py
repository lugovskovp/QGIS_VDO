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

import re
import struct

from vdo.datatypes import BYTESTRUCT
from vdo.datatypes import DOUBLE_BYTES_CNT, UINT_struct
from vdo.enums import en_GEO_CATEGORY, en_DRAW_TYPE

# use: (cat, draw, ptr, next_ptr) = GEO_CATEGORY_struct.unpack(buf)
GEO_CATEGORY_struct = struct.Struct(">bbHxxH")

# use: (ptr_str, ptr_vrtx, id, ptr_tstr, next_ptr_vrtx) = GEO_SHAPE_struct.unpack(buf)
GEO_SHAPE_struct = struct.Struct(">HHL8x2xHxxH16x")

# use: (   prt_str, ptr_vrtx, id, ptr_linesign, ptr_unk2, ptr_tstr, ptr_unk3,
#           next_ptr_vrtx) = GEO_LINE_struct.unpack(buf)
GEO_LINE_struct = struct.Struct(">HHLHHHHxxH12x")

# use: (x, y) = VERTEX_struct.unpack(buf)
VERTEX_struct = struct.Struct(">HH")

# на столько делится 1°00′
# 1 градус экватора = 111362м / 5555554 = 0,02м - цена меньшего бита 2cm
MULCOORD = 0x54C563     # dec 5555555 - волшебный коэффициент перевода.
                        
MOST_SIGNIFICANT_BIT = 0x80000000  # hi bit =1 -> minus val.


class COORD(BYTESTRUCT):
    """ coordinates, 2 dwords: lon lat """
    #_lon: float         # double lon = ((1.0f * hlon )/ MULCOORD) - 30.0;
    #_lat: float         # double lat = 1.0f * hlat / MULCOORD;
    _hlon: int
    _hlat: int
       
    size: int = DOUBLE_BYTES_CNT     # 2*DWORD: lon lat

    def __init__(self, buffer: bytearray) -> None:
        """ """

        # === bytearray
        super().__init__(buffer[:DOUBLE_BYTES_CNT])   # 8 - self.size

        self._hlon = UINT_struct.unpack(self._raw[:4])[0]
        self._hlat = UINT_struct.unpack(self._raw[4:8])[0]
        if MOST_SIGNIFICANT_BIT & self._hlon:     # hi bit =1 -> minus val.
            # self.hlo = ctypes.c_int32(self._hlon).value
            self._hlon = 0 - (0xffffffff - self._hlon + 1)
        if MOST_SIGNIFICANT_BIT & self._hlat:     # hi bit =1 -> minus val.
            # self.hla = ctypes.c_int32(self._hlat).value
            self._hlat = 0 - (0xffffffff - self._hlat + 1)
        self.lon = (self._hlon / MULCOORD) - 30     # e/w
        self.lat = self._hlat / MULCOORD            # n/s

        return
        # FFFFFFF = 268435455, / 180 = 1degree = 1491308 (16C16C)=
        # MULCOORD = 0x54C563 # dec 5555554;
        # *90 = 2FAF07B0, *180 = 5F5E0F60,  *180=BEBC1EC0
        # 1 градус экватора = 111362м / 5555554 = 0,02м - цена меньшего бита 2cm
        # 5555554 / 111362м = 49,88734038540974 - в одном метре

    def __repr__(self):
        ''' View while debug value'''
        ch_lat = 'N' if self.lat >= 0 else 'S'
        ch_lon = 'E' if self.lon >= 0 else 'W'
        return "{:02.6f}{:s} {:02.6f}{:s}".format(abs(self.lat),
                                                  ch_lat, abs(self.lon),
                                                  ch_lon)


class MAP_AREA(BYTESTRUCT):
    ''' Near offs 0x20 - координаты нижнего левого и верхнего правого, 0x32 - масштаб '''  # noqa: E501
    size: int = 20

    def __init__(self, buffer: bytearray) -> None:
        super().__init__(buffer[:self.size])
        self.left_bottom = COORD(self._raw[0:COORD.size])
        self.rigth_top = COORD(self._raw[COORD.size:(COORD.size * 2)])
        self._scale = self.ushort(0x12)    # 2**scale, на сколько сдвигать влево ху вертекса чтобы получить координаты   # noqa: E501
    
    def __repr__(self):
        ''' View while debug value '''
        val = "{:s}  {:s}".format(self.left_bottom.__repr__(), self.rigth_top.__repr__())   # noqa: E501
        return val
    
    @property
    def dimentions(self) -> str:
        ''' Размеры в точках и км.'''
        '''111,134861111 км в одном градусе, делим на 60 минут:
           1,85224768519 км в одной минуте, делим на 60 секунд:
         0,0308707947531 км (30,8707947531 м) в одной секунде.'''
        KM_IN_DEGREE = 111.134861111
        grad = (KM_IN_DEGREE * (self.rigth_top._hlon - self.left_bottom._hlon)) / MULCOORD      # mul = 5555555 # noqa: E501
        val = '{:x}*{:x} ({:0.3f}km)'.format((self.rigth_top._hlat - self.left_bottom._hlat),   # noqa: E501
                                             (self.rigth_top._hlon - self.left_bottom._hlon),   # noqa: E501
                                             grad)          # noqa: E501
        return val
       
    @property
    def max_vrt_val(self) -> str:
        ''' Максимально возможное значение Х или Y вертекса'''
        max_x = (self.rigth_top._hlon - self.left_bottom._hlon) >> self._scale
        max_y = (self.rigth_top._hlat - self.left_bottom._hlat) >> self._scale
        return "{:04X} {:04X}".format(max_x, max_y)


# -------------------------------------------------------------------------
# прототипы

# ----
class GEO_CATEGORY(BYTESTRUCT):
    '''GEO CATEGORY портотип?, используемый класс - дочерний'''
    cat: en_GEO_CATEGORY = None
    draw: en_DRAW_TYPE = None  # SHAPE = 0, POLILINE = 1
    cnt: int = 0    # сколько элементов в категории (расчетом, разница со следующим ptr
    ptr: int = 0    # near на первый объект
    obj_size: int = 0          # shape size = 0x14, line = 0x10
    size: int = 4               # b b w

    def __init__(self, buffer) -> None:
        """
        size = 4, но в следующих 4 есть следующий CAT, с ptr, и по их разнице
                получим количество элементов этой категории
        """
        (cat, draw, ptr, next_ptr) = GEO_CATEGORY_struct.unpack(buffer)
        # 4 важны, для инициализации нужны ещё ptr следущего
        super().__init__(buffer[:self.size])
        self.category = en_GEO_CATEGORY(cat)
        self.draw = en_DRAW_TYPE(draw)
        self.obj_size = 0x10 if draw else 0x14  # 0x10 if POLILINE else if SHAPE 0x14
        self.cnt = int((next_ptr - ptr) / self.obj_size)
        self.ptr = ptr

    def __repr__(self):
        ''' View while debug value'''
        val = f"{self.ptr:02x} {self.draw.name} {self.category.name}:[{self.cnt}]"
        return val
    
    def __str__(self) -> str:
        return self.__repr__()

    pass  # GEO_CATEGORY_PROTO


# ----
class GEO_SHAPE(BYTESTRUCT):
    '''
    Geo shape - closed, filled poligon
        2h - ptr2str/0;
        2h - ptr2vertexes (first=first vert)
        4h - id [0000 7685]
        8h - LON_LAT
        2h = 00 00 - aligment
        2h - ptr2 list strPtr
    '''
    size: int = 0x14              # ptr ptr dword qword w ptr
    name: str = ''

    def __init__(self, buffer: bytearray, category: en_GEO_CATEGORY) -> None:
        OFFSET_COORD = 8
        VRTX_OBJ_SIZE = 4       # word x, word y
        (ptr_str, ptr_vrtx, id, ptr_tstr, next_ptr_vrtx) = GEO_SHAPE_struct.unpack(buffer[:(self.size * 2)])  # noqa: E501
        super().__init__(buffer[:self.size])  # первые 0x14 в raw, для инициализации нужны ещё ptr следущего # noqa: E501
        self.ptr_str = ptr_str    # begin zero-ended string
        self.ptr_vrtx = ptr_vrtx
        self.cnt_vrtx = int((next_ptr_vrtx - ptr_vrtx) / VRTX_OBJ_SIZE)
        self.id = id
        self.coord = COORD(self.read(OFFSET_COORD, COORD.size))
        self.ptr_tstr = ptr_tstr
        self.name = "Proto. Need read from parent"
        self.cat = category
        pass
  
    def __repr__(self):
        ''' View while debug value'''
        val = f"{self.cat.category.name}:[{self.cnt_vrtx}] {self.name}"
        return val
    pass    # GEO_SHAPE_PROTO


# ----

class GEO_LINE(BYTESTRUCT):
    '''
    # noqa: E501
    Geo segment of line - poligon
        PTR         p_str_name <bgcolor=cGreen>;
        PTR         p_vertexes_obj;
            local WORD vertex_cnt <format=hex> = 0;
                // ReadUInt(FTell() = 0 in last
            if( ReadUInt( FTell() ) ) vertex_cnt = (ReadUShort(FTell()+0eh) - p_vertexes_obj.Ptr )/4;
        DWORD       id<format=hex, fgcolor=cBlue, bgcolor=cLtYellow>;
        // LON_LAT     THIS_NOT_coord; // THIS_NOT_coord    bl_offset( 0x293B9000 );
        PTR   p_line_sign; // Or start pstr
        WORD  b_or_c;
        PTR   p_p_str_name; // ptr to GEO_OBJ_STR
        WORD   or_38_or_0_b_country;
    '''
    size: int = 0x10              # ptr ptr dword qword w ptr
    name: str = ''
    cnt_vrtx: int = 0

    def __init__(self, buffer: bytearray, category: en_GEO_CATEGORY) -> None:
        VRTX_OBJ_SIZE = 4       # word x, word y
        (ptr_str,
         ptr_vrtx,
         id,
         ptr_linesign,
         ptr_unk2,
         ptr_tstr,
         ptr_unk3,
         next_ptr_vrtx) = GEO_LINE_struct.unpack(buffer[:(self.size * 2)])  # noqa: E501
        super().__init__(buffer[:self.size])  # первые 0x10 в raw
        self.ptr_str = ptr_str           # begin zero-ended string
        self.ptr_vrtx = ptr_vrtx         # begin vertexes
        self.id = id
        self.ptr_unk1 = ptr_linesign      # ptstr - but strange, unkn
        self.ptr_unk2 = ptr_unk2   # named as "b or c" but bl_addr(0x03c68a03); // 0x 1e345000 - 0x1c kaliningrad = 0 # noqa: E501
        self.ptr_tstr = ptr_tstr    # ptr to GEO_OBJ_STR
        self.ptr_unk3 = ptr_unk3    # last 2 butes - strange w|o system length?)  or_38_or_0_b_country; # noqa: E501
        self.cnt_vrtx = int((next_ptr_vrtx - ptr_vrtx) / VRTX_OBJ_SIZE)
        self.name = "Proto. Need read from parent"
        self.cat = category
    
    def __repr__(self):
        ''' View while debug value '''
        val = f"{self.cat.category.name}:[{self.cnt_vrtx}] {self.name}"
        return val
    pass    # GEO_LINE_PROTO


# ----
class VERTEX(BYTESTRUCT):
    '''' прототип класса вертекса - координаты ХY точек на map area карты'''
    size: int = 4   # размер элемента класса в байтах

    def __init__(self, buffer: bytearray) -> None:
        """ """
        super().__init__(buffer[:self.size])
        (self._x, self._y) = VERTEX_struct.unpack(buffer)
        # self.x = self.ushort(0)
        # self.y = self.ushort(2)
    
    @property
    def x(self) -> int:        # координата х
        return self._x

    @property
    def y(self) -> int:        # координата y
        return self._y

    def getXY(self) -> tuple:
        return (self.x, self.y)
    
    def __repr__(self) -> str:
        ''' View vertex hex val - debug value '''
        val = "{:04X} {:04X}".format(self.x, self.y)
        return val
    pass    # VERTEX_PROTO


# -------------------------------------------------------------------------
# functions

def hex2COORD(hex_longtude: int, hex_latitude: int) -> COORD:
    ''' Ret COORD by hex_vdo values lo&la'''
    res: COORD
    hex_latitude = 0xffffffff & hex_latitude    # to dword
    if hex_latitude < 0:                        # Negative val
        hex_latitude = 0x80000000 | (-hex_latitude)
       
    hex_longtude = 0xffffffff & hex_longtude    # to dword
    if hex_longtude < 0:                        # Negative val
        hex_longtude = 0x80000000 | (-hex_longtude)

    coo_by = (UINT_struct.pack(">L", hex_longtude)
              + UINT_struct.pack(">L", hex_latitude))
    res = COORD(coo_by)
    '''    #int DWORD со знаком в старшем бите
    if 0x80000000 & self._hlon:     # hi bit =1 -> minus val.
        self._hlon = 0 - (0xffffffff - self._hlon + 1)
    if 0x80000000 & self._hlat:     # hi bit =1 -> minus val.
        self._hlat = 0 - (0xffffffff - self._hlat + 1)    '''
    return res


def str2COORD(lon_lat: str) -> tuple:
    '''Координаты по строке, lon где E|W, lat-N|S, exmpl: 73.920441N 54.297287E
    Args:
        lon_lat: str  # Широта, latitude и Долгота, longtitude  градусы
    Returns:
        coordinates: tuple(N_lat: hlat, E_lng: hlon)
    '''
        
    # lon_lat - типа 73.92N 54.30E, разделитель - пробел
    # вычистить мусор

    lon_lat = re.sub(r'\s+', ' ', lon_lat)      # remove multispaces
    lon_lat = re.sub(r',\s', ' ', lon_lat)      # remove ', ' between digits
    lon_lat = re.sub(r',', '.', lon_lat)        # . in digits instead ,
    splted = lon_lat.split(' ')
    # две части?
    if len(splted) != 2:
        raise TypeError(f"В строке {lon_lat} координаты не распознаны")
    # разбираемся - где долгота, где широта
    for k in splted:
        if re.search(r'[NnSs]$', k):         # последняя буква - север или юг
            lat = float(re.sub(r'[NnSs]$', '', k))
            if re.search(r'[Ss]', k):
                lat = -lat
        elif re.search(r'[EeWw]$', k):         # последняя буква - восток или запад
            lon = float(re.sub(r'[EeWw]$', '', k))
            if re.search(r'[Ww]', k):
                lon = -lon
        else:
            raise TypeError(f"В строке {lon_lat} должны быть N (или S) и E (или W)")
    # вернуть координаты
    res = float2COORD(lat, lon)
    return res


def float2COORD(n_latitude: float, e_longtude: float) -> tuple:
    ''' Координаты в градусах (широта, долгота)
    Args:
        n_latitude: float   # Широта, latitude градусы
        e_longtude: float   # Долгота, longtitude градусы
    Returns:
        coordinates: tuple(N_lat: hlat, E_lng: hlon)
        '''
    res: COORD
    lat, lon = normLatLng(n_latitude, e_longtude)
    hlon = int((lon + 30) * MULCOORD)   # self._lon = ( self._hlon / MULCOORD ) - 30
    hlat = int(lat * MULCOORD)          # self._lat =   self._hlat / MULCOORD
    res = hex2COORD(hlon, hlat)
    return res


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
    a1 = b'\x06\xe6y\xaa\x0b\xb1\xde\x1f'
    a2 = b'\nlvM\x10_\xf3\xf9'
    a3 = b'(\xc7\xb2\xb8\x17)\x94p'
    a4 = b'\x0cS\xbd\xcb\x11\xb7\x02='

    c1 = COORD(a1)  # 35.317104N 9.161808W
    c2 = COORD(a2)  # 49.450295N 1.478463E
    c3 = COORD(a3)  # 69.948177N 93.151702E
    c4 = COORD(a4)  # 53.497145N 7.226644E

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
//GEO_VERTEX
typedef struct{
    WORD x;
    WORD y;
}GEO_VERTEX

class POI_CATEGORY(BYTESTRUCT):     #   
    ''' POI_CATEGORY 3*DWORD
        QWORD   POIs  FAR_LIST
        WORD    en_POI_CATEGORY - enum тип, категория POI 
        WORD    reference_addr_start  В 0X0a - УКАЗЫВАЕТ НА НАЧАЛО СТРОКОВЫХ ДАННЫХ ''' 
    bytescnt: int = 12  # 3*DWORD 0a 0c
    def __init__(self, bytes_arr) -> None:
        if (len(bytes_arr) < self.bytescnt):
            raise TypeError(f"Размер массива байтов {len(bytes_arr)} меньше требуемого {self.bytescnt}")
        super().__init__(bytes_arr[:self.bytescnt]) # 12 - self.bytescnt
    @property
    def fl_poi(self):
        ''' QWORD   POIs  FAR_LIST '''
        res = FAR_LIST(self.read(0, FAR_LIST.bytescnt)) 
        return res
    @property
    def poi_cat(self):
        ''' WORD    en_POI_CATEGORY - enum тип, категория POI '''
        res = self.read(FAR_LIST.bytescnt+1 , 1) # from FAR_LIST.bytescnt, zero, enum
        return en_POI_CATEGORY( struct.unpack('>B', res)[0] )
    @property
    def pname(self):
        ''' WORD    reference_addr_start  В 0X0a - УКАЗЫВАЕТ НА НАЧАЛО СТРОКОВЫХ ДАННЫХ '''
        return self.ushort(0x0a) 
        barr = self.read(10, 2)
        res = struct.unpack('>H', barr)[0]
        return res

"""
