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

# from QGIS_VDO.vdo.consts import struct_UINT  # struct_WORD  #
from QGIS_VDO.vdo.block_base import block_base
from QGIS_VDO.vdo.datatypes import BLADDR       # BYTESTRUCT
from QGIS_VDO.vdo.geotypes import COORD, hex2COORD


OFFSET_LIST_FOLDEFS = 0x08
OFFSET_FOLDER_SIZE = 0x0c


class block_0x08(block_base):
    """
    """
    def __init__(self, bl_addr: BLADDR) -> None:
        super().__init__(bl_addr)
        self.side = self.uint(OFFSET_FOLDER_SIZE)
        self.li_folders = self.list(OFFSET_LIST_FOLDEFS)
        self.qty_side = int(self.li_folders.cnt ** 0.5)      # sqrt of overall qty

    def folders(self, start: COORD):
        """
        Генератор
        Returns:
            Folders с координатами углов
        """
        for (bladdr_fldr, x, y) in self._get_raw_content():
            #
            lb_x = start._hlon + int(x * self.side)
            lb_y = start._hlat + int(y * self.side)
            rt_x = lb_x + self.side
            rt_y = lb_y + self.side
            point_lb = hex2COORD(lb_x, lb_y)
            point_rt = hex2COORD(rt_x, rt_y)
            yield (bladdr_fldr, point_lb, point_rt)
        
    def _get_raw_content(self):
        """
        Генератор содержимого
        Returns:
            (bladdr_folder, x, y) - x, y - координаты в квадрате
        """
        x = 0
        y = 0
        for offset in range(self.li_folders.ptr,
                            self.li_folders.ptr + BLADDR.size * self.li_folders.cnt,
                            BLADDR.size):
            ffolder: BLADDR = self.bladdr(offset)
            if x >= self.qty_side:
                #
                x = 0
                y += 1
            res = (ffolder, x, y)
            x += 1
            if ffolder.isZero:
                # пустые folders - значит информации нет
                continue
            yield res


# All block tests in block_0x07
