"""
MAP__05k200 = 0x14  # scale 5   14_MAP_POLI_5_k200	//[5] 5(9:200h)-0x14

"""
from vdo.block_basegeo import block_basegeo
from vdo.datatypes import BLADDR


class block_0x14(block_basegeo):
    """

    """
    def __init__(self, bladdr: BLADDR) -> None:
        super().__init__(bladdr)
