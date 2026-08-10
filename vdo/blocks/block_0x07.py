"""
0x07  SCALES

Набор масштабов, начальный для определения по координатам
и масштабу текущего отображения блока с геосодержимым.

Перечень типов POI.

Список стран на картах.*

Территориальное деление стран.*

* - only dbrev.34

block_0x07
SCALE

"""
from __future__ import annotations  # Обязательно на самой первой строчке файла

from typing import TYPE_CHECKING, Union, Optional, Tuple, Iterator


if TYPE_CHECKING:
    # Этот блок видит только Pylance, интерпретатор Python его игнорирует
    from _typeshed import ReadableBuffer        # pragma: no cover
else:
    # Запасной вариант для рантайма, чтобы не было NameError
    ReadableBuffer = bytes

# from QGIS_VDO.vdo.consts import struct_WORD  # struct_UINT
from QGIS_VDO.vdo.enums import en_POI_CAT, en_TeleAtlasRegion
from QGIS_VDO.vdo.block_base import block_base
from QGIS_VDO.vdo.datatypes import BYTESTRUCT, BLADDR, VDO_FILE, LIST
from QGIS_VDO.vdo.geotypes import COORD
from QGIS_VDO.vdo.blocks import block_0x08

OFFSET_LI_POI = 0x08
OFFSET_LI_TERR_DIVISIONS = 0x0C
OFFSET_LI_COUNTRY_LIST = 0x10
SCALES_COUNT = 12


class SCALE(BYTESTRUCT):
    """
    0   UINT    BLADDR almanac_idx
    4   QWORD   COORD left bottom
    12  QWORD   COORD right top
    20  WORD    value_a - unknown, [6, 0, 1, 2, 65535*]
    22  WORD    zoom_from, [0, 1, 320, 40, 120, 1200, 3000]
    24* WORD    zoom_to, [0, 1, 3000, 1200, 120, 40, 65535]
    * - only dbrev.34
    """

    # 1. Жестко фиксируем слоты. vdo и size теперь легитимно живут в памяти структуры
    __slots__ = ("vdo", "size")

    def __init__(self, buffer: Union[bytes, bytearray, memoryview], vdo: "VDO_FILE") -> None:
        # Определяем размер структуры на основе версии dbrev
        if vdo.dbrev == 34:
            structure_size = 0x1C
        elif vdo.dbrev == 30:
            structure_size = 0x18
        else:
            raise ValueError(f"dbrev must be 30 or 34, got {vdo.dbrev}")

        # too small buffer
        if len(buffer) < structure_size:
            raise ValueError(f"Len buffer {buffer}: {len(buffer)}, but must be {structure_size}")

        # 2. Передаем размер в родительский класс, чтобы self._raw был строго нужной длины
        super().__init__(buffer, size=structure_size)
        
        self.size = structure_size
        self.vdo = vdo

    def __repr__(self) -> str:
        # Используем ленивые свойства, чтобы дамп не падал
        return f"{self.d_delta} {self.zoom_from}-{self.zoom_to} {self.value_a} [0x{self.square_side:X}]"

    # --- Координаты и Зоны (Zero-Copy) ---

    @property
    def area(self) -> Tuple["COORD", "COORD"]:
        """Возвращает лениво инициализированные объекты координат (пара left-bottom, right-top)."""
        # Используем self.read() для передачи zero-copy memoryview срезов
        point_lb = COORD(self.read(4, 8))
        point_rt = COORD(self.read(12, 8))
        return point_lb, point_rt

    @property
    def square_side(self) -> int:
        """Ленивый расчет стороны квадрата (вычисляется только при вызове)."""
        lb, rt = self.area
        return rt._hlat - lb._hlat

    @property
    def d_delta(self) -> str:
        """Ленивый расчет дельты."""
        lb, rt = self.area
        return rt.delta(lb)

    # --- Свойства полей структуры ---

    @property
    def almanac_idx(self) -> Optional["BLADDR"]:
        """bladdr block_0x08 - альманаха."""
        # Передаем первые 4 байта как memoryview без копирования
        return BLADDR(self.read(0, 4), self.vdo)
        
    @property
    def value_a(self) -> int:
        """20  WORD    value_a - unknown, [6, 0, 1, 2, 65535*]"""
        return self.ushort(20)

    @property
    def zoom_from(self) -> int:
        """22  WORD    zoom_from, [0, 1, 320, 40, 120, 1200, 3000]"""
        return self.ushort(22)

    @property
    def zoom_to(self) -> int:
        """
        24* WORD    zoom_to, [0, 1, 3000, 1200, 120, 40, 65535]
        if vdo.dbrev == 34: else 0
        """
        if self.vdo.dbrev == 34:
            return self.ushort(24)
        return 0
        
    @property
    def is_empty(self) -> bool:
        """Валидный или пустой блок (проверка по нулевым координатам area)."""
        # Сравниваем memoryview с bytes напрямую — это быстро и эффективно на уровне Си
        # return self._raw[:4] == b'\x00' * 4     # а вот херь: у бмв есть 0x04dffa01, но пустой area # noqa
        return self._raw[4:20] == b'\x00' * 16

    # --- Бизнес-логика ---

    def find_by_coord(self, srch_point: "COORD") -> Optional["BLADDR"]:
        """Поиск idx блока, в который попадают координаты, или None."""
        if not self.almanac_idx:
            return None
        
        lb, rt = self.area
        
        # Проверка границ (границы теперь берутся из ленивого свойства area)
        if (srch_point.lat < lb.lat or srch_point.lat >= rt.lat
                or srch_point.lon < lb.lon or srch_point.lon >= rt.lon):
            # print(f"No way: {srch_point} not in ({lb}, {rt})")
            return None
            
        # Запрашиваем блок через vdo
        alm: "block_0x08" = self.vdo.get_block(self.almanac_idx, lb, rt)
        return alm.find_by_coord(srch_point)


