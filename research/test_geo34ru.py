import struct       # noqa: F401
from vdo.datatypes import VDO_FILE, BLADDR    # struct_UINT,    # noqa
from vdo.block_base import block_base        # noqa
# from vdo.datatypes import BLADDR
from vdo.consts import struct_UINT        # noqa

from vdo.blocks import block_0x12       # noqa
from vdo.enums import BlockType       # noqa

from vdo.test_vdo import vdoRu as vdo

#--------------------------------------

tos_bl = vdo.get_block(0)

''' '''
block_packed: block_base
bla_bl = BLADDR(struct_UINT.pack(0x08a06b02), vdo)  # 08a06b02 ru34 packed (mar mediterráneo? andor oceano atlântico )   # noqa
# bla_bl = BLADDR(struct_UINT.pack(0x06cc8b05), vdo)  # //16p7 =2/9/1/2b9/0/0a + oceano atlântico id= 4005d71   # noqa
# bla_bl = BLADDR(struct_UINT.pack(0x094fa401), vdo)  # lzw
bla_bl = BLADDR(struct_UINT.pack(0x07bbaf08), vdo)  # //16p11 5/2c/8/3a2/0/1c

block_packed = vdo.get_block(bla_bl)

# next = block_packed.head.bladdr.offset + block_packed.head.bladdr.segcnt * block_packed.vdo.segsize    # noqa
# bla_bl = BLADDR(vdo.read(next, 4), vdo)  # next off=0xe2a320 bl=0x07151903 unk= 0500 0900        # noqa
# block_packed2 = vdo.get_block(bla_bl)   # 67.880639N 125.307310E  76.940337N 134.367008E   # noqa
pass

"""
  # noqa
c:\DIY\VDO\db_src\ru_2013\ru\carindb
08a06b 02  BlockType.MAP__06k80: 0x15

Max PTR bites: 11
cat 0034:0003 cnt:3     next ptr: 0044
shp 0044:0001 cnt:1     next ptr: 006C
lin 006C:0002 cnt:2     next ptr: 009C
poi 0000:0000 cnt:0 
vrt 009C:011F cnt:287   next ptr: 0518
tst 0518:0002 cnt:2     next ptr: 0520
strs from 0520
begin word = 0E00:0900
Map_hex: 08 B9 30 00 0B 9A 50 00  09 19 30 00 0B FA 50 00   00 01 00 07  

01 00 00 44  
65 01 00 6C  
67 01 00 7C  
00 00 00 8C  
start_vrtx_num = 0
0520 009C 40045aa0  093CACFB 0BE5616F  0000 0518
start_vrtx_num = 260
0000 04AC 00000000  00000000 00000000  0000 051C
tail_08a06b 02.bin
SHAPE WATER[1] :0x44
POLILINE RIVER_MAJOR[1] :0x6c
POLILINE BORDER[1] :0x7c
"""

# [[04:bl_0x4]]
# chouse = 'last'
# chouse = 'first'
# bla_bl = tos_bl.cd_map[BlockType(0x04)][chouse]
# bl__04 = vdo.get_block(bla_bl)
# print(bl__04.hex)

# abstract file info
abl__abstract: block_0x12 = vdo.get_block(0)
