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

# from QGIS_VDO.vdo.consts import struct_WORD  # struct_UINT
from QGIS_VDO.vdo.enums import en_POI_CAT
from QGIS_VDO.vdo.block_base import block_base
from QGIS_VDO.vdo.datatypes import BYTESTRUCT, BLADDR, OFFSET_TOC, VDO_FILE   # LIST,
from QGIS_VDO.vdo.geotypes import COORD
from QGIS_VDO.vdo.blocks import block_0x08


OFFSET_TERR_DIVISIONS = 0x0C
OFFSET_COUNTRY_LIST = 0x10
SCALES_COUNT = 12


class GEO_INDEX(BYTESTRUCT):
    """
    """
    def __init__(self, byte_array: bytes) -> None:

        pass


class SCALE(BYTESTRUCT):
    """
    0   UINT    BLADDR almanac_ids
    4   QWORD   COORD left bottom
    12  QWORD   COORD right top
    20  WORD    value_a - unknown, [6, 0, 1, 2, 65535*]
    22  WORD    zoom_from, [0, 1, 320, 40, 120, 1200, 3000]
    24* WORD    zoom_to, [0, 1, 3000, 1200, 120, 40, 65535]
    * - only dbrev.34
    """
    def __init__(self, byte_array: bytes, vdo: VDO_FILE) -> None:
        if vdo.dbrev == 34:
            self.size = 0x1C
        elif vdo.dbrev == 30:
            self.size = 0x18
        else:
            raise ValueError(vdo.dbrev, " dbrev must be 30 or 34")

        super().__init__(byte_array)
        # area
        self.almanac_idx = BLADDR(self._raw[:4], vdo)
        point_lb = COORD(self._raw[4:12])
        point_rt = COORD(self._raw[12:20])
        self.area = (point_lb, point_rt)
        # 20  WORD    value_a - unknown, [6, 0, 1, 2, 65535*]
        self.val_A = self.ushort(20)
        # 22  WORD    zoom_from, [0, 1, 320, 40, 120, 1200, 3000]
        self.zoom_from = self.ushort(22)
        if vdo.dbrev == 34:
            # 24* WORD    zoom_to, [0, 1, 3000, 1200, 120, 40, 65535]
            self.zoom_to = self.ushort(24)
        else:
            self.zoom_to = 0

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
        res += f" {self.zoom_from}-{self.zoom_to} {self.val_A}"
        res += f" [0x{self.square_side:X}]"
        return res

    @property
    def is_empty(self) -> bool:
        """ Валидный или пустой"""
        # если almanac_idx == 0, то scale пустой
        return self.almanac_idx.isZero

    def find_idx(self, poin: COORD) -> BLADDR | None:
        """
        Поиск idx блока, в который попадают координаты, или None
        """
        res = None
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
            self.li_countries = self.list(OFFSET_COUNTRY_LIST)
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
        self.li_country_divisions = self.list(OFFSET_TERR_DIVISIONS)

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
        return self.list(OFFSET_TOC)


# -------------------------------------------------------------------------

if __name__ == '__main__':
    # from vdo.datatypes import VDO_FILE
    from vdo.test_vdo import vdo30, vdo34ee, vdobmv # noqa
    from vdo.consts import struct_UINT        # noqa
    from vdo.blocks import block_0x12, block_0x09

    vdo = vdo30
    # vdo = vdo34ee
    # vdo = vdobmv

    bl_toc: block_0x12 = vdo.get_block(0)
    bl_scales: BLADDR = bl_toc.bladdr_scales

    block_07: block_0x07 = vdo.get_block(bl_scales)

    scale_5 = block_07.scales[6]
    block_almanac: block_0x08 = vdo.get_block(scale_5.almanac_idx)  # block_08

    # block_08 content
    print("block_08: block_0x09 : x : y")
    for f in block_almanac._get_raw_content():
        print(f)
        pass
    
    # block_08 content
    print("block_08: block_0x09 : COORD(lb) : COORD(rt)")
    bla_first = None
    for (f, lb, rt) in block_almanac.items(scale_5.area[0]):
        if not bla_first:
            bla_first = f   # noqa 03cdcc01 09 0000 [09:FOLDER_MAPS] - qty 16 area 0x1400 0000 item(fromFile) 0x140 0000
            lb_f = lb
            rt_f = rt
        print((f, lb, rt))
        pass
    
    # block_09 content
    print("block_09: geo_block_0xXX : x : y")
    bl_folder: block_0x09 = vdo.get_block(bla_first.offset)

    print("block_08: block_0x09 : COORD(lb) : COORD(rt)")
    for f in bl_folder._get_raw_content():
        print(f)
        pass

    bl_map_first = None
    for f in bl_folder.items(lb_f):     # 03cdcc01 09 0000 [09:FOLDER_MAPS]
        if not bl_map_first:
            (bl_map_first, lb_map, _) = f
            print(f"map: {bl_map_first} lb_coord: {lb_map}")
        pass
    
    # map
    bl_map = vdo.get_block(bl_map_first)

    print(f"infile map area: {bl_map.map}")

    # bl_ru_big_map = vdo.get_block(BLADDR(struct_UINT.pack(0x)))
    # @ 00000201 13 0202 [13:BIBLIOGR]
    pass