class TERR_DIV(BYTESTRUCT):
    """
    size = 20
    0	+BLADDR block_0x18
    4	WORD	unkn_4
    6	WORD	unkn_6_mb_cnt
    8	PSTR 	local country name
    10	byte	const_01
    11  byte	const_00_or_01
    12  WORD 	en_country
    14	WORD 	align = 0
    16  LIST 	NUTS (Nomenclature of Territorial Units for Statistics)
    """

    # Обязательно проверяем, что в BYTESTRUCT тоже объявлены __slots__
    __slots__ = ('name_local', 'vdo', '_li_NUTS_cache')

    size = 20

    def __init__(self, buffer: Union[bytes, bytearray, memoryview], block: 'block_0x07') -> None:
        super().__init__(buffer, size=self.size)

        self.vdo = block.vdo
        
        # Безопасное приведение первой буквы к заглавной без порчи остального регистра
        raw_name = block.read_str(self.ptr_name_local())
        self.name_local = raw_name[0].upper() + raw_name[1:] if raw_name else ""
        
        # Кэшируем объект LIST сразу, чтобы не пересоздавать его при каждом вызове свойства
        self._li_NUTS_cache = LIST(self.read(16, LIST.size))

    def __repr__(self) -> str:
        return f"{self.name_local} {self.en_country.name}:{self.en_country.value:X}h "
    
    @property
    def bladdr(self) -> Optional[BLADDR]:
        """Block 0x18 type / 0 +BLADDR block_0x18"""
        return BLADDR(self.read(0, 4), self.vdo)

    @property
    def unkn_4(self) -> int:
        """4 WORD unkn_4"""
        return self.ushort(4)

    @property
    def unkn_6_mb_cnt(self) -> int:
        """6 WORD unkn_6_mb_cnt"""
        return self.ushort(6)

    def ptr_name_local(self) -> int:
        """8 PSTR local country name"""
        return self.ushort(8)

    @property
    def const_01(self) -> int:
        """10 byte const_01"""
        return self.uchar(10)

    @property
    def const_00_or_01(self) -> int:
        """11 byte const_00_or_01"""
        return self.uchar(11)  # ИСПРАВЛЕНО: смещение изменено с 10 на 11

    @property
    def en_country(self) -> en_TeleAtlasRegion:
        """12 WORD en_country"""
        v = self.ushort(12)
        return en_TeleAtlasRegion(v)
    
    # 14 WORD align = 0

    @property
    def li_NUTS(self) -> LIST:
        """16 LIST NUTS (Nomenclature of Territorial Units for Statistics)"""
        return self._li_NUTS_cache  # ОПТИМИЗИРОВАНО: возврат закэшированного значения

    
