"""
FOLDER_MAPS = 0x09		# map folders 0x09.

Индекс гео-блоков
"""

from QGIS_VDO.vdo.datatypes import BLADDR, PTR
from QGIS_VDO.vdo.block_base import block_base
from QGIS_VDO.vdo.geotypes import COORD, hex2COORD


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
    def __init__(self, bl_addr: BLADDR) -> None:
        super().__init__(bl_addr)
        # item - one ptr 2 map block
        self.li_items = self.list(OFFSET_LIST_PTR)
        self.li_valid = self.list(OFFSET_GEOBLOCKS)
        self.item_side = self.uint(OFFSET_FOLDER_SIZE)
        self.qty_items_on_side = int(self.li_items.cnt ** 0.5)   # sqrt of overall qty
        self.area_side = self.item_side * self.qty_items_on_side

    def items(self, start: COORD):
        """
        Генератор, все валидные блоки с координатами
        Args:
            start: COORD - left bottom area coord
        Returns:
            (bladdr_fldr, point_lb, point_rt) Folders с координатами углов
        """
        start_lb_x = start._hlon
        start_lb_y = start._hlat
        for (bladdr_geo, x, y) in self._get_raw_content():
            #
            lb_x = start_lb_x + x * self.item_side
            lb_y = start_lb_y + y * self.item_side
            rt_x = lb_x + self.item_side
            rt_y = lb_y + self.item_side
            point_lb = hex2COORD(lb_x, lb_y)
            point_rt = hex2COORD(rt_x, rt_y)
            yield (bladdr_geo, point_lb, point_rt)

    def _get_raw_content(self):
        """
        Генератор содержимого

        Returns:
            (bladdr_folder, y, x) - x, y - координаты в квадрате
        """
        # "координаты" в квадрате ареа
        x = 0
        y = 0
        finded_early = []
        for offset in range(self.li_items.ptr,
                            self.li_items.ptr + PTR.size * self.li_items.cnt,
                            PTR.size):
            ptr_2geoblock = self.ushort(offset)   # : PTR = self.ptr(offset)
            # а вот приращение идёт по вертикали, по y
            if y >= self.qty_items_on_side:
                # следующий столбец
                y = 0
                x += 1
            curr_y = y
            y += 1
            if not ptr_2geoblock:
                # пустые ptr - значит информации нет
                continue
            bladdr_geo = self.bladdr(self.read(ptr_2geoblock, BLADDR.size))

            # а вообще бывают которые занимают 2 и/или 4 места?
            if bladdr_geo in finded_early:
                raise ValueError(finded_early, finded_early)
            finded_early.append(bladdr_geo)

            yield (bladdr_geo, x, curr_y)


# All block tests in block_0x07
