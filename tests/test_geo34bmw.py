import struct       # noqa: F401
from vdo.datatypes import VDO_FILE, BLADDR, UINT_struct    # noqa
from vdo.block_base import block_base        # noqa
from vdo.datatypes import BLADDR        # noqa

from vdo.blocks import block_0x12       # noqa
from vdo.enums import BlockType       # noqa

from vdo.test_vdo import vdobmv as vdo

#--------------------------------------

tos_bl = vdo.get_block(0)

'''bmw_a_1d = vf.block(0xE2A2A00)  0x07154f02 '''
bla_bl = BLADDR(vdo.read(0xE2A2A00, 4), vdo)    # @ 07151504 1d 0105 [1D:MAP__10k400] 0500 0900 распаковкаОК  # noqa
bla_bl = BLADDR(UINT_struct.pack(0x07154f02), vdo)    # //1Dp3  =2/4/0/11a/0/3  'tail_07154f 02.bin'  # noqa
# bla_bl = BLADDR(UINT_struct.pack(0x07152605), vdo)    # 07152605 -1dp6 =2/6/0/276/0/6  # noqa
block_packed: block_base
block_packed = vdo.get_block(bla_bl)

next = block_packed.head.bladdr.offset + block_packed.head.bladdr.segcnt * block_packed.vdo.segsize    # noqa
bla_bl = BLADDR(vdo.read(next, 4), vdo)  # next off=0xe2a320 bl=0x07151903 unk= 0500 0900        # noqa
block_packed2 = vdo.get_block(bla_bl)   # 67.880639N 125.307310E  76.940337N 134.367008E
pass

'''
# noqa
c:\DIY\VDO\db_src\bmw34-2010\DB\DB_0
07154f 02  BlockType.MAP__10k400: 0x1d

Max PTR bites: 11
cat 0034:0002 cnt:2     next ptr: 0040
shp 0040:0004 cnt:4     next ptr: 00A4
lin 0000:0000 cnt:0 
poi 0000:0000 cnt:0 
vrt 00A4:011A cnt:282   next ptr: 050C
tst 050C:0003 cnt:3     next ptr: 0518
strs from 0518
begin word = 0500:0900
Map_hex: 42 6D 90 00 16 7A 50 00  45 6D 90 00 19 7A 50 00   00 01 00 0A  

01 00 00 40  
01 00 00 54  
00 00 00 90  

0000 00A4 400d9206  387EEDF5 1AF37D90  0000 050C    start_vrtx_num = 0
0518 00B4 400cd65c  3F579717 18395941  0000 050C    start_vrtx_num = 4
0518 04E8 400cd65c  3F579717 18395941  0000 0510    start_vrtx_num = 273
0518 04F4 400cd65c  3F579717 18395941  0000 0514    start_vrtx_num = 276
0000 050C 00000000  00000000 00000000  0000 0518    start_vrtx_num = 282
tail_07154f 02.bin
SHAPE WATER[1] :0x40
SHAPE WATER[3] :0x54
                '''


# [[04:bl_0x4]]
# chouse = 'last'
# chouse = 'first'
# bla_bl = tos_bl.cd_map[BlockType(0x04)][chouse]
# bl__04 = vdo.get_block(bla_bl)
# print(bl__04.hex)

# abstract file info
abl__abstract: block_0x12 = vdo.get_block(0)

chouse = 'first'
# chouse = 'last'


# [14:MAP__05k200]
bla_bl = abl__abstract.cd_map[BlockType(0x14)][chouse]
bl__05k200 = vdo.get_block(bla_bl)
del bla_bl

# [15:MAP__06k80]
bla_bl = abl__abstract.cd_map[BlockType(0x15)][chouse]
bl__06k80 = vdo.get_block(bla_bl)
del bla_bl

# [16:MAP__07k40]
bla_bl = abl__abstract.cd_map[BlockType(0x16)][chouse]
bl__07k40 = vdo.get_block(bla_bl)
del bla_bl

# [1C:MAP__09k100]
# bnl: {'first': 017fce 01, 'last': 018008 01, 'idxidx08': 017fc8 01} # noqa
bla_bl = abl__abstract.cd_map[BlockType(0x1c)][chouse]
bl__09k100 = vdo.get_block(bla_bl)
del bla_bl

# [1D:MAP__10k400]
bla_bl = abl__abstract.cd_map[BlockType(0x1d)][chouse]
bl__10k400 = vdo.get_block(bla_bl)
del bla_bl

# [1E:MAP__11k_11]
bla_bl = abl__abstract.cd_map[BlockType(0x1e)][chouse]
bl__11k_11 = vdo.get_block(bla_bl)
del bla_bl


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
