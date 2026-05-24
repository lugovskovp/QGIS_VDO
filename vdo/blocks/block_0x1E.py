"""
    MAP__11k_11 = 0x1e  # scale 11  1e_MAP_POLI_11			//[11] b(b:666h)-0x1e

"""
from vdo.block_basegeo import block_basegeo
from vdo.datatypes import BLADDR


class block_0x1E(block_basegeo):
    """

    """
    def __init__(self, bladdr: BLADDR) -> None:
        super().__init__(bladdr)
