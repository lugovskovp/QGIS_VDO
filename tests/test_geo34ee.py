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

вc:\DIY\VDO\db_src\3. EE_13_14\carindb
0571b8 01  BlockType.MAP__10k400: 0x1d

Max PTR bites: 12
cat 0034:0002 cnt:2     next ptr: 0040
shp 0040:0004 cnt:4     next ptr: 00A4
lin 0000:0000 cnt:0 
poi 0000:0000 cnt:0 
vrt 00A4:029C cnt:668   next ptr: 0B14
tst 0B14:0003 cnt:3     next ptr: 0B20
strs from 0B20
begin word = 0500:0900
Map_hex: 13 E9 F8 00 0A 7A 50 00  15 E9 F8 00 0C 7A 50 00   00 01 00 0A  

01 00 0040  
01 00 0054  
00 00 0090  
0040:
start_vrtx_num = 0
0000 00A4 00000000  113E1F3A 0B20DBB8  0000 0B14
start_vrtx_num = 8
0B20 00C4 4005ab9b  143507C4 0BC91F4E  0000 0B14
start_vrtx_num = 271
0B28 04E0 4006c6ce  14E77BC8 0B667F38  0000 0B18
start_vrtx_num = 570
0B3A 098C 400756fc  13648A44 0B73197C  0000 0B1C
start_vrtx_num = 668
0000 0B14 00000000  00000000 00000000  0000 0B20
tail_0571b8 01.bin

"""

next = block_packed.head.bladdr.offset + block_packed.head.bladdr.segcnt * block_packed.vdo.segsize    # noqa

pass

#===================================
# blnum = UINT_struct.pack(0x03c68a03)    # bl_addr(0x03c68a03); // 0x 1e345000 - 0x1c kaliningrad = 0 # noqa: E501
# blak = BLADDR(blnum, vdo)
# geo_bl = vdo.get_block(blak)  '08 b9 30 00  0b 9a 50 00  09 19 30 00  0b fa 50 00  00 01 00 07'  # noqa

pass
