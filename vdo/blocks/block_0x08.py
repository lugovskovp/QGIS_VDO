"""
SCALE_ALMANAC = 0x08    # set of map folders 0x9.

Индекс папок с гео-блоками.
Описывает квадрат (в SCALE), количество итемов - папок (block_0x9),
дельта координат между папками, сам список папок

ALARM! количество items - не всегда квадрат стороны!

block_0x08

//header start
    BL_HEADER       block;
// header end, last = 0Ch -1
   DWORD folder_side_size <format=hex, fgcolor=cYellow,bgcolor=cDkGreen>;
   //was side_one_square_almanac
    
   FOLDER_MAPS folder[block.data.Cnt] <optimize=false>;

}BLOCK_TYPE_0x08

"""

from typing import Iterator, Tuple

from QGIS_VDO.vdo.block_base import block_base
from QGIS_VDO.vdo.blocks import block_0x09
from QGIS_VDO.vdo.datatypes import BLADDR
from QGIS_VDO.vdo.geotypes import COORD  # , MULCOORD
from QGIS_VDO.vdo.consts import struct_UINT, MOST_SIGNIFICANT_BIT


OFFSET_LIST_FOLDEFS = 0x08
OFFSET_FOLDER_SIZE = 0x0c


class block_0x08(block_base):
    """
    0x08    LIST     li_folders  ptr_cnt на BLADDR | 0
    0x0c    DWORD    side        размер приращения _hlat на следующий folder
    0x10    [BLADDR]             массив на папки-индексы гео-блоков
    """

    __slots__ = (
        'li_items',
        'item_side',
        'origin_hlon',
        'origin_hlat',
        'qty_y',
        'qty_x'
    )

    def __init__(self, bl_addr: BLADDR, origin: COORD, max: COORD) -> None:
        super().__init__(bl_addr)

        self.li_items = self.read_list(OFFSET_LIST_FOLDEFS)
        self.item_side = self.uint(OFFSET_FOLDER_SIZE)
        
        # Сохраняем сырые uint32 значения для корректной CarInDB-математики
        self.origin_hlon = origin._hlon - 0x100000000 if origin._hlon & MOST_SIGNIFICANT_BIT else origin._hlon
        self.origin_hlat = origin._hlat - 0x100000000 if origin._hlat & MOST_SIGNIFICANT_BIT else origin._hlat
        
        # Вычисляем размеры сетки
        self.qty_y = (max._hlatitude - origin._hlatitude) // self.item_side
        self.qty_x = (max._hlongitude - origin._hlongitude) // self.item_side

    def items_cnt(self) -> int:
        """Возвращает количество уникальных итемов за O(N) через хеш-сет."""
        finded_early = set()
        raw_buffer = self._raw
        step = BLADDR.size
        start_ptr = self.li_items.ptr
        end_ptr = start_ptr + self.li_items.cnt * step

        for offset in range(start_ptr, end_ptr, step):
            val = struct_UINT.unpack_from(raw_buffer, offset)[0]
            if val:
                finded_early.add(val)
                
        return len(finded_early)

    def get_items(self) -> Iterator[Tuple[int, COORD, COORD]]:
        """Генератор валидных итемов с оригинальными объектами COORD.
        
        Возвращает:
            tuple: (bla_val, coord_lb, coord_rt)
        """
        finded_early = set()
        step = BLADDR.size
        base_ptr = self.li_items.ptr
        total_cnt = self.li_items.cnt
        q_y = self.qty_y
        q_x = self.qty_x
        side = self.item_side
        raw_buffer = self._raw

        for x in range(q_x):
            # Ваша оригинальная индексация по qty_x
            x_offset = x * q_x
            
            # Рассчитываем долготу (X) с учетом uint32 специфики
            hex_lon = (self.origin_hlon + x * side) & 0xFFFFFFFF
            hex_lon_next = (hex_lon + side) & 0xFFFFFFFF

            for y in range(q_y):
                curr_item = y + x_offset
                if curr_item >= total_cnt:
                    break

                offset = base_ptr + step * curr_item
                bla_val = struct_UINT.unpack_from(raw_buffer, offset)[0]
                
                if not bla_val:
                    continue
                    
                if bla_val in finded_early:
                    raise ValueError(f"Дубликат bla_val {bla_val} обнаружен в сетке папок")
                
                finded_early.add(bla_val)

                # Рассчитываем широту (Y) с маской 0xFFFFFFFF для имитации Си-переполнения
                hex_lat = (self.origin_hlat + y * side) & 0xFFFFFFFF
                hex_lat_next = (hex_lat + side) & 0xFFFFFFFF

                # Создаем тяжелые COORD только для валидных элементов (после всех continue)
                coord_lb = COORD(hex_lon, hex_lat)
                coord_rt = COORD(hex_lon_next, hex_lat_next)

                yield (bla_val, coord_lb, coord_rt)

    def find_by_coord(self, srch: COORD) -> BLADDR | None:
        """Поиск подблока карты, в который попадают координаты."""
        side = self.item_side
        
        max_hlat = (self.origin_hlat + self.qty_y * side)
        max_hlat = max_hlat - 0x100000000 if max_hlat & MOST_SIGNIFICANT_BIT else max_hlat   # & 0xFFFFFFFF
        max_hlon = (self.origin_hlon + self.qty_x * side)
        max_hlon = max_hlon - 0x100000000 if max_hlon & MOST_SIGNIFICANT_BIT else max_hlon

        # В геоинформационных системах (ГИС) общепринятый стандарт для ячеек регулярной сетки (растра или индекса)
        #  — это полуоткрытые интервалы: [left, right) и [bottom, top). То есть левая/нижняя граница включается
        #  в ячейку, а правая/верхняя — принадлежит уже следующей.
        if (srch._hlatitude < self.origin_hlat or srch._hlatitude >= max_hlat
                or srch._hlongitude < self.origin_hlon or srch._hlongitude >= max_hlon):
            return None

        delta_x = (srch._hlongitude - self.origin_hlon) // side
        delta_y = (srch._hlatitude - self.origin_hlat) // side
        
        bladdr_folder_maps = self.get_xy_item(delta_x, delta_y)
        if bladdr_folder_maps is None:
            return None
            
        lb, rt = self.get_xy_area(delta_x, delta_y)
        folder_maps: block_0x09 = self.vdo.get_block(bladdr_folder_maps, lb, rt)
        return folder_maps.find_by_coord(srch)

    def get_xy_area(self, x: int, y: int) -> Tuple[COORD, COORD]:
        """Возвращает оригинальные объекты COORD lb, rt для ячейки x, y."""
        side = self.item_side
        hex_lon = (self.origin_hlon + x * side)
        hex_lat = (self.origin_hlat + y * side)

        hex_lat = hex_lat - 0x100000000 if hex_lat & MOST_SIGNIFICANT_BIT else hex_lat   # & 0xFFFFFFFF
        hex_lon = hex_lon - 0x100000000 if hex_lon & MOST_SIGNIFICANT_BIT else hex_lon
        
        return COORD(hex_lon, hex_lat), COORD((hex_lon + side) & 0xFFFFFFFF, (hex_lat + side) & 0xFFFFFFFF)

    def get_xy_item(self, x: int, y: int) -> BLADDR | None:
        """Вернуть адрес папки по индексам сетки."""
        item_num = x + y * self.qty_y
        if item_num >= self.li_items.cnt:
            return None
            
        offset = self.li_items.ptr + item_num * BLADDR.size
        bladdr_val = struct_UINT.unpack_from(self._raw, offset)[0]
        
        if not bladdr_val:
            return None
            
        res = self.vdo.get_bladdr(bladdr_val)
        return None if res.isZero else res

        
# All block tests in block_0x07
#05154A03 0008 00 00 [08:SCALE_ALMANAC]
