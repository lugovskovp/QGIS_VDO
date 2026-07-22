"""
SCALE_ALMANAC = 0x08    # set of map folders 0x9.

Индекс папок с гео-блоками.
Описывает квадрат (в SCALE), количество итемов - папок (block_0x9),
дельта координат между папками, сам список папок

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
from QGIS_VDO.vdo.geotypes import COORD, hex2COORD


OFFSET_LIST_FOLDEFS = 0x08
OFFSET_FOLDER_SIZE = 0x0c


class block_0x08(block_base):
    """
    0x08    LIST    li_folders  ptr_cnt на BLADDR | 0
    0x0c    DWORD    side    размер приращения _hlat на следующий folder
    0x10    [BLADDR] - массив на папки-индексы гео-блоков
    """
    def __init__(self, bl_addr: BLADDR) -> None:
        super().__init__(bl_addr)
        # item - one valid folder maps
        self.li_items = self.list(OFFSET_LIST_FOLDEFS)
        self.item_side = self.uint(OFFSET_FOLDER_SIZE)
        self.qty_items_on_side = int(self.li_items.cnt ** 0.5)   # sqrt of overall qty
        self.area_side = self.item_side * self.qty_items_on_side

    def items(self, start: COORD):
        """
        Генератор
        Returns:
            (bladdr_fldr, point_lb, point_rt) Folders с координатами углов
        """
        start_lb_x = start._hlon    # 0xa800  x = 1
        start_lb_y = start._hlat    # 0xf5cd6500  y = 1
        for (bladdr_fldr, x, y) in self._get_raw_content():
            #
            lb_x = start_lb_x + x * self.item_side  # noqa 0xa800 + 1 * 0x14000000 = 0x1400a800
            lb_y = start_lb_y + y * self.item_side  # noqa 0xf5cd6500 + 1 * 0x28000000 = 0x11dcd6500
            rt_x = lb_x + self.item_side
            rt_y = lb_y + self.item_side
            point_lb = hex2COORD(lb_x, lb_y)
            point_rt = hex2COORD(rt_x, rt_y)
            yield (bladdr_fldr, point_lb, point_rt)
        
    def _get_raw_content(self):
        """
        Генератор содержимого
        Returns:
            (bladdr_folder, x, y) - x, y - координаты в квадрате
        """
        # "координаты" в квадрате ареа
        x = 0
        y = 0
        for offset in range(self.li_items.ptr,
                            self.li_items.ptr + BLADDR.size * self.li_items.cnt,
                            BLADDR.size):
            ffolder: BLADDR = self.bladdr(offset)
            # приращение идёт по вертикали, по y
            if y >= self.qty_items_on_side:
                # следующий столбец
                y = 0
                x += 1
            res = (ffolder, x, y)
            y += 1
            if ffolder.isZero:
                # пустые folders - значит информации нет
                continue
            yield res


# All block tests in block_0x07
