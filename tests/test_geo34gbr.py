
import struct       # noqa: F401
from vdo.datatypes import VDO_FILE, BLADDR    # UINT_struct,
#block(0x03350c01);  // 01-packed in 5 gbr: cat=4, shp=e, lin=9, vrtx=cc, tst=59 (wow///) 


def get_vdo():
    fpath30 = 'c:\\DIY\\VDO\\db_src\\NAV_DB\\carindb'
    vdo30 = VDO_FILE(fpath30)       # noqa: F841

    fpath34bnl = 'c:\\DIY\\VDO\\db_src\\1. BNL_13_14\\carindb'
    vdo34bnl = VDO_FILE(fpath34bnl)       # noqa: F841

    fpath34gbr = 'c:\\DIY\\VDO\\db_src\\5. GBR_IR_13_14\\carindb'
    vdo34gbr = VDO_FILE(fpath34gbr)       # noqa: F841

    fpathRu = 'c:\\DIY\\VDO\\db_src\\ru_2013\\ru\\carindb'
    vdoRu = VDO_FILE(fpathRu)       # noqa: F841

    fpathbmw = 'c:\\DIY\\VDO\\db_src\\bmw34-2010\\DB\\DB_0'
    vdobmv = VDO_FILE(fpathbmw)       # noqa: F841

    vdo = vdobmv
    #vdo = vdo34bnl
    #vdo = vdoRu
    #vdo = vdo30
    vdo = vdo34gbr
    return vdo


# --------------------------------------------------------------
from vdo.blocks import block_0x12, block_0x1E       # noqa
from vdo.enums import BlockType       # noqa

vdo = get_vdo()

tos_bl: block_0x12 = vdo.get_block(0)

"""
# block(0x03350c01);  // 01-packed in 5 gbr: cat=4, shp=e, lin=9, vrtx=cc, tst=59 (wow///) 
# bl.offs = '0x19a86000'
# bl.addr = '0x03350c01'
# tp:1Eh() of:0x19A86000 sz=1 
#  area [4000000x4000000] h_scale scale_667 (11)
# 37.681648N, 0.060900W  x  49.761246N, 12.018696E
# shift scale   0x0b --- SO? err???
# unkn          0x15170b00

bla_bl = BLADDR(vdo.read(0x19a86000, 4), vdo)
block_1e_pack: block_0x1E = vdo.get_block(bla_bl)   # 37.681647N 0.060899W  49.761244N 12.018697E
"""

# bl.offs = '0x19a87800' // offset 19a87800 // 01-packed  e/6/2/0/3f
# bl.addr = '0x03350f01' 

bla_bl = BLADDR(vdo.read(0x19a87800, 4), vdo)
block_1e_pack: block_0x1E = vdo.get_block(bla_bl)

print(block_1e_pack.hex.replace("   ", "\n"))
pass
