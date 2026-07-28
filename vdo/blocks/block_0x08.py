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

from typing import Iterator

from QGIS_VDO.vdo.block_base import block_base
from QGIS_VDO.vdo.datatypes import BLADDR
from QGIS_VDO.vdo.geotypes import COORD


OFFSET_LIST_FOLDEFS = 0x08
OFFSET_FOLDER_SIZE = 0x0c


class block_0x08(block_base):
    """
    0x08    LIST    li_folders  ptr_cnt на BLADDR | 0
    0x0c    DWORD    side    размер приращения _hlat на следующий folder
    0x10    [BLADDR] - массив на папки-индексы гео-блоков
    """

    def __init__(self, bl_addr: BLADDR, origin: COORD, max: COORD):
        """
        Args:
            bl_addr: BLADDR
            origin: COORD - left bottom
            max: COORD - right top
        """
        super().__init__(bl_addr)

        # item - bladdr value map block
        self.li_items = self.list(OFFSET_LIST_FOLDEFS)
        self.item_side = self.uint(OFFSET_FOLDER_SIZE)
        
        self.origin = origin      # "начало" координат, left bottom
        self.qty_y = int((max._hlatitude - origin._hlatitude) / self.item_side)
        self.qty_x = int((max._hlongtitude - origin._hlongtitude) / self.item_side)
        pass

    def items_cnt(self) -> int:
        """
        Возвращает количество уникальных итемов
        """
        finded_early = []
        for offset in range(self.li_items.ptr,
                            self.li_items.ptr + self.li_items.cnt * BLADDR.size,
                            BLADDR.size):
            val = self.uint(offset)
            if not val:
                continue
            if val in finded_early:
                continue
            finded_early.append(val)
        return len(finded_early)

    def get_items(self) -> Iterator[tuple]:
        """
        Генератор валидных итемов с координатами COORD lb, rt
        Returns:
            res = (bla_val, coord_lb, coord_rt): tuple
                bla_val: int - значение bladdr Folders
                coord_lb: COORD left bottom
                coord_rt: COORD right top
        """
        finded_early = []        # ранее ptr уже был найден
        step = BLADDR.size       # единица приращения
        # "координаты" в квадрате ареа
        for x in range(self.qty_x):
            # в файле перебор по вертикали, потом по Х
            for y in range(self.qty_y):
                curr_item = y + x * self.qty_x
                if curr_item >= self.li_items.cnt:
                    # количество итемов может быть меньше квадрата стороны
                    break
                offset = self.li_items.ptr + step * curr_item  # noqa
                bla_val = self.uint(offset)
                if not bla_val:
                    # следующий, если bla_val == 0
                    continue
                # а вообще бывают которые занимают 2 и/или 4 места?
                if bla_val in finded_early:
                    # если попали хоть раз сюда, то надо допереписать по примеру 0х09
                    raise ValueError(finded_early, finded_early)
                # ок, найден новый

                # left bottom
                # Долгота (Lng) E/W - x
                lon = self.origin._hlongtitude + x * self.item_side
                # Широта (Lat) N/S - y
                lat = self.origin._hlatitude + y * self.item_side
                coord_lb = COORD(lon, lat)

                # right top
                # if (lat1 := (lat0 + self.delta_degree)) > 85:
                #     lat1 = 85
                lat += self.item_side
                lon += self.item_side
                coord_rt = COORD(lon, lat)

                res = (bla_val, coord_lb, coord_rt)
                yield res
        pass

    def find_by_coord(self, srch_point: COORD) -> BLADDR | None:
        """
        Поиск idx блока, в который попадают координаты, или None
        """

        
# All block tests in block_0x07
