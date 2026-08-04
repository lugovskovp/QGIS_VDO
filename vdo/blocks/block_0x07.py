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

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    # Этот блок видит только Pylance, интерпретатор Python его игнорирует
    from _typeshed import ReadableBuffer
else:
    # Запасной вариант для рантайма, чтобы не было NameError
    ReadableBuffer = bytes

# from QGIS_VDO.vdo.consts import struct_WORD  # struct_UINT
from QGIS_VDO.vdo.enums import en_POI_CAT
from QGIS_VDO.vdo.block_base import block_base
from QGIS_VDO.vdo.datatypes import BYTESTRUCT, BLADDR, OFFSET_TOC, VDO_FILE   # LIST,
from QGIS_VDO.vdo.geotypes import COORD
from QGIS_VDO.vdo.blocks import block_0x08


OFFSET_TERR_DIVISIONS = 0x0C
OFFSET_COUNTRY_LIST = 0x10
SCALES_COUNT = 12


# class GEO_INDEX(BYTESTRUCT):
#     """
#     """
#     def __init__(self, byte_array: bytes) -> None:

#         pass


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
    def __init__(self, byte_array: ReadableBuffer, vdo: VDO_FILE) -> None:
        if vdo.dbrev == 34:
            self.size = 0x1C
        elif vdo.dbrev == 30:
            self.size = 0x18
        else:
            raise ValueError(vdo.dbrev, " dbrev must be 30 or 34")

        super().__init__(byte_array)
        self.vdo = vdo

        # area
        point_lb = COORD(bytearray(self._raw[4:12]))
        point_rt = COORD(self._raw[12:20])
        self.area = (point_lb, point_rt)

        # @properties:
        # 0   UINT    BLADDR almanac_idx
        # 20  WORD    value_a - unknown, [6, 0, 1, 2, 65535*]
        # 22  WORD    zoom_from, [0, 1, 320, 40, 120, 1200, 3000]
        # 24* WORD    zoom_to, [0, 1, 3000, 1200, 120, 40, 65535]

        # TODO а оно надо?
        self.square_side = (self.area[1]._hlat - self.area[0]._hlat)
        self.d_delta = self.area[1].delta(self.area[0])

        return
        # Список folders с areas покрытия
        self.folders = {}  # dict areas, key - block_0x09, val - area

        alm: block_0x08 = vdo.get_block(self.almanac_idx)
        from_x = point_lb._hlon
        to_x = point_rt._hlon
        from_y = point_lb._hlat
        # to_y = point_rt._hlat
        x = from_x
        y = from_y
        i = 0
        j = 0
        for offset in range(alm.li_folders.ptr,
                            alm.li_folders.ptr + BLADDR.size * alm.li_folders.cnt,
                            BLADDR.size):
            ffolder = alm.bladdr(offset)    # следующий folder
            # lb rt area
            if x + alm.side > to_x:
                i = 0
                j += 1
                x = from_x
                y += alm.side
                # y и не проверяем
            # Вот тут бы проверить - узкий-высокий...
            lb = (x, y)
            rt = (x + alm.side, y + alm.side)
            i += 1
            x += alm.side
            if not ffolder.isZero:
                self.folders[f"{ffolder}"] = (ffolder, lb, rt, i, j)
                pass
            pass
        # -171088640 x  0x-a329b00
        # 43008 y 0xa800
        # 30.795958S 29.992259W lat-lon
        # '00 00 A8 00 F5 CD 65 00  '
        pass

    def __repr__(self):
        res = f"{self.area[1].delta(self.area[0])}"
        res += f" {self.zoom_from}-{self.zoom_to} {self.value_a}"
        res += f" [0x{self.square_side:X}]"
        return res

    @property
    def almanac_idx(self) -> BLADDR | None:
        """
        bladdr block_0x08 - альманаха
        """
        return BLADDR(self._raw[:4], self.vdo)
        
    @property
    def value_a(self) -> int:
        """
        20  WORD    value_a - unknown, [6, 0, 1, 2, 65535*]
        """
        return self.ushort(20)

    @property
    def zoom_from(self) -> int:
        """
        22  WORD    zoom_from, [0, 1, 320, 40, 120, 1200, 3000]
        """
        return self.ushort(22)

    @property
    def zoom_to(self) -> int:
        """
        24* WORD    zoom_to, [0, 1, 3000, 1200, 120, 40, 65535]
        if vdo.dbrev == 34: else 0
        """
        if self.vdo.dbrev == 34:
            return self.ushort(24)
        else:
            return 0
        
    @property
    def isEmpty(self) -> bool:
        """ Валидный или пустой"""
        # если almanac_idx == 0, то scale пустой
        # return self.almanac_idx.isZero
        # return self._raw[:4] == b'\x00' * 4     # а вот херь: у бмв есть 0x04dffa01, но пустой area # noqa
        return self._raw[4:20] == b'\x00' * 16

    def find_by_coord(self, srch_point: COORD) -> BLADDR | None:
        """
        Поиск idx блока, в который попадают координаты, или None
        """
        # check borders
        if srch_point.lat < self.area[0].lat or srch_point.lat > self.area[1].lat \
           or srch_point.lon < self.area[0].lon or srch_point.lon > self.area[1].lon:
            # не попал в квадрат lb-rt scale
            print(f"No way: {srch_point} not in {self.area}")
            return None
        # 0x08
        if not self.almanac_idx:
            return None
        alm: block_0x08 = self.vdo.get_block(self.almanac_idx, self.area[0], self.area[1])
        res = alm.find_by_coord(srch_point)     # bladdr geoblock
        return res


