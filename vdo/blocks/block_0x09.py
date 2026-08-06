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
    """0x09 — Индексная папка гео-блоков с оптимизированной структурой памяти."""

    # 1. Жестко фиксируем слоты. __slots__ не наследуются автоматически!
    # Дочерний класс обязан объявить свои слоты, иначе для него создается __dict__.
    __slots__ = (
        'li_items',
        'li_valid',
        'item_side',
        'origin',
        'qty_y',
        'qty_x'
    )

    def __init__(self, bl_addr: BLADDR, origin: COORD, max: COORD) -> None:
        super().__init__(bl_addr)

        self.li_items = self.read_list(OFFSET_LIST_PTR)
        self.li_valid = self.read_list(OFFSET_GEOBLOCKS)
        self.item_side = self.uint(OFFSET_FOLDER_SIZE)

        self.origin = origin   # "начало" координат, left bottom
        
        # Микрооптимизация: побитовый сдвиг или деление с округлением вниз // работает быстрее int(a / b)
        self.qty_y = (max._hlatitude - origin._hlatitude) // self.item_side
        self.qty_x = (max._hlongtitude - origin._hlongtitude) // self.item_side

    def items_cnt(self) -> int:
        """
        Возвращает количество уникальных итемов
        """
        return self.li_valid.cnt

    def get_items(self) -> Iterator[tuple[int, COORD, COORD]]:
        """Генератор уникальных гео-блоков.
        Returns:
            res = (bla_val, coord_lb, coord_rt): tuple
                bla_val: int - значение bladdr map - geoblock
                coord_lb: COORD left bottom
                coord_rt: COORD right top
        Сложность поиска дубликатов снижена с O(N) до O(1).
        """
        # ОПТИМИЗАЦИЯ: Множество (set) гарантирует поиск 'in' за константное время O(1)
        finded_early: set[int] = set()
        step = PTR.size
        base_ptr = self.li_items.ptr
        total_cnt = self.li_items.cnt
        q_y = self.qty_y  # Локальные переменные в Python читаются быстрее, чем атрибуты self

        for x in range(self.qty_x):
            # В VDO-форматах традиционно идет упорядочивание по столбцам (Y), затем по строкам (X)
            x_offset = x * q_y
            
            for y in range(q_y):
                curr_item = y + x_offset
                if curr_item >= total_cnt:
                    # количество итемов может быть меньше квадрата стороны
                    break

                offset = base_ptr + step * curr_item
                ptr_val = self.ushort(offset)
                if not ptr_val or ptr_val in finded_early:
                    continue

                finded_early.add(ptr_val)

                # Вычисляем размер по оси X (смерженные блоки)
                size_X = 0
                for i in range(x, self.qty_x):
                    next_item = y + i * q_y
                    if next_item >= total_cnt:
                        break
                    if self.ushort(base_ptr + step * next_item) != ptr_val:
                        break
                    size_X += 1
                
                # Вычисляем размер по оси Y
                size_Y = 0
                for i in range(y, q_y):
                    next_item = x_offset + i
                    if next_item >= total_cnt:
                        break
                    if self.ushort(base_ptr + step * next_item) != ptr_val:
                        break
                    size_Y += 1

                bladdr_map_val = self.uint(ptr_val)
                # # Долгота (Lng) E/W - x
                # hex_lon = self.origin._hlongtitude + x * self.item_side
                # # Широта (Lat) N/S - y
                # hex_lat = self.origin._hlatitude + y * self.item_side
                # coord_lb = COORD(hex_lon, hex_lat)
                # hex_lon += size_X * self.item_side
                # hex_lat += size_Y * self.item_side
                # coord_rt = COORD(hex_lon, hex_lat)
                yield (bladdr_map_val, *self.get_xy_area(x, y, size_X, size_Y))

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
        # Локальный кэш для устранения повторных обращений через точку внутри горячего метода
        side = self.item_side
        orig = self.origin
        # left bottom
        # Долгота (Lng) E/W - x
        hex_lon = orig._hlongtitude + x * side
        # Широта (Lat) N/S - y
        hex_lat = orig._hlatitude + y * side
        coord_lb = COORD(hex_lon, hex_lat)

        coord_rt = COORD(hex_lon + x_size * side, hex_lat + y_size * side)
        return coord_lb, coord_rt

    def get_xy_item(self, x: int, y: int) -> BLADDR | None:
        """
        Вернуть bladdr карты
        Args:
            x, y: int "координаты" в "квадрате" итемов
        Returns:
            block: BLADDR, item self - geo_block
        """
        item_num = y + x * self.qty_y
        if item_num >= self.li_items.cnt:
            return None
            
        offset = self.li_items.ptr + item_num * PTR.size
        # items in 0x09 - ptr to bladdr
        ptr = self.ushort(offset)
        if not ptr:
            return None
            
        return self.vdo.get_bladdr(self.uint(ptr))
    
    def find_by_coord(self, srch: COORD) -> BLADDR | None:
        """
        Поиск блока КАРТЫ, в который попадают координаты, или None
        """
        orig = self.origin
        side = self.item_side
        
        # Быстрая проверка границ через локальные переменные
        max_hlatitude = orig._hlatitude + self.qty_y * side
        max_hlongtitude = orig._hlongtitude + self.qty_x * side
        
        # Проверяем также сырые методы .lat/.lon, если они используются в классе COORD
        if (srch._hlatitude < orig._hlatitude or srch._hlatitude > max_hlatitude
                or srch._hlongtitude < orig._hlongtitude or srch._hlongtitude > max_hlongtitude):
            # Избегаем тяжелых f-строк в легаси-логах, если они не будут напечатаны
            # print(f"bl_0x08: No way: {srch} not in area")
            return None

        delta_x = (srch._hlongtitude - orig._hlongtitude) // side
        delta_y = (srch._hlatitude - orig._hlatitude) // side
        
        return self.get_xy_item(delta_x, delta_y)

# -------------------------------------------------------------------------


if __name__ == '__main__':      # pragma: no cover
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

    bl_08 = block_almanac
    beg = str(bl_08.vdo).split(":")
    bl_08.write_raw(f"{beg[0]}_0x08.bin")

    print(f"{bl_08.vdo}")

    #
    bla = BLADDR(struct_UINT.pack(bl_folder), vdo)
    block_maps: block_0x09 = vdo.get_block(bla, coord_lb, coord_rt)
    block_maps.write_raw()

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
