"""

# noqa:
SCALES [2, 3, 4] - (types 01, 02, 03) POI, по возрастанию масштаба [4, 3, 2]
PREAMBULA_BLOCK = 0x74 - размер заголовка
BL_HEAD head; // заголовок
// local size-offset для LIST
    local ushort size <format=hex, hidden=true> = head.addr.size * 0x800; // size of this block  
    local uint   offset < hidden=true> = head.addr.offset;     // absolute block offset
    
	LIST s0_a08;       //to 0x74, cnt=2, 10bpi byte per item
    LIST s1_a0с;    // 88 02, 10bpi
    LIST s2_a10;    //9c 02, 10bpi
    LIST s3_a14;    //b0 07, +1, 4bpi
    LIST s4_a18;    //d0 b3, 180bpi
    LIST s5_a1с;    //1318 84, 8bpi
    
    LIST s6_a20;    //1738 11
    LIST s7_a24;    //1848 57
    LIST s8_a28;    //1a84 100
    LIST s9_a2c;    //1a54 06
    
    LIST s10_a30;   //1e84 09
    LIST s11_a34;   //1ecc 00
    LIST s12_a38;   //1ecc 00
    LIST s13_a3c;   //1ecc 00
    
    CONST_I zero1(0);
    GEO_AREA area;
    CONST_I zero2(0);
    FAR_LIST type02_1;
    CONST_I unk1(0x20c49b);
    CONST_I unk2(0x20c49b);
    CONST_I unk3(0x20c49b);
    CONST_I zero3(0);
    CONST_I thou(0x1000);
	
}BT_0x03 <read=Read_BT_0x03>;

0x00 - like block.
"""


from QGIS_VDO.vdo.block_base import block_base
from QGIS_VDO.vdo.datatypes import BLADDR


class block_0x03(block_base):
    """

    """
    def __init__(self, bladdr: BLADDR) -> None:
        super().__init__(bladdr)
