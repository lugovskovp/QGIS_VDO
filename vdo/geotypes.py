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

POI_ITEM

POI_BRIF
POI_DETAILS
POI
"""
from __future__ import annotations  # Обязательно на самой первой строчке файла

# import ctypes
# import re
import struct

from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:                   # pragma: no cover
    # Этот блок видит только Pylance, интерпретатор Python его игнорирует
    from _typeshed import ReadableBuffer
else:
    # Запасной вариант для рантайма, чтобы не было NameError
    ReadableBuffer = bytes

from QGIS_VDO.vdo.datatypes import BYTESTRUCT, FAR_LIST, VDO_FILE, LIST, struct_LIST
from QGIS_VDO.vdo.datatypes import DOUBLE_BYTES_CNT
from QGIS_VDO.vdo.consts import struct_2UINT, MOST_SIGNIFICANT_BIT
from QGIS_VDO.vdo.enums import en_GEO_CATEGORY, en_DRAW_TYPE, en_CARINET_LANGUAGE, en_POI_CAT  # noqa

# use: (cat, draw, ptr, next_ptr) = GEO_CATEGORY_struct.unpack(buf)
GEO_CATEGORY_struct = struct.Struct(">BBHxBH")

# use: (ptr_str, ptr_vrtx, id, ptr_tstr, next_ptr_vrtx) = GEO_SHAPE_struct.unpack(buf)
GEO_SHAPE_struct = struct.Struct(">HHL8x2xHxxH16x")

# use: (   prt_str, ptr_vrtx, id, ptr_linesign, ptr_unk2, ptr_tstr, ptr_unk3,
#           next_ptr_vrtx) = GEO_LINE_struct.unpack(buf)
GEO_LINE_struct = struct.Struct(">HHLHHHHxxH12x")

# use: (x, y) = VERTEX_struct.unpack(buf)
VERTEX_struct = struct.Struct(">HH")

TSTR_struct = struct.Struct(">HBB")

POI_ITEM_struct = struct.Struct(">LHHHHHHLLL")

struct_POI_BRIF = struct.Struct(">HBBHH")

struct_POI_DETAILS = struct.Struct(">HHHHHHHHHHLHHL")


# на столько делится 1°00′
# 1 градус экватора = 111362м / 5555554 = 0,02м - цена меньшего бита 2cm
MULCOORD = 0x54C562     # was 54C563     # dec 5555555 - волшебный коэффициент перевода.

# MOST_SIGNIFICANT_BIT = 0x80000000  # hi bit =1 -> minus val.

# FFFFFFF = 268435455, / 180 = 1degree = 1491308 (16C16C)=
# MULCOORD = 0x54C563 # dec 5555554;
# *90 = 2FAF07B0, *180 = 5F5E0F60,  *180=BEBC1EC0
# 1 градус экватора = 111362м / 5555554 = 0,02м - цена меньшего бита 2cm
# 5555554 / 111362м = 49,88734038540974 - в одном метре

KM_IN_DEGREE = 111.134861111


class COORD(BYTESTRUCT):
    """Coordinates, 2 dwords: lon lat. Deeply optimized for PyQGIS memory footprint."""
    
    # Жестко фиксируем слоты, убираем __dict__. Имена синхронизированы с block_0x09
    __slots__ = ('_hlon', '_hlat', '_precalculated_lon', '_precalculated_lat')
    
    size: int = DOUBLE_BYTES_CNT

    def __init__(self, lo: Union[bytes, memoryview, bytearray, int, float], la: Union[int, float, None] = None) -> None:
        """Координаты.
        
        Долгота (Lng) E/W - x - lo
        Широта (Lat) N/S - y - la
        """
        # ОПТИМИЗАЦИЯ: type() is быстрее isinstance() для простых типов
        # Сценарий A: На входе сырые байты (любой объект с поддержкой buffer protocol)
        if type(lo) is bytes:
            super().__init__(lo)
            self._hlon, self._hlat = struct_2UINT.unpack_from(self._raw, 0)
            self._do_calculate_lon_lat()
            return
        if type(lo) is memoryview or type(lo) is bytearray:
            super().__init__(bytes(lo[:DOUBLE_BYTES_CNT]))
            self._hlon, self._hlat = struct_2UINT.unpack_from(self._raw, 0)
            self._do_calculate_lon_lat()
            return
        # if type(lo) is bytearray:
        #     super().__init__(bytes(lo[:DOUBLE_BYTES_CNT]))
        #     self._hlon, self._hlat = struct_2UINT.unpack_from(self._raw, 0)
        #     self._do_calculate_lon_lat()
        #     return

        # Сценарий B: На входе два целых числа (hlon, hlat) — самый частый вызов из block_0x06/0x09
        if type(lo) is int and type(la) is int:
            self._hlon = lo & 0xFFFFFFFF
            self._hlat = la & 0xFFFFFFFF
            
            # ОПТИМИЗАЦИЯ: пропускаем super().__init__() — _raw не нужен,
            # если координаты создаются из int и используются только для lon/lat.
            # Placeholder для совместимости с __slots__ BYTESTRUCT.
            self._raw = memoryview(b'')
            self._do_calculate_lon_lat()
            return

        # Сценарий C: На входе две координаты float (в градусах)
        if type(lo) is float and type(la) is float:
            self._hlon = int((30 + lo) * MULCOORD) & 0xFFFFFFFF
            self._hlat = int(la * MULCOORD) & 0xFFFFFFFF
            
            super().__init__(struct_2UINT.pack(self._hlon, self._hlat))
            self._do_calculate_lon_lat()
            return

        raise ValueError(f"Неверные типы аргументов для COORD: lo={type(lo)}, la={type(la)}")

    @property
    def _hlongitude(self) -> int:
        """Получение знакового (signed) int из беззнакового _hlon. Опечатка 'g' исправлена."""
        return self._hlon - 0x100000000 if self._hlon & MOST_SIGNIFICANT_BIT else self._hlon

    @property
    def _hlatitude(self) -> int:
        """Получение знакового (signed) int из беззнакового _hlat."""
        return self._hlat - 0x100000000 if self._hlat & MOST_SIGNIFICANT_BIT else self._hlat

    @property
    def lon(self) -> float:
        """Longitude, x, w|e"""
        return self._precalculated_lon

    @property
    def lat(self) -> float:
        """Latitude, y, n/s"""
        return self._precalculated_lat

    def _do_calculate_lon_lat(self):
        """Предрасчет при инициализации lon, lat для кеширования. Исправлена опечатка в имени слота."""
        self._precalculated_lon = (self._hlongitude / MULCOORD) - 30
        self._precalculated_lat = self._hlatitude / MULCOORD

    def as_tuple(self) -> tuple[float, float]:
        """Быстрый экспорт в формате (lon, lat) для QgsPointXY."""
        return (self._precalculated_lon, self._precalculated_lat)

    def __repr__(self) -> str:
        lat_val = self._precalculated_lat
        lon_val = self._precalculated_lon
        ch_lat = 'N' if lat_val >= 0 else 'S'
        ch_lon = 'E' if lon_val >= 0 else 'W'
        return f"{abs(lat_val):02.6f}{ch_lat} {abs(lon_val):02.6f}{ch_lon}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, COORD):
            return NotImplemented
        return self._hlat == other._hlat and self._hlon == other._hlon

    def delta(self, other: object) -> str:
        if not isinstance(other, COORD):
            return NotImplemented
        return f"lat:{self._precalculated_lat - other._precalculated_lat:.2f}° x lon:{self._precalculated_lon - other._precalculated_lon:.2f}°"  # noqa

    # COORD


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

    # MAP_AREA


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

    # GEO_CATEGORY


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
        'cat',
        'vrtx',
        'block'
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
        self.vrtx = []

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
        'c_p_line_sign',    # 'POI_regi',
        'c_b_or_c',         # 'or_b_or_c',
        'c_pp_str_name',    # 'tstr_name',
        'c_38_or_0b_country',    # 'or_38_or_0_b_country',
        'cnt_vrtx',
        'name',
        'name2',
        'cat',
        'vrtx',
        'block'
        
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
         c_p_line_sign,
         c_b_or_c,
         c_pp_str_name,
         c_38_or_0b_country,
         next_ptr_vrtx) = GEO_LINE_struct.unpack_from(mem_buf, 0)
         
        # Передаем базовому классу первые 16 байт (size)
        super().__init__(mem_buf[:self.size])
        
        self.p_str_name = p_str_name           # begin zero-ended string
        self.ptr_vrtx = ptr_vrtx               # begin vertexes
        self.id = id
        self.c_p_line_sign = c_p_line_sign               # ptstr - but strange, unkn
        self.c_b_or_c = c_b_or_c             # estimated length or travel time
        self.c_pp_str_name = c_pp_str_name             # ptr to GEO_OBJ_STR
        self.c_38_or_0b_country = c_38_or_0b_country
        self.cnt_vrtx = int((next_ptr_vrtx - ptr_vrtx) / VRTX_OBJ_SIZE)
        self.name = "Proto line. Need read from parent"
        self.name2 = ""
        self.cat = category
        self.vrtx = []

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


class POI_ITEM(BYTESTRUCT):
    """
    in block_0x06
    (c) fdemusso
    off  size  field
    0x00   4   BLOCK_ID of the 0x10 block (POI parcel, §8.1.1) holding this POI's details
    0x04   2   byte offset, within that 0x10 block, of this POI's S0 index record (§8.1.1)
    0x06   2   LOCAL_X    position in tile, step 64        <- sorted ascending
    0x08   2   LOCAL_Y    position in tile, step 64
    0x0A   2   CATEGORY   (12 petrol, 21 hotels, 37 landmarks, 48 towns, …; 01-architecture.md §4.4.1)
    0x0C   2   BRAND      offset of the POI's brand in this block's name blob, 0 = no brand
    0x0E   2   0, or 1 on a few ports and airports (187 records on CD-ID 2952, 240 on CD-ID 21594)
    0x10   4   POI_ID     the 0x10 detail record's +0x1C (§8.1.1); read before as a "brand reference"
    0x14   8   0          DB-REL 34 only: the 20-byte form (DB-REL 22) ends at 0x14
    """
    __slots__ = (
        '_bladr10', '_ptr10', '_LOCAL_X', '_LOCAL_Y', '_cat',
        '_p_brand', 'is_custom', 'id',
        'brand', 'coord', 'poi',
    )

    size: int = 0x1c

    def __init__(self, buffer: ReadableBuffer):      # TODO: может parent_block, а не vdo?
        super().__init__(buffer)
        # 0x0E   2   0, or 1 on a few ports and airports - closed regular use flag?
        (bladdr10, self._ptr10, self._LOCAL_X, self._LOCAL_Y,
            en_cat, self._p_brand, self.is_custom,
            self.id, zero1, zero2) = POI_ITEM_struct.unpack_from(self._raw, 0)
        self._cat = en_POI_CAT(en_cat)
        # _base10 - bladdr. рассчитать абсолютный адрес начала блока 0x10
        self._bladr10 = bladdr10  # (bladdr10 >> 8) * vdo.segsize
        self.brand = ''
        if zero1 or zero2:
            raise NotImplementedError(f"z1: {zero1}, z2: {zero2}")
        self.coord = None
        self.poi = None

    def __repr__(self):
        s = f"{self.cat}: {self.brand}"
        return s

    @property
    def cat(self) -> str:
        return self._cat.name

# POI_ITEM

    
class POI_CATEGORY(BYTESTRUCT):
    """
    POI_CATEGORY 3*DWORD
    0     QWORD   POIs  FAR_LIST
    8     WORD    en_POI_CATEGORY - enum тип, категория POI
    10    WORD    reference_addr_start  В 0x0a - УКАЗЫВАЕТ НА НАЧАЛО СТРОКОВЫХ ДАННЫХ '''
    """
    
    # Жестко резервируем память под все атрибуты экземпляра. __dict__ удален.
    __slots__ = ('fl_POIs', 'poi_type', 'p_str', 'name')
    
    size: int = 12  # 3*DWORD = 12 байт

    def __init__(self, buffer: ReadableBuffer, parent_vdo: VDO_FILE) -> None:
        mem_buf = memoryview(buffer)
        
        # Передаем буфер в родительский BYTESTRUCT (срез до 12 байт через self.size)
        super().__init__(mem_buf[:self.size])
        
        # Оптимизация: берем zero-copy срез напрямую из сохраненного self._raw
        self.fl_POIs = FAR_LIST(self._raw[0:FAR_LIST.size], parent_vdo)
        
        # Извлекаем тип категории (unsigned short по смещению 8)
        self.poi_type = en_POI_CAT(self.ushort(8))
        
        # Извлекаем указатель на строковые данные (unsigned short по смещению 10)
        self.p_str = self.ushort(10)
        
        # Инициализируем имя по умолчанию
        self.name = "Proto. Name set where called"

    def __repr__(self) -> str:
        ''' View while debug value '''
        return f"{self.poi_type.name} [{self.fl_POIs.hex}] -> 0x{self.p_str:04X}: {self.name}"

    def __str__(self) -> str:
        return self.__repr__()

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


class POI_BRIF(BYTESTRUCT):
    """
    from block_0x10
    (c) fdemusso
    0x00   2   NAME_PTR
        ~0x02   2   TYPE          (2 in 94% of records on DB-REL 22, >99% on DB-REL 34)~
    0x02 - is 2 bytes: is_alias flag (0/1) and en_CARINET_LANGUAGE.value
    0x04   2   LOCALITY_PTR  or 0; shown after the post-town initial ("S.-LOCALITY")
    0x06   2   DETAIL_PTR    byte offset of an S1 record
    """
    __slots__ = ('_ptr_name', 'alias', 'en_Lang', '_ptr_locality',
                 '_ptr_more', 'name' , 'locality')

    size: int = 8

    def __init__(self, buffer: ReadableBuffer):
        super().__init__(buffer)
        (self._ptr_name, alias, en_Lang,
         self._ptr_locality, self._ptr_more) = struct_POI_BRIF.unpack_from(self._raw, 0)  # (">HBBHH
        self.en_Lang = en_CARINET_LANGUAGE(en_Lang)
        # TYPE field: 0=main name, 1=alias, 2=common (94% DB-REL 22, >99% DB-REL 34)
        # if alias in (0, 2):
        if alias in [0, 1, 2]:
            self.alias = alias
        else:
            raise NotImplementedError(f"Byte alias: {alias} is neither zero, not 1. \
                                      {struct_POI_BRIF.unpack_from(self._raw, 0)}")
        self.name = ''
        self.locality = ''  # Read city.." if self._ptr_city else ""
        
    def __repr__(self):
        a = f' (alias: {self.alias})' if self.alias else ''
        s = f" [{self.locality}]" if self._ptr_locality else ''
        b = f"{self.name}{a}{s}: {self.en_Lang.name}"
        return b
# POI_BRIF
    
# ===============================================


class POI_DETAILS(BYTESTRUCT):
    """
    from block_0x10
    (c) fdemusso
    S1 — `n1` detail records, 40 bytes (`T[0x2f]`; the other candidate, `T[0x51]`, is 28
    on DB-REL 22):

    ```LHHHHHLHLHHL
    off  size  field
    0x00   4   X             absolute, same frame as §7
    0x04   4   Y
    0x08   2   LINK_PTR      byte offset of an S4 road link (the record's own in 77,711 / 92,774)
    0x0A   2   1             (92,305 / 92,774 on CD-ID 2952)
    0x0C   2   BRAND_PTR     or 0
    0x0E   2   STREET_PTR
    0x10   2   CITY_PTR
    0x12   2   ~COUNTY_PTR~  ppl: region
    0x14   2   COUNTRY_PTR   (`england`, `scotland`, `wales`, `france`, …)
    0x16   4   0             (92,308 / 92,774) ppl: not seems as zero
    0x1A   2   HOUSE_NO_PTR
    0x1C   4   POI_ID        u16 prefix (0x0113, 0x0114, 0x0115, … on CD-ID 2952) + u16 serial;
                            the same in every copy of the POI and in its 0x06 records
    0x20   2   PHONE_PTR
    0x22   2   POSTCODE_PTR  (outward code + first inward digit, e.g. "sw7 2"; 0 on DB-REL 22)
    0x24   4   0             (all)
    """
    __slots__ = ('coord', 'li_road', '_ps_brand', '_ps_street', '_ps_city', '_ps_region', '_ps_country', '_ps_street',
                 'zero1', '_ps_house', 'id', '_ps_phone', '_ps_postcode')
    #  'brand', 'id', 'postcode', 'phone', 'houseno', 'country', 'region', 'city', 'street')

    size: int = 0x28

    def __init__(self, buffer: ReadableBuffer):
        super().__init__(buffer)
        self.coord = COORD(self.read(0, COORD.size))
        (road_ptr, road_cnt, self._ps_brand, self._ps_street, self._ps_city,
            self._ps_region, self._ps_country, self.zero1, zero2, self._ps_house,
            self.id, self._ps_phone, self._ps_postcode,
            zero3) = struct_POI_DETAILS.unpack_from(self._raw, 8)  # ">LHHHHHHHHLHHL"

        if (self.zero1 and self.zero1 != 1) or zero2 or zero3:
            raise NotImplementedError(f"POI_DETAILS z1: {self.zero1}, z2: {zero2}, z3: {zero3}")
        self.li_road = LIST(struct_LIST.pack(road_ptr, road_cnt))
        # zero=1 = aeroport twente, closed from 2008
        
# POI_DETAILS


class POI(POI_BRIF):
    """
    block 0x10 - extended
    """
    __slots__ = ('brand', 'id', 'raw_road', 'coord',
                 'postcode', 'phone', 'houseno', 'country', 'region', 'city', 'street')

    def __init__(self, mem_buff):
        super().__init__(mem_buff)
        self.brand = ''
        self.postcode = ''
        self.phone = ''
        self.houseno = ''
        self.country = ''
        self.region = ''
        self.city = ''
        self.street = ''
        self.id = 0
        self.coord = None
        self.raw_road = None


# -------------------------------------------------------------------------
# functions
# -------------------------------------------------------------------------

# def read_far_poi(vdo: VDO_FILE, int_bladdr: int, brif_offset: int) -> POI:
#     """
#     для чтения POI извне блока 0x10
#     """
#     # загружаем весь блок - т.к. множественное чтение лучше делать из памяти и некоторые функции уж реализованы
#     raw_block = BYTESTRUCT(vdo.read((int_bladdr >> 8) * vdo.segsize, (int_bladdr & 0xFF) * vdo.segsize))
#     # вычисляем offset
#     poi = POI(raw_block.read(brif_offset, POI_BRIF.size))
#     if poi._ptr_name:
#         poi.name = raw_block.read_str(poi._ptr_name)
#     if poi._ptr_locality:
#         poi.locality = raw_block.read_str(poi._ptr_locality)
#     if poi._ptr_more:
#         # если есть ссылка на детальную информацию
#         det: POI_DETAILS = POI_DETAILS(raw_block.read(poi._ptr_more, POI_DETAILS.size))

#         if det._ps_brand:
#             poi.brand = raw_block.read_str(det._ps_brand)
#         if det._ps_postcode:
#             poi.postcode = raw_block.read_str(det._ps_postcode)
#         if det._ps_phone:
#             poi.phone = raw_block.read_str(det._ps_phone)
#         if det._ps_house:
#             poi.houseno = raw_block.read_str(det._ps_house)
#         if det._ps_country:
#             poi.country = raw_block.read_str(det._ps_country)
#         if det._ps_region:
#             poi.region = raw_block.read_str(det._ps_region)
#         if det._ps_city:
#             poi.city = raw_block.read_str(det._ps_city)
#         if det._ps_street:
#             poi.street = raw_block.read_str(det._ps_street)
#         poi.coord = det.coord
#         poi.id = det.id

#         #
#         if det.li_road:
#             # bladdr short short
#             poi.raw_road = BYTESTRUCT(raw_block.read(det.li_road.ptr, det.li_road.cnt * 8))

#         return poi
    
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
