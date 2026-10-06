"""
MAP__05k200 = 0x14  # scale 5   14_MAP_POLI_5_k200	//[5] 5(9:200h)-0x14
блок масштаба sc5.
"""
from QGIS_VDO.vdo.block_basegeo import block_basegeo
from QGIS_VDO.vdo.datatypes import BLADDR


class block_0x14(block_basegeo):
    """

    """
    def __init__(self, bladdr: BLADDR) -> None:
        super().__init__(bladdr)


"""
line = p_str_name + ptr2firstObjVertex + id + ptr_linesign + ptr2poi + ptr2tstr + shrtEnd
ptr_linesign - multilang, ссылка на первый TSTR с наименованием (=p_str_name)
ptr2poi - 1 байт, *10 похоже на разрешенную скорость на дороге
shrtEnd - код страны, принадлежность дороги
"""