# ---------------

class block_0x07(block_base):
    """ SCALES =  type 0x07   """

    __slots__ = ('vdo', 'scales', '_li_countries', '_li_POI_cat', '_li_country_divisions')

    def __init__(self, bl_addr: BLADDR) -> None:
        super().__init__(bl_addr)

        self.vdo = bl_addr.vdo

        # <<< SCALES
        # у старой и новой версии разный отступ списка масштабов
        if self.vdo.dbrev == 34:
            OFFSET_SCALES = 0x14
            SIZE_SCALE = 0x1C
            self._li_countries = self.read_list(OFFSET_LI_COUNTRY_LIST)
        elif self.vdo.dbrev == 30:    # 30
            OFFSET_SCALES = 0x10
            SIZE_SCALE = 0x18
            self._li_countries = None
        else:
            raise ValueError(f"dbrev: {self.vdo.dbrev} must be in [30, 34]")

        self._li_POI_cat = self.read_list(OFFSET_LI_POI)
        self._li_country_divisions = self.read_list(OFFSET_LI_TERR_DIVISIONS)

        # scales array
        self.scales: list[SCALE] = []
        for s_offset in range(OFFSET_SCALES, OFFSET_SCALES + SIZE_SCALE * 12, SIZE_SCALE):  # 12 - qty scales  # noqa
            b = self.read(s_offset, SIZE_SCALE)
            scale = SCALE(b, self.vdo)
            self.scales.append(scale)

    @property
    def li_POI_cat(self) -> LIST:
        """ LIST to table of POI categories"""
        return self._li_POI_cat

    # # <<< TERR_DIVISIONS
    @property
    def li_country_divisions(self) -> LIST:
        """ LIST to table of TERR_DIVISIONS """
        return self._li_country_divisions

    @property
    def li_countries(self) -> Optional[LIST]:
        """ LIST countries information"""
        return self._li_countries

    def find_by_coord(self, point: COORD, idScale: int) -> BLADDR | None:
        """
        Args:
            point: COORD - searched
            idScale: int - номер SCALE - num scale
        Returns:
            bladdr_map: BLADDR
        """
        # проверка на существование масштаба
        if idScale < 0 or idScale >= SCALES_COUNT:
            return None
        
        sc: SCALE = self.scales[idScale]
        if sc.is_empty:
            return None
        
        # res = sc.find_by_coord(point)
        return sc.find_by_coord(point)

    def get_pois(self) -> Iterator[en_POI_CAT]:
        """ Iterator POI categories

        poi struct:
        0   WORD   en_POI_CAT
        4   WORD    ptr2zero byte   -> unuse
        8   WORD    align const 0   -> unuse
        """
        # Список категорий точек интереса self.li_POI_cat
        step_POI_SIZE = 6
        poi_list = self._li_POI_cat    # Локальная переменная для оптимизации
        offset_start = poi_list.ptr
        offset_end = offset_start + poi_list.cnt * step_POI_SIZE

        for offset in range(offset_start, offset_end, step_POI_SIZE):
            # poi_code = self.ushort(offset)
            # Возвращаем напрямую без перехвата исключений, как и требовалось
            # en_poi = en_POI_CAT(poi_code)
            # try:
            #     en_poi = en_POI_CAT(poi_code)
            # except ValueError:
            #     en_poi = en_POI_CAT(0xFF)  # - UNCNOWN category
            #     # Сообщение - неизвестная категория ПОИ.
            #     print(f"Неизвестный код POI: 0x{poi_code:0X}")
            yield en_POI_CAT(self.ushort(offset))

    def get_terr_div_countries(self) -> Iterator[TERR_DIV]:
        """ Iterator territory divisions of coutryes
        terr div struct:
        0	BLADDR block_0x18
        4	WORD	unkn
        6	WORD	mb_cnt
        8	PSTR 	local country name
        10	byte	always_01
        11  byte	_00_or_01
        12  WORD 	en_country
        14	WORD 	align = 0
        16  LIST 	NUTS (Nomenclature of Territorial Units for Statistics) — единый стандарт
            кодирования административного деления стран в ЕС и Европе для статистических целей
        """
        step = TERR_DIV.size    # 20
        div_list = self._li_country_divisions    # Избегаем повторного вызова read_list
        offset_start = div_list.ptr
        offset_end = offset_start + div_list.cnt * step

        for offset in range(offset_start, offset_end, step):
            # terr_div = TERR_DIV(self.read(offset, step), self)
            yield TERR_DIV(self.read(offset, step), self)


