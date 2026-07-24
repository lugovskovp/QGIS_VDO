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

from QGIS_VDO.vdo.block_base import block_base
from QGIS_VDO.vdo.datatypes import BLADDR       # BYTESTRUCT
from QGIS_VDO.vdo.geotypes import COORD, MULCOORD   # , hex2COORD


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
        self.li_items = self.list(OFFSET_LIST_FOLDEFS)
        self.item_side = self.uint(OFFSET_FOLDER_SIZE)
        self.delta_degree = self.item_side / MULCOORD    # приращение градусов
        self.origin = origin      # "начало" координат, left bottom
        # self.bound_max = max
        self.qty_y = int((max._hlatitude - origin._hlatitude) / self.item_side)
        self.qty_x = int((max._hlongtitude - origin._hlongtitude) / self.item_side)
        pass

    def get_items(self) -> tuple:
        """
        Генератор валидных итемов с координатами lb, rt
        Returns:
            res = (bla_val, lat0, lon0, lat1, lon1): tuple
            bla_val: int - значение bladdr Folders
            lat, lon - значения координат
            _0, _1: градусы с координатами углов
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
                lat0 = self.origin.lat + y * self.delta_degree  # Широта (Lat) N/S - y
                lon0 = self.origin.lon + x * self.delta_degree  # Долгота (Lng) E/W - x
                # right top
                # if (lat1 := (lat0 + self.delta_degree)) > 85:
                #     lat1 = 85
                lat1 = lat0 + self.delta_degree
                lon1 = lon0 + self.delta_degree
                res = (bla_val, lat0, lon0, lat1, lon1)
                # res = (f"{bla_val:X}", lat0, lon0, lat1, lon1)
                yield res
        pass

    # def items(self, origin: COORD):
    #     """
    #     Генератор
    #     Returns:
    #         (bladdr_fldr, point_lb, point_rt) Folders с координатами углов
    #     """
    #     # для ускорения, расчет координат не через COORD
    #     origin_lon = origin.lon     # E/W - y
    #     origin_lat = origin.lat     # N/S - x
    #     for (bladdr_almanac_val, x_lb, y_lb, x_rt, y_rt) in self._get_raw_content():
    #         # (X, Y) -> (Долгота (Long) E/W, Широта (Lat) N/S)
    #         lat_lb = origin_lat + y_lb * self.atom_delta
    #         lon_lb = origin_lon + x_lb * self.atom_delta
    #         lat_rt = origin_lat + y_rt * self.atom_delta
    #         lon_rt = origin_lon + x_rt * self.atom_delta
    #         if lat_rt > 90:
    #             lat_rt = 85
    #         if lat_lb > 90:
    #             lat_lb = 85
    #         point_lb = (lat_lb, lon_lb)
    #         point_rt = (lat_rt, lon_rt)
    #         yield (bladdr_almanac_val, point_lb, point_rt)
       
    # def _get_raw_content(self):
    #     """
    #     Генератор содержимого
    #     Returns:
    #         (bladdr_folder_val, x_lb, y_lb, x_tr, y_rt) -
    #             bladdr_folder_val: int value bladdr
    #             _lb, _rt - left bottom, right top
    #             x, y: int - координаты в альманахе
    #     """
    #     finded_early = []        # ранее ptr уже был найден
    #     atom_delta = BLADDR.size       # единица приращения
    #     # "координаты" в квадрате ареа
    #     for x in range(self.qty_items_on_side):
    #         for y in range(self.qty_items_on_side):
    #             # в файле перебор по вертикали, потом по Х
    #             offset = self.li_items.ptr + atom_delta * (y + x * self.qty_items_on_side)  # noqa
    #             bla_val = self.uint(offset)
    #             if not bla_val:
    #                 # следующий, если bla_val == 0
    #                 continue
    #             # а вообще бывают которые занимают 2 и/или 4 места?
    #             if bla_val in finded_early:
    #                 # если попали хоть раз сюда, то надо допереписать по примеру 0х09
    #                 raise ValueError(finded_early, finded_early)
    #             # ок, найден новый
    #             finded_early.append(bla_val)
    #             res = (bla_val, x, y, x + 1, y + 1)
    #             yield res

# All block tests in block_0x07
