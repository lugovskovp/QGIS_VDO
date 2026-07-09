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
from QGIS_VDO.vdo.datatypes import BLADDR       # BYTESTRUCT,


OFFSET_LIST_FOLDEFS = 0x08
OFFSET_FOLDER_SIZE = 0x0c


class block_0x08(block_base):
    """
    """
    def __init__(self, bl_addr: BLADDR) -> None:
        super().__init__(bl_addr)
        # struct_UINT.unpack(self.read(OFFSET_FOLDER_SIZE, 4))[0]
        self.side = self.uint(OFFSET_FOLDER_SIZE)
        self.li_folders = self.list(OFFSET_LIST_FOLDEFS)
        
