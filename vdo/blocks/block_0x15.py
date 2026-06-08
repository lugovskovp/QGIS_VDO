"""
MAP__06k80 = 0x15  	# scale 6   15_MAP_POLI_6_k80	//[6] 6(7:80h)-0x15

"""
from vdo.block_basegeo import block_basegeo
from vdo.datatypes import BLADDR


class block_0x15(block_basegeo):
    """

    """
    def __init__(self, bladdr: BLADDR) -> None:
        super().__init__(bladdr)
