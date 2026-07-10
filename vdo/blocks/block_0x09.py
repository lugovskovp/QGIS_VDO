"""
FOLDER_MAPS = 0x09		# map folders 0x09.

Индекс гео-блоков
"""

from QGIS_VDO.vdo.datatypes import BLADDR, PTR
from QGIS_VDO.vdo.block_base import block_base


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
        self.side = self.uint(OFFSET_FOLDER_SIZE)
        self.li_p_geo = self.list(OFFSET_LIST_PTR)
        self.li_valid = self.list(OFFSET_GEOBLOCKS)
        self.qty_side = int(self.li_p_geo.cnt ** 0.5)      # sqrt of overall qty

    def _get_ptr_by_xy(self, coord, x, y) -> PTR:
        """
        Returns:
            res: PTR - ptr by x, y in block space
        """
        res = 0
        return res

    def _get_raw_content(self):
        """
        Генератор содержимого
        Returns:
            (bladdr_folder, x, y) - x, y - координаты в квадрате
        """
        x = 0
        y = 0
        for offset in range(self.li_folders.ptr,
                            self.li_folders.ptr + PTR.size * self.li_folders.cnt,
                            PTR.size):
            ptr_2geoblock: PTR = self.ptr(offset)
            if x >= self.qty_side:
                # следующая строка.
                x = 0
                y += 1
            res = (ptr_2geoblock, x, y)
            x += 1
            if ptr_2geoblock.isZero:
                # пустые ptr - значит информации нет
                continue
            yield res


# All block tests in block_0x07
