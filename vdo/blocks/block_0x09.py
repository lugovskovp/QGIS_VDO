"""
FOLDER_MAPS = 0x09		# map folders 0x09.

Индекс гео-блоков
"""

from QGIS_VDO.vdo.datatypes import BLADDR, PTR
from QGIS_VDO.vdo.block_base import block_base
from QGIS_VDO.vdo.geotypes import COORD, MULCOORD   # , hex2COORD


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
        self.atom_delta = self.item_side / MULCOORD    # приращение градусов

    def items(self, origin: COORD):
        """
        Генератор, все валидные блоки с координатами
        Args:
            origin: COORD - left bottom area coordinate
        Returns:
            (bladdr_map_val, point_lb, point_rt) val bl_map с координатами углов
                point_lb - left bottom (lon, lat)
                point_rt right top (lon, lat)
        """
        # для ускорения, расчет координат не через COORD
        origin_lon = origin.lon     # E/W -y
        origin_lat = origin.lat     # N/S -x
        for (bladdr_map_val, y_lb, x_lb, y_rt, x_rt) in self._get_raw_content():
            lat_lb = origin_lat + x_lb * self.atom_delta
            lon_lb = origin_lon + y_lb * self.atom_delta
            lat_rt = origin_lat + x_rt * self.atom_delta
            lon_rt = origin_lon + y_rt * self.atom_delta
            point_lb = (lat_lb, lon_lb)
            point_rt = (lat_rt, lon_rt)
            yield (bladdr_map_val, point_lb, point_rt)

    def _get_raw_content(self):
        """
        Генератор содержимого
        Returns:
            (bladdr_map_val, x_lb, y_lb, x_tr, y_rt) -
                bladdr_map_val: int value bladdr
                x, y: int - координаты в альманахе
        """
        finded_early = []        # ранее ptr уже был найден
        atom_delta = PTR.size       # единица приращения
        # "координаты" в квадрате альманаха
        for x in range(self.qty_items_on_side):
            for y in range(self.qty_items_on_side):
                offset = self.li_items.ptr + atom_delta * (x + y * self.qty_items_on_side)  # noqa
                ptr_val = self.ushort(offset)
                if not ptr_val or ptr_val in finded_early:
                    # следующий, если ptr == 0 или ранее был найден
                    continue
                # finded new ptr
                finded_early.append(ptr_val)
                size_X = 0
                # calculate X side size
                for i in range(x, self.qty_items_on_side):
                    off_next = offset + atom_delta * size_X
                    ptr_next_val = self.ushort(off_next)
                    if ptr_next_val != ptr_val:
                        break
                    size_X += 1
                # Calculate Y side size
                size_Y = 0
                for i in range(y, self.qty_items_on_side):
                    off_next = offset + atom_delta * size_Y * self.qty_items_on_side
                    ptr_next_val = self.ushort(off_next)
                    if ptr_next_val != ptr_val:
                        break
                    size_Y += 1
                # read bladdr_value
                bladdr_map_val = self.uint(ptr_val)
                res = (bladdr_map_val, y, x, y + size_Y, x + size_X)
                yield res

# All block tests in block_0x07
