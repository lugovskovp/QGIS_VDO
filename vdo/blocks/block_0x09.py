"""
FOLDER_MAPS = 0x09		# map folders 0x09.

Индекс гео-блоков
"""

from typing import Iterator, cast

from QGIS_VDO.vdo.datatypes import BLADDR, PTR
from QGIS_VDO.vdo.block_base import block_base
from QGIS_VDO.vdo.geotypes import COORD


OFFSET_LIST_PTR = 0x08
OFFSET_GEOBLOCKS = 0x0c
OFFSET_FOLDER_SIZE = 0x10


class block_0x09(block_base):
    """
    0x08    LIST    li_p_geo  ptr_cnt на near ptr | 0, указывающие на bladdr
    0x0c    LIST    li_valid  ptr_cnt на список только валидных BLADDR
    0x10    UINT    размер приращения _hlat на следующий p_geo
    0x14    [PTR]   near ptr | 0, указывающие на bladdr
            [BLADDR] - массив папки-индексы гео-блоков
    """
    def __init__(self, bl_addr: BLADDR, origin: COORD, max: COORD) -> None:
        super().__init__(bl_addr)

        # item - one ptr to map block
        self.li_items = self.list(OFFSET_LIST_PTR)
        self.li_valid = self.list(OFFSET_GEOBLOCKS)
        self.item_side = self.uint(OFFSET_FOLDER_SIZE)

        self.origin = origin      # "начало" координат, left bottom
        self.qty_y = int((max._hlatitude - origin._hlatitude) / self.item_side)
        self.qty_x = int((max._hlongtitude - origin._hlongtitude) / self.item_side)
        pass    # __init__(self, bl_addr: BLADDR, origin: COORD, max: COORD)

    def items_cnt(self) -> int:
        """
        Возвращает количество уникальных итемов
        """
        return self.li_valid.cnt

    def get_items(self) -> Iterator[tuple]:
        """
        Генератор валидных итемов с координатами COORD lb, rt
        Returns:
            res = (bla_val, coord_lb, coord_rt): tuple
                bla_val: int - значение bladdr map - geoblock
                coord_lb: COORD left bottom
                coord_rt: COORD right top
        """
        finded_early = []        # ранее ptr уже был найден
        step = PTR.size          # единица приращения
        # "координаты" в квадрате ареа
        for x in range(self.qty_x):
            # в файле перебор по вертикали, потом по Х
            for y in range(self.qty_y):
                curr_item = y + x * self.qty_x
                if curr_item >= self.li_items.cnt:
                    # количество итемов может быть меньше квадрата стороны
                    break
                offset = self.li_items.ptr + step * curr_item
                ptr_val = self.ushort(offset)
                if not ptr_val or ptr_val in finded_early:
                    # следующий, если ptr_val == 0
                    continue

                # finded new ptr
                finded_early.append(ptr_val)

                # calculate X side size
                size_X = 0
                for i in range(x, self.qty_x):
                    next_item = y + i * self.qty_x
                    off_next = self.li_items.ptr + step * next_item
                    ptr_next_val = self.ushort(off_next)
                    if ptr_next_val != ptr_val:
                        break
                    size_X += 1
                
                # Calculate Y side size
                size_Y = 0
                for i in range(y, self.qty_y):
                    next_item = x * self.qty_x + i
                    off_next = self.li_items.ptr + step * next_item
                    ptr_next_val = self.ushort(off_next)
                    if ptr_next_val != ptr_val:
                        break
                    size_Y += 1

                # read bladdr_value
                bladdr_map_val = self.uint(ptr_val)
                # Долгота (Lng) E/W - x
                hex_lon = self.origin._hlongtitude + x * self.item_side
                # Широта (Lat) N/S - y
                hex_lat = self.origin._hlatitude + y * self.item_side
                coord_lb = COORD(hex_lon, hex_lat)
                hex_lon += size_X * self.item_side
                hex_lat += size_Y * self.item_side
                coord_rt = COORD(hex_lon, hex_lat)
                res = (bladdr_map_val, coord_lb, coord_rt)
                yield res


# -------------------------------------------------------------------------

if __name__ == '__main__':
    # from vdo.datatypes import VDO_FILE
    from vdo.test_vdo import vdo30, vdo34ee, vdobmv, vdo34bnl, vdoRu  # noqa
    from vdo.consts import struct_UINT        # noqa
    from vdo.blocks import block_0x12, block_0x07, block_0x08

    vdo = vdo30
    # vdo = vdo34ee
    # vdo = vdobmv
    # vdo = vdo34bnl
    vdo = vdoRu

    bl_toc: block_0x12 = cast("block_0x12", vdo.get_block(0))
    bl_scales: BLADDR = bl_toc.bladdr_scales

    block_07: block_0x07 = cast("block_0x07", vdo.get_block(bl_scales))

    scale_5 = block_07.scales[5]
    scale_5 = block_07.scales[11]
    block_almanac: block_0x08 = cast("block_0x08", vdo.get_block(scale_5.almanac_idx, scale_5.area[0], scale_5.area[1]))  # noqa

    # block_08 content
    print(f"block_08: 0x{block_almanac} block_0x09 : x : y")
    bla_first_val = None
    for f in block_almanac.get_items():
        if not bla_first_val:
            (bla_first_val, coord_lb, coord_rt) = f
        print(f)
        pass
    
    bla_first = BLADDR(struct_UINT.pack(bla_first_val), vdo)
    block_maps: block_0x09 = cast("block_0x09", vdo.get_block(bla_first, coord_lb, coord_rt))

    print(f"\nmap{block_maps}")
    for f in block_maps.get_items():
        print(f)
        pass
    pass

    # (156661763, 31.641849N 20.643179W, 49.761244N 2.523783W)
    bla = BLADDR(struct_UINT.pack(156661763), vdo)
    bla_map = vdo.get_block(bla)

    """
    vdo ru
    scale 3
    fldr - 0x6766107
    map - 0x110573619

    """
    print()
    search_fldr = 0x6766107
    search_map = 110573619
    # search_map = 0x110586636
    # search_map = 0x110449163
    scale = block_07.scales[3]
    block_almanac: block_0x08 = cast("block_0x08", vdo.get_block(scale.almanac_idx, scale.area[0], scale.area[1]))  # noqa
    for (bl_folder, coord_lb, coord_rt) in block_almanac.get_items():
        if bl_folder == search_fldr:
            break
    #
    bla = BLADDR(struct_UINT.pack(bl_folder), vdo)
    block_maps: block_0x09 = cast("block_0x09", vdo.get_block(bla, coord_lb, coord_rt))
    for (bl_map, coord_lb, coord_rt) in block_maps.get_items():
        print(bl_map, coord_lb, coord_rt)
        if bl_map == 110553640:
            pass
        # 110553640 50.893706N 7.102145E 51.459937N 7.668376E
        # 110573619 51.459937N 7.102145E 52.026168N 7.385261E
        if bl_map == search_map:    # 110573619
            print("finded")
            break

    pass
