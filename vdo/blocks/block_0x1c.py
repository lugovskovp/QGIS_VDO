"""
    MAP__09k100 = 0x1c  # scale 9   1c_MAP_POLI_9_k100	//[9]  9(8:100h)-0x1c

"""
from vdo.block_basegeo import block_basegeo
from vdo.datatypes import BLADDR


class block_0x1C(block_basegeo):
    """

    """
    def __init__(self, bladdr: BLADDR) -> None:
        super().__init__(bladdr)
