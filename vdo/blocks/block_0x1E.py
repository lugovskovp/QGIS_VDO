"""
    MAP__11k_11 = 0x1e  # scale 11  1e_MAP_POLI_11			//[11] b(b:666h)-0x1e

"""
from QGIS_VDO.vdo.block_basegeo import block_basegeo
from QGIS_VDO.vdo.datatypes import BLADDR


class block_0x1E(block_basegeo):
    """

    """
    def __init__(self, bladdr: BLADDR) -> None:
        super().__init__(bladdr)


"""
07158906 001e 0000
p_poi = 0

GEO_LINES
ru30  0x03c68a03
последний элемент - значения сгруппированы в категориях по возрастанию, и, кажется, по странам в хвостовом = 00F5

"""
