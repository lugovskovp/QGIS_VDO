"""
FOLDER_MAPS = 0x09		# map folders 0x09.

Индекс гео-блоков
"""
from typing import Iterator, Tuple

from QGIS_VDO.vdo.datatypes import BLADDR, PTR
from QGIS_VDO.vdo.block_base import block_base
from QGIS_VDO.vdo.geotypes import COORD, MULCOORD   # MULCOORD берем из модуля констант
from QGIS_VDO.vdo.consts import struct_WORD, struct_UINT


OFFSET_LIST_PTR = 0x08
OFFSET_GEOBLOCKS = 0x0c
OFFSET_FOLDER_SIZE = 0x10


# Выносим структуру чтения USHORT на уровень модуля для zero-alloc распаковки массивов
# Предполагаем, что у вас есть struct_WORD для чтения 2 байт.
_STRUCT_SHORT = struct_WORD  # struct.Struct('<H')


class block_0x09(block_base):
    """0x09 — Высокопроизводительный пространственный индекс гео-блоков."""

    __slots__ = (
        'li_items',
        'li_valid',
        'item_side',
        'origin_hlon',  # Кэшируем сырые int вместо хранения объекта COORD
        'origin_hlat',
        'qty_y',
        'qty_x'
    )

    def __init__(self, bl_addr: BLADDR, origin: COORD, max: COORD) -> None:
        super().__init__(bl_addr)

        self.li_items = self.read_list(OFFSET_LIST_PTR)
        self.li_valid = self.read_list(OFFSET_GEOBLOCKS)
        self.item_side = self.uint(OFFSET_FOLDER_SIZE)
        self.write_raw("c:/temp/bl.bin")    # ""
        # ОПТИМИЗАЦИЯ: Раскладываем COORD на примитивы int.
        # Избавляемся от удержания ссылок на тяжелые объекты геометрии.
        self.origin_hlon = origin._hlon
        self.origin_hlat = origin._hlat
        
        # Целочисленное деление на Си-уровне
        self.qty_y = (max._hlatitude - origin._hlatitude) // self.item_side
        self.qty_x = (max._hlongitude - origin._hlongitude) // self.item_side

    def items_cnt(self) -> int:
        return self.li_valid.cnt

    def get_items(self) -> Iterator[Tuple[int, float, float, float, float]]:
        """Генератор уникальных гео-блоков.
        
        Вместо объектов COORD возвращает плоский кортеж WGS-84 координат:
        (bladdr_map_val, lon_min, lat_min, lon_max, lat_max)
        Это снижает нагрузку на GC (Garbage Collector) до нуля.
        """
        finded_early: set[int] = set()
        step = PTR.size
        base_ptr = self.li_items.ptr
        total_cnt = self.li_items.cnt
        q_y = self.qty_y
        q_x = self.qty_x
        side = self.item_side
        
        # Кэшируем значения для быстрой float-математики WGS-84 без вызова свойств COORD
        # MULCOORD берем из модуля констант

        # Загружаем байты всего списка указателей в memoryview один раз
        # Это позволяет читать ushort() без вызова накладных расходов методов BYTESTRUCT
        raw_buffer = self._raw

        for x in range(q_x):
            x_offset = x * q_y
            
            for y in range(q_y):
                curr_item = y + x_offset
                if curr_item >= total_cnt:
                    break

                offset = base_ptr + step * curr_item
                # Прямая распаковка из буфера без вызова self.ushort()
                ptr_val = _STRUCT_SHORT.unpack_from(raw_buffer, offset)[0]
                
                if not ptr_val or ptr_val in finded_early:
                    continue

                finded_early.add(ptr_val)

                # Оптимизация RLE по оси X
                size_X = 0
                for i in range(x, q_x):
                    next_item = y + i * q_y
                    if next_item >= total_cnt:
                        break
                    if _STRUCT_SHORT.unpack_from(raw_buffer, base_ptr + step * next_item)[0] != ptr_val:
                        break
                    size_X += 1
                
                # Оптимизация RLE по оси Y
                size_Y = 0
                for i in range(y, q_y):
                    next_item = x_offset + i
                    if next_item >= total_cnt:
                        break
                    if _STRUCT_SHORT.unpack_from(raw_buffer, base_ptr + step * next_item)[0] != ptr_val:
                        break
                    size_Y += 1

                bladdr_map_val = struct_UINT.unpack_from(raw_buffer, ptr_val)[0]

                # --- Мгновенный расчет координат ГИС "на лету" без аллокации COORD ---
                # Рассчитываем сырые VDO-координаты
                hlon_lb = self.origin_hlon + x * side
                hlat_lb = self.origin_hlat + y * side
                hlon_rt = hlon_lb + size_X * side
                hlat_rt = hlat_lb + size_Y * side

                # Переводим в WGS-84 float аналогично логике COORD._do_calculate_lon_lat
                # (Учитываем знаковые переходы, если координаты могут быть отрицательными)
                lon_min = (((hlon_lb - 0x100000000 if hlon_lb & 0x80000000 else hlon_lb) / MULCOORD) - 30)
                lat_min = (hlat_lb - 0x100000000 if hlat_lb & 0x80000000 else hlat_lb) / MULCOORD
                lon_max = (((hlon_rt - 0x100000000 if hlon_rt & 0x80000000 else hlon_rt) / MULCOORD) - 30)
                lat_max = (hlat_rt - 0x100000000 if hlat_rt & 0x80000000 else hlat_rt) / MULCOORD

                yield (bladdr_map_val, lon_min, lat_min, lon_max, lat_max)

    def get_xy_item(self, x: int, y: int) -> BLADDR | None:
        item_num = y + x * self.qty_y
        if item_num >= self.li_items.cnt:
            return None
            
        offset = self.li_items.ptr + item_num * PTR.size
        ptr = _STRUCT_SHORT.unpack_from(self._raw, offset)[0]
        if not ptr:
            return None
            
        # Прямое чтение uint значения адреса блока
        bladdr_val = struct_UINT.unpack_from(self._raw, ptr)[0]
        return self.vdo.get_bladdr(bladdr_val)
    
    def find_by_coord(self, srch: COORD) -> BLADDR | None:
        side = self.item_side
        
        # Проверка границ на основе оригинальных свойств COORD
        max_hlatitude = self.origin_hlat + self.qty_y * side
        max_hlongitude = self.origin_hlon + self.qty_x * side
        
        if (srch._hlatitude < self.origin_hlat or srch._hlatitude > max_hlatitude
                or srch._hlongitude < self.origin_hlon or srch._hlongitude > max_hlongitude):
            return None

        # Расчет дельт сетки пространственного индекса
        delta_x = (srch._hlongitude - self.origin_hlon) // side
        delta_y = (srch._hlatitude - self.origin_hlat) // side
        
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
