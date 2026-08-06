"""
FOLDER_MAPS = 0x09		# map folders 0x09.

Индекс гео-блоков
"""

from typing import Iterator

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
        self.li_items = self.read_list(OFFSET_LIST_PTR)
        self.li_valid = self.read_list(OFFSET_GEOBLOCKS)
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

                # # Долгота (Lng) E/W - x
                # hex_lon = self.origin._hlongtitude + x * self.item_side
                # # Широта (Lat) N/S - y
                # hex_lat = self.origin._hlatitude + y * self.item_side
                # coord_lb = COORD(hex_lon, hex_lat)
                # hex_lon += size_X * self.item_side
                # hex_lat += size_Y * self.item_side
                # coord_rt = COORD(hex_lon, hex_lat)

                (coord_lb, coord_rt) = self.get_xy_area(x, y, size_X, size_Y)
                # res = (bladdr_map_val, coord_lb, coord_rt)
                yield (bladdr_map_val, coord_lb, coord_rt)

    def get_xy_area(self, x: int, y: int, x_size: int, y_size: int) -> tuple[COORD, COORD]:
        """
        Args:
            x, y: int - "координаты" левого нижнего в квадрате
            x_size, y_size: int - размеры сторон
        значения x, y ОБЯЗАНЫ быть 0..qty_x, не проверяется
        Returns:
            tuple[left_bottov, right_top]
                left_bottom: COORD
                right_top: COORD
        """
        # left bottom
        # Долгота (Lng) E/W - x
        hex_lon = self.origin._hlongtitude + x * self.item_side
        # Широта (Lat) N/S - y
        hex_lat = self.origin._hlatitude + y * self.item_side
        coord_lb = COORD(hex_lon, hex_lat)

        # right top
        hex_lon += x_size * self.item_side
        hex_lat += y_size * self.item_side
        coord_rt = COORD(hex_lon, hex_lat)

        return (coord_lb, coord_rt)

    def get_xy_item(self, x, y) -> BLADDR | None:
        """
        Вернуть bladdr карты
        Args:
            x, y: int "координаты" в "квадрате" итемов
        Returns:
            block: BLADDR, item self - geo_block
        """
        item_num = y + x * self.qty_y
        offset = self.li_items.ptr + item_num * PTR.size
        # items in 0x09 - ptr to bladdr
        if not (ptr := self.ushort(offset)):
            # non valid ptr == 0
            return None
        # а вот теперь сам bladdr, и он точно не самый первый блок
        # bladdr_val = self.uint(ptr)
        # bladdr = self.bladdr(self.uint(ptr))
        return self.bladdr(self.uint(ptr))
    
    def find_by_coord(self, srch: COORD) -> BLADDR | None:
        """
        Поиск блока КАРТЫ, в который попадают координаты, или None
        """
        # проверка, что srch в пределах координат блока
        max_hlatitude = self.origin._hlatitude + self.qty_y * self.item_side
        max_hlongtitude = self.origin._hlongtitude + self.qty_x * self.item_side
        if srch._hlatitude < self.origin._hlatitude or srch.lat > max_hlatitude \
           or srch._hlongtitude < self.origin._hlongtitude or srch.lon > max_hlongtitude:
            # не попал в квадрат lb-rt
            print(f"bl_0x08: No way: {srch} not in {self.area}")
            return None
        # расчет offset для srch : _hlongtitude - SIGNED!
        # delta_hlon_x = (srch._hlongtitude - self.origin._hlongtitude) / self.item_side
        # delta_hlat_y = (srch._hlatitude - self.origin._hlatitude) / self.item_side
        delta_x = int((srch._hlongtitude - self.origin._hlongtitude) / self.item_side)
        delta_y = int((srch._hlatitude - self.origin._hlatitude) / self.item_side)
        # Если есть такой блок в итемах
        if (bladdr_map := self.get_xy_item(delta_x, delta_y)) is None:
            return None
        # координаты углов полученного итема не нужны - есть внутри geoblock
        return bladdr_map
# -------------------------------------------------------------------------


if __name__ == '__main__':
    # from vdo.datatypes import VDO_FILE
    from QGIS_VDO.vdo.test_vdo import vdo30, vdo34ee, vdobmv, vdo34bnl, vdoRu  # noqa
    from QGIS_VDO.vdo.consts import struct_UINT        # noqa
    from QGIS_VDO.vdo.blocks import block_0x12, block_0x07, block_0x08

    vdo = vdo30
    # vdo = vdo34ee
    # vdo = vdobmv
    # vdo = vdo34bnl
    vdo = vdoRu

    bl_toc: block_0x12 = vdo.get_block(0)
    bl_scales: BLADDR = bl_toc.bladdr_scales

    block_07: block_0x07 = vdo.get_block(bl_scales)

    scale_5 = block_07.scales[5]
    scale_5 = block_07.scales[11]
    block_almanac: block_0x08 = vdo.get_block(scale_5.almanac_idx, scale_5.area[0], scale_5.area[1])

    # block_08 content
    print(f"block_08: 0x{block_almanac} block_0x09 : x : y")
    bla_first_val = None
    for f in block_almanac.get_items():
        if not bla_first_val:
            (bla_first_val, coord_lb, coord_rt) = f
        print(f)
        pass
    
    bla_first = BLADDR(struct_UINT.pack(bla_first_val), vdo)
    block_maps: block_0x09 = vdo.get_block(bla_first, coord_lb, coord_rt)

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
    search_map = 110573619      # 0x6973833
    # search_map = 0x110586636
    # search_map = 0x110449163
    scale = block_07.scales[3]
    block_almanac: block_0x08 = vdo.get_block(scale.almanac_idx, scale.area[0], scale.area[1])
    for (bl_folder, coord_lb, coord_rt) in block_almanac.get_items():
        if bl_folder == search_fldr:
            break
    #
    bla = BLADDR(struct_UINT.pack(bl_folder), vdo)
    block_maps: block_0x09 = vdo.get_block(bla, coord_lb, coord_rt)
    for (bl_map, coord_lb, coord_rt) in block_maps.get_items():
        print(f"0x{bl_map:X}", bl_map, coord_lb, coord_rt)
        if bl_map == 110553640:
            pass
        # 110553640 50.893706N 7.102145E 51.459937N 7.668376E
        # 110573619 51.459937N 7.102145E 52.026168N 7.385261E
        if bl_map == search_map:    # 110573619
            print("finded")
            break

    pass