# -------------------------------------------------------------------------

if __name__ == '__main__':
    # from vdo.datatypes import VDO_FILE
    from QGIS_VDO.vdo.fixtures_vdo import vdo30, vdo34ee, vdobmv, vdo34bnl, vdoRu  # noqa
    from QGIS_VDO.vdo.consts import struct_UINT        # noqa

    # block(0x55D7201);   // EE scale 7 0x16 arch=0 near SPb
    # block(0x55D6903);   // EE scale 7 0x16 arch=1 near SPb

    vdo = vdo30
    # vdo = vdo34ee
    # vdo = vdobmv
    # vdo = vdo34bnl
    vdo = vdoRu

    # test get_items ---------------------------------------------------------------------
    # from QGIS_VDO.vdo.blocks import block_0x12, block_0x09
    # bl_toc: block_0x12 = vdo.get_block(0)
    # bl_scales: BLADDR = bl_toc.bladdr_scales

    # block_07: block_0x07 = vdo.get_block(bl_scales)

    # scale_5 = block_07.scales[5]
    # scale_5 = block_07.scales[11]
    # block_almanac: block_0x08 = vdo.get_block(scale_5.almanac_idx, scale_5.area[0], scale_5.area[1])  # noqa

    # # block_08 content
    # print(f"block_08: 0x{block_almanac} block_0x09 : x : y")
    # bla_first = None
    # for f in block_almanac.get_items():
    #     if not bla_first:
    #         (bla_first, coord_lb, coord_rt) = f

    #     print(f)
    #     pass

    # # block_09 content
    # print("block_09: geo_block_0xXX : x : y")
    # bla = BLADDR(struct_UINT.pack(bla_first), vdo)
    # bl_folder: block_0x09 = vdo.get_block(bla, coord_lb, coord_rt)

    # print(f"block_08: block_0x09: 0x{bl_folder.head.bladdr.hex.replace(' ', '')} COORD(lb) : COORD(rt)")  # noqa
    # bla_first = None
    # cnt = bl_folder.items_cnt()

    # for f in bl_folder.get_items():
    #     if not bla_first:
    #         (bla_first, coord_lb, coord_rt) = f
    #     print(f)
    #     pass

    # geoblock content

    pass

    # test search find_by_coord ===============================================================
    vdo = vdo34bnl

    bladdr_scales: BLADDR = vdo.get_block(0).bladdr_scales
    print(type(bladdr_scales))
    block_07: block_0x07 = vdo.get_block(bladdr_scales)
    print(type(block_07))
    print(type(block_0x07))

    pois = [f for f in block_07.get_pois()]
    terd = [k for k in block_07.get_terr_div_countries()]

    sc: SCALE = block_07.scales[1]
    # b'\x13\xc7\xb9\x02\x13\xddiu'  59.989966N 29.734109E
    srch = COORD(b'\x13\xc7\xb9\x02\x13\xddiu')
    bladdr_map = sc.find_by_coord(srch)

    bl_map = vdo.get_block(bladdr_map)

    bladdr_map = block_07.find_by_coord(srch, 8)
    bl_map = vdo.get_block(bladdr_map)

    # bl_ru_big_map = vdo.get_block(BLADDR(struct_UINT.pack(0x)))
    # @ 00000201 13 0202 [13:BIBLIOGR]
    pass
