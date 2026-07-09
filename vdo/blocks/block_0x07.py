"""
0x07  SCALES
Набор масштабов, начальный для определения по координатам
и масштабу текущего отображения блока с геосодержимым.

block_0x07
SCALE

"""

from QGIS_VDO.vdo.consts import struct_WORD  # struct_UINT
from QGIS_VDO.vdo.enums import en_POI_CAT
from QGIS_VDO.vdo.block_base import block_base
from QGIS_VDO.vdo.datatypes import BYTESTRUCT, BLADDR, OFFSET_TOC, VDO_FILE   # LIST,
from QGIS_VDO.vdo.geotypes import COORD


OFFSET_TERR_DIVISIONS = 0x0C
OFFSET_COUNTRY_LIST = 0x10
SCALES_COUNT = 12


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
        lb = COORD(self._raw[4:12])
        rt = COORD(self._raw[12:20])
        self.area = (lb, rt)
        self.val_A = struct_WORD.unpack(self._raw[20:22])[0]
        self.zoom_from = struct_WORD.unpack(self._raw[22:24])[0]
        if vdo.dbrev == 34:
            self.zoom_to = struct_WORD.unpack(self._raw[24:26])[0]
        else:
            self.zoom_to = 0

        # TODO а оно надо?
        self.square_side = (self.area[1]._hlat - self.area[0]._hlat)
        self.d_delta = self.area[1].delta(self.area[0])

        # Список idx
        self.idxs = {}  # dict areas, key - block_0x09, val - area

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
    """ CH_country type 0x0b  # fully parsed chars idxs """

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
            poi_code = struct_WORD.unpack(self.read(offset, 2))[0]
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
    from vdo.blocks import block_0x12

    vdo = vdo30
    # vdo = vdo34ee
    # vdo = vdobmv

    bl_toc: block_0x12 = vdo.get_block(0)
    bl_scales: BLADDR = bl_toc.bladdr_scales

    block_07: block_0x07 = vdo.get_block(bl_scales)

    scale_5 = block_07.scales[5]

    # @ 00000201 13 0202 [13:BIBLIOGR]
    pass
