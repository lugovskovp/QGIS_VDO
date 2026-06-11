

from vdo.datatypes import VDO_FILE, BLADDR


fpath30 = 'c:\\DIY\\VDO\\db_src\\NAV_DB\\carindb'
vdo30 = VDO_FILE(fpath30)

fpath34 = 'c:\\DIY\\VDO\\db_src\\1. BNL_13_14\\carindb'
vdo34 = VDO_FILE(fpath34)

fpathRu = 'c:\\DIY\\VDO\\db_src\\ru_2013\\ru\\carindb'
vdoRu = VDO_FILE(fpathRu)

fpathbmw = 'c:\\DIY\\VDO\\db_src\\bmw34-2010\\DB\\DB_0'
vdobmv = VDO_FILE(fpathbmw)

vdo = vdobmv
#vdo = vdo34
#vdo = vdoRu
#vdo = vdo30
#--------------------------------------

bl_false = vdo.get_block(100)
bla = BLADDR(b'\x00\x00\x00\x01', vdo)
bl_first = vdo.get_block(bla)
bla = BLADDR(b'\x00\x00\x00\x00', vdo)
bl_zero = vdo.get_block(bla)
addr = bl_first.head.bladdr.offset + (bl_first.head.bladdr.segcnt * bl_first.vdo.segsize)   # noqa: E501
bl_third = vdo.get_block(addr)
if bl_third:
    addr = bl_third.offset_next()
else:
    addr = bl_first.bladdr_scales.offset
bl_forths = vdo.get_block(addr)

print(f"{bl_false}\n{bl_first}\n{bl_third}\n{bl_zero}\n{bl_forths}")
pass
