import struct       # noqa: F401
# from vdo.datatypes import VDO_FILE, BLADDR    # UINT_struct,

#--------------------------------------
from vdo.blocks import block_0x12       # noqa

from vdo.enums import BlockType       # noqa
from vdo.block_base import block_base    # noqa
from vdo.datatypes import BLADDR

from vdo.test_vdo import vdo34ee as vdo


tos_bl = vdo.get_block(0)

# 0571b801
#
bl_addr = BLADDR(struct.pack(">L", 0x0571b801), vdo)
block_packed: block_base    # @ 0571b801 1d 0102 [1D:MAP__10k400]
block_packed = vdo.get_block(bl_addr)
del bl_addr

pass
"""
# noqa

вообще есть и незапакованные, где 2 категории water одна за другой
Max PTR bites: 12
cat 0034:0002 cnt:2     next ptr: 40
shp 0040:0004 cnt:4     next ptr: a4
lin 0000:0000 cnt:0 
poi 0000:0000 cnt:0 
vrt 00A4:029C cnt:668   next ptr: b14
tst 0B14:0003 cnt:3     next ptr: b20
strs from 0b20

begin word = 0500:0900

31.641849N 30.138092E  37.681647N 36.177891E
'2000000*2000000 (671.232km)'
'13E9 F800 0A7A 5000  15E9 F800 0C7A 5000   0001 000A  '

01 00 00 40  
01 00 00 54  
00 00 00 90  
start_vrtx_num = 0
0000 00A4  00 00 00 00   08 9F 0F 9D 05 90 6D DC   00 00 0B 14    16.803252N 3.964447W
start_vrtx_num = 4
0590 00B4  00 00 00 00   50 01 6A E6 C5 0D 41 F1   00 00 0B 18    178.017659S 211.608657E
start_vrtx_num = 145
002F 02E8  E9 D6 50 87   D0 01 B1 B3 85 39 DE F2   00 00 0B 1C   370.764927S 174.935176W
start_vrtx_num = 615
002D 0A40  E7 16 75 1D   50 01 D5 BF 04 D9 22 91   00 00 0B 20    14.641026N 211.613580E
start_vrtx_num = 817
002D 0D68  2F 80 01 4E   00 00 00 00 00 00 00 00   00 00 0B 24  
tail_0571b8 01.bin
SHAPE WATER[1] :0x40
SHAPE WATER[3] :0x54

"""


next = block_packed.head.bladdr.offset + block_packed.head.bladdr.segcnt * block_packed.vdo.segsize    # noqa

pass
'''
# noqa
bmw_a_1d = vf.block(0xE2A2A00) unk: 0x5000900
                01 00 00 3c
                00 00 00 8c
    08 c0 00 a0 40 01 8d 00 3e 8b 4f f4 14 62 9e 01 00 00 08 b0  WATER:[126] 
    08 d3 02 98 40 02 3f f0 3f d4 0f e0 14 3e b2 69 00 00 08 b4  WATER:[43] 
    08 e5 03 44 40 04 2b 13 3e 75 79 94 13 e8 ef 5a 00 00 08 b8  WATER:[267] 
    08 f6 07 70 40 12 e8 aa 3b 0e bb 42 12 26 61 83 00 00 08 bc  WATER:[80] 
    00 00 08 b0 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 c0
                shp 003C:0004 cnt:4
                lin 0000:0000 cnt:0
                poi 0000:0000 cnt:0
                vrt 00A0:0204 cnt:516
                tst 08B0:0004 cnt:4
                str 08c0


                '''


def print_abstract():
    # abstract file info
    abl__abstract: block_0x12 = vdo.get_block(0)

    chouse = 'first'
    # chouse = 'last'

    # [14:MAP__05k200]
    bla_bl = abl__abstract.cd_map[BlockType(0x14)][chouse]
    bl__05k200 = vdo.get_block(bla_bl)      # noqa
    del bla_bl

    # [15:MAP__06k80]
    bla_bl = abl__abstract.cd_map[BlockType(0x15)][chouse]
    bl__06k80 = vdo.get_block(bla_bl)        # noqa
    del bla_bl

    # [16:MAP__07k40]
    bla_bl = abl__abstract.cd_map[BlockType(0x16)][chouse]
    bl__07k40 = vdo.get_block(bla_bl)        # noqa
    del bla_bl

    # [1C:MAP__09k100]
    # bnl: {'first': 017fce 01, 'last': 018008 01, 'idxidx08': 017fc8 01} # noqa
    bla_bl = abl__abstract.cd_map[BlockType(0x1c)][chouse]
    bl__09k100 = vdo.get_block(bla_bl)       # noqa
    del bla_bl

    # [1D:MAP__10k400]
    bla_bl = abl__abstract.cd_map[BlockType(0x1d)][chouse]
    bl__10k400 = vdo.get_block(bla_bl)       # noqa
    del bla_bl

    # [1E:MAP__11k_11]
    bla_bl = abl__abstract.cd_map[BlockType(0x1e)][chouse]
    bl__11k_11 = vdo.get_block(bla_bl)       # noqa
    del bla_bl

    #
    # geo_bl = vdo.get_block(0x1E6EA000)      # ru30 0x1E6EA000

    pass
#===================================
# blnum = UINT_struct.pack(0x03c68a03)    # bl_addr(0x03c68a03); // 0x 1e345000 - 0x1c kaliningrad = 0 # noqa: E501
# blak = BLADDR(blnum, vdo)
# geo_bl = vdo.get_block(blak)  '08 b9 30 00  0b 9a 50 00  09 19 30 00  0b fa 50 00  00 01 00 07'  # noqa


pass

"""
# noqa: E501, W291
print_about_coord(50.9619376, 11.256128, "Nohra");

bl_addr(0x00D65801);	// scale 0
bl_addr(0x00958E01);	// scale 1  0x06; 50.835602 N, 11.059422 E - 51.307457 N, 11.531281 E
/*bl_addr(0x02B54D04);	// scale 2
bl_addr(0x028D2904);	// scale 3

bl_addr(0x02644E04);	// scale 4; 0x03; 50.835602 N, 11.059422 E - 51.307457 N, 11.531281 E
bl_addr(0x03CF9A09);	// scale 5; 0x14; 50.363743 N,  7.756413 E - 52.251175 N, 11.531281 E
bl_addr(0x03965005);	// scale 6; 0x15; 50.363743 N, 10.587563 E - 51.307457 N, 11.531281 E
bl_addr(0x02F6F404);	// scale 7; 0x16; 50.835602 N, 11.059422 E - 51.307457 N, 11.531281 E 
//bl_addr(0x00000000);	// scale 8;   
bl_addr(0x03C4A30B);	// scale 9; 0x1c; 50.363743 N,  9.643848 E - 52.251175 N, 11.531281 E
bl_addr(0x03D33D07);	// scale 10;0x1d; 50.363743 N,  7.756413 E - 52.251175 N, 11.531281 E
//bl_addr(0x00000000);	// scale 11;0x1e;

"""
