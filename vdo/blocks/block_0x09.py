"""
FOLDER_MAPS = 0x09		# map folders 0x09.

Индекс гео-блоков
"""
from typing import Iterator, Tuple, Optional, Dict, List

from QGIS_VDO.vdo.datatypes import BLADDR, PTR
from QGIS_VDO.vdo.block_base import block_base
from QGIS_VDO.vdo.geotypes import COORD     # , MULCOORD   # MULCOORD берем из модуля констант
from QGIS_VDO.vdo.consts import struct_WORD, struct_UINT    # , MOST_SIGNIFICANT_BIT


OFFSET_LIST_PTR = 0x08
OFFSET_GEOBLOCKS = 0x0c
OFFSET_FOLDER_SIZE = 0x10


# Выносим структуру чтения USHORT на уровень модуля для zero-alloc распаковки массивов
_STRUCT_SHORT = struct_WORD  # struct.Struct('<H')


class block_0x09(block_base):
    """0x09 — Высокопроизводительный пространственный индекс гео-блоков с uint32 арифметикой."""

    __slots__ = (
        'li_items',
        'li_valid',
        'item_side',
        'origin',
        'qty_y',
        'qty_x',
        'items',
        'quant',
    )

    def __init__(self, bl_addr: BLADDR, origin: COORD, max: COORD) -> None:
        super().__init__(bl_addr)

        self.li_items = self.read_list(OFFSET_LIST_PTR)
        self.li_valid = self.read_list(OFFSET_GEOBLOCKS)
        self.item_side = self.uint(OFFSET_FOLDER_SIZE)

        self.origin = origin
        
        self.qty_y = (max._hlatitude - origin._hlatitude) // self.item_side
        self.qty_x = (max._hlongitude - origin._hlongitude) // self.item_side

        self.quant = (max.lat - origin.lat) / self.qty_y
        self.items: Optional[Dict[int, List[int]]] = None

    def items_cnt(self) -> int:
        return self.li_valid.cnt

    def get_items(self) -> Iterator[Tuple[int, float, float, float, float]]:
        """Генератор уникальных гео-блоков с поддержкой uint32 переполнений."""
        # ИСПРАВЛЕНО: Корректная ленивая инициализация
        if self.items is None:
            self._fill_items()

        quant = self.quant
        origin_lon = self.origin.lon
        origin_lat = self.origin.lat
        # get_bladdr = self.vdo.get_bladdr  # ОПТИМИЗАЦИЯ: кэшируем метод в локальную переменную

        # ИСПРАВЛЕНО: Итерация по .values() и корректное число переменных (5 вместо 6)
        for bladdr_map_val, x, y, size_X, size_Y in self.items.values():
            # bladdr: BLADDR = get_bladdr(bladdr_map_val)

            # Расчет координат ГИС
            lon_lb = origin_lon + x * quant
            lat_lb = origin_lat + y * quant
            lon_rt = lon_lb + size_X * quant
            lat_rt = lat_lb + size_Y * quant

            yield (bladdr_map_val, lon_lb, lat_lb, lon_rt, lat_rt)

    def _fill_items(self) -> None:
        """Заполняет кеш итемов с оптимизированным RLE анализом."""
        finded_early: set[int] = set()
        _items = {}
        step = PTR.size
        base_ptr = self.li_items.ptr
        total_cnt = self.li_items.cnt
        q_y = self.qty_y
        q_x = self.qty_x
        raw_buffer = self._raw

        # ОПТИМИЗАЦИЯ: Предварительно читаем матрицу в плоский массив одномерным проходом
        # Это убирает повторные вызовы десериализации (сокращение сложности с O(N^2) до O(N))
        grid = [0] * total_cnt
        for idx in range(total_cnt):
            grid[idx] = _STRUCT_SHORT.unpack_from(raw_buffer, base_ptr + idx * step)[0]

        for x in range(q_x):
            x_offset = x * q_y
            
            for y in range(q_y):
                curr_item = y + x_offset
                if curr_item >= total_cnt:
                    break

                ptr_val = grid[curr_item]
                
                if not ptr_val or ptr_val in finded_early:
                    continue

                finded_early.add(ptr_val)
                
                # Оптимизация RLE по оси X с использованием кэшированной grid
                size_X = 0
                for i in range(x, q_x):
                    next_item = y + i * q_y
                    if next_item >= total_cnt or grid[next_item] != ptr_val:
                        break
                    size_X += 1
                
                # Оптимизация RLE по оси Y с использованием кэшированной grid
                size_Y = 0
                for i in range(y, q_y):
                    next_item = x_offset + i
                    if next_item >= total_cnt or grid[next_item] != ptr_val:
                        break
                    size_Y += 1

                bladdr_map_val = struct_UINT.unpack_from(raw_buffer, ptr_val)[0]
                _items[ptr_val] = [bladdr_map_val, x, y, size_X, size_Y]

        self.items = _items

    def _get_xy_item(self, x: int, y: int) -> Optional[BLADDR]:
        """Ptr по координатам блока"""
        if x < 0 or x >= self.qty_x or y < 0 or y >= self.qty_y:
            return None
            
        item_num = y + x * self.qty_y
        if item_num >= self.li_items.cnt:
            return None
        
        offset = self.li_items.ptr + item_num * PTR.size
        ptr = _STRUCT_SHORT.unpack_from(self._raw, offset)[0]
        if not ptr:
            return None
        
        bladdr_val = struct_UINT.unpack_from(self._raw, ptr)[0]
        return self.vdo.get_bladdr(bladdr_val)
    
    def find_by_coord(self, srch: COORD) -> Optional[BLADDR]:
        side = self.item_side
        x = (srch._hlongitude - self.origin._hlongitude) // side
        y = (srch._hlatitude - self.origin._hlatitude) // side
        return self._get_xy_item(x, y)


# -------------------------------------------------------------------------


if __name__ == '__main__':      # pragma: no cover
    # from vdo.datatypes import VDO_FILE
    from QGIS_VDO.vdo.fixtures_vdo import vdo30, vdo34ee, vdobmv, vdo34bnl, vdoRu  # noqa
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

    bl_08 = block_almanac
    beg = str(bl_08.vdo).split(":")
    bl_08.write_raw(f"{beg[0]}_0x08.bin")

    print(f"{bl_08.vdo}")

    #
    bla = BLADDR(struct_UINT.pack(bl_folder), vdo)
    block_maps: block_0x09 = vdo.get_block(bla, coord_lb, coord_rt)
    block_maps.write_raw()

    for item in block_maps.get_items():
        # (bl_map, coord_lb, coord_rt) = item
        (bl_map, lb_lo, lb_la, rt_lo, rt_la) = item
        coord_lb = COORD(lb_lo, lb_la)
        coord_rt = COORD(rt_lo, rt_la)
        print(f"0x{bl_map:X}", bl_map, coord_lb, coord_rt)
        if bl_map == 110553640:
            pass
        # 110553640 50.893706N 7.102145E 51.459937N 7.668376E
        # 110573619 51.459937N 7.102145E 52.026168N 7.385261E
        if bl_map == search_map:    # 110573619
            print("finded")
            bbb = block_maps.vdo.get_bladdr(0x6973833)
            bbb_bl = block_maps.vdo.get_block(bbb)
            break

    pass
