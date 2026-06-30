"""
    MAP__10k400 = 0x1d  # scale 10  1d_MAP_POLI_10_k400 //[10] a(a:400h)-0x1d

"""
from QGIS_VDO.vdo.block_basegeo import block_basegeo
from QGIS_VDO.vdo.datatypes import BLADDR


class block_0x1D(block_basegeo):
    """

    """
    def __init__(self, bladdr: BLADDR) -> None:
        super().__init__(bladdr)
