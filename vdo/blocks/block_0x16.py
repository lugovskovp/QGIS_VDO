"""
 MAP__07k40 = 0x16  	# scale 7   16_MAP_POLI_7_k40	//[7] 7(6:40h)-0x16

"""
from QGIS_VDO.vdo.block_basegeo import block_basegeo
from QGIS_VDO.vdo.datatypes import BLADDR


class block_0x16(block_basegeo):
    """

    """
    def __init__(self, bladdr: BLADDR) -> None:
        super().__init__(bladdr)
