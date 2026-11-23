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
bmw:
ptr2poi - 1 байт, *10 похоже на разрешенную скорость на дороге
shrtEnd - код страны, принадлежность дороги

ru30:
border, river major, road highway
ptr2poi - 1 байт, *10 похоже на разрешенную скорость на дороге (7, c, e)
03d049 04 163426  shrtEnd = 0x83D0/33744 у дороги А116, 30 вершин, длинна  163422,182 м (33744 * 4 =13496)

wkt_geom	variant	render_order	name	name2	id	block	c_p_line_sign	c_b_or_c	c_pp_str_name	c_38_or_0b_country
LineString ROAD_HIGHWAY	104	A116	0 0x10:[noLang]: a116	163426	03d049 04 163426	175C	0000	1830	83D0

shrtEnd - код страны, принадлежность дороги

ee:
border, river major =0, =0
roadhighway =[0,4,7,b,c,d,e], = countrycodes



https://github.com/fdemusso/OpenCarin/issues/1
0x14, 0x15, 0x16: T[0x3A], T[0x3B], T[0x3C], T[0x3D], T[0x3F].
S0 - categories
S1 - poligons
S2 - polilines
S3 -
val      bnl ru30 -
T[0x3A] 0x14 -
T[0x3B] 0x04 -
T[0x3C] 0x10 -
T[0x3D] 0x34 -
T[0x3F] 0x18 -
"""