class block_0x07(block_base):
    """ SCALES =  type 0x07   """

    def __init__(self, bl_addr: BLADDR) -> None:
        super().__init__(bl_addr)
        # <<< SCALES
        # у старой и новой версии разный отступ списка масштабов
        if bl_addr.vdo.dbrev == 34:
            OFFSET_SCALES = 0x14
            SIZE_SCALE = 0x1C
            self.li_countries = self.read_list(OFFSET_COUNTRY_LIST)
        else:       # 30
            OFFSET_SCALES = 0x10
            SIZE_SCALE = 0x18
            self.li_countries = None
        self.scales = []
        for s_offset in range(OFFSET_SCALES, OFFSET_SCALES + SIZE_SCALE * 12, SIZE_SCALE):  # noqa
            b = self.read(s_offset, SIZE_SCALE)
            scale = SCALE(b, bl_addr.vdo)
            self.scales.append(scale)
        pass

        # <<< TERR_DIVISIONS
        self.li_country_divisions = self.read_list(OFFSET_TERR_DIVISIONS)

        # <<< POIs self.li_POI_cat = self.li_toc
        """
        0   WORD   en_POI_CAT
        4   WORD    ptr2zero byte
        8   WORD    align const 0
        """
        # Список категорий точек интереса self.li_toc
        self.pois = []
        POI_SIZE = 6
        for offset in range(self.li_toc.ptr,
                            self.li_toc.ptr + POI_SIZE * self.li_toc.cnt,
                            POI_SIZE):
            poi_code = self.ushort(offset)
            #
            en_poi = en_POI_CAT(poi_code)
            # try:
            #     en_poi = en_POI_CAT(poi_code)
            # except ValueError:
            #     en_poi = en_POI_CAT(0xFF)  # - UNCNOWN category
            #     # Сообщение - неизвестная категория ПОИ.
            #     print(f"Неизвестный код POI: 0x{poi_code:0X}")
            self.pois.append(en_poi)
        pass

    @property
    def li_toc(self):
        """ LIST to table of contents """
        return self.read_list(OFFSET_TOC)

    def find_by_coord(self, point: COORD, idScale: int) -> BLADDR | None:
        """
        Args:
            point: COORD - searched
            idScale: int - номер SCALE - num scale
        Returns:
            bladdr_map: BLADDR
        """
        # проверка на существование масштаба
        if idScale < 0 or idScale > len(self.scales):
            return None
        sc: SCALE = self.scales[idScale]
        # проверка на то, что scale валиден
        if sc.isEmpty:
            return None
        res = sc.find_by_coord(point)
        return res


# -------------------------------------------------------------------------

if __name__ == '__main__':
    # from vdo.datatypes import VDO_FILE
    from QGIS_VDO.vdo.test_vdo import vdo30, vdo34ee, vdobmv, vdo34bnl, vdoRu  # noqa
    from QGIS_VDO.vdo.consts import struct_UINT        # noqa

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
    vdo = vdo30

    bladdr_scales: BLADDR = vdo.get_block(0).bladdr_scales      # type: ignore
    block_07: block_0x07 = vdo.get_block(bladdr_scales)         # type: ignore
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
