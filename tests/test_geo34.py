import struct       # noqa: F401
from vdo.datatypes import VDO_FILE, BLADDR    # UINT_struct,


def get_vdo():
    fpath30 = 'c:\\DIY\\VDO\\db_src\\NAV_DB\\carindb'
    vdo30 = VDO_FILE(fpath30)       # noqa: F841

    fpath34bnl = 'c:\\DIY\\VDO\\db_src\\1. BNL_13_14\\carindb'
    vdo34bnl = VDO_FILE(fpath34bnl)       # noqa: F841

    fpathRu = 'c:\\DIY\\VDO\\db_src\\ru_2013\\ru\\carindb'
    vdoRu = VDO_FILE(fpathRu)       # noqa: F841

    fpathbmw = 'c:\\DIY\\VDO\\db_src\\bmw34-2010\\DB\\DB_0'
    vdobmv = VDO_FILE(fpathbmw)       # noqa: F841

    vdo = vdobmv
    #vdo = vdo34bnl
    #vdo = vdoRu
    #vdo = vdo30
    return vdo


#--------------------------------------
from vdo.blocks import block_0x12       # noqa
from vdo.enums import BlockType       # noqa

vdo = get_vdo()

tos_bl = vdo.get_block(0)

# [1D:MAP__10k400]
chouse = 'last'
chouse = 'first'
bla_bl = tos_bl.cd_map[BlockType(0x04)][chouse]
bl__04 = vdo.get_block(bla_bl)
print(bl__04.hex)

'''bmw_a_1d = vf.block(0xE2A2A00)'''
bla_bl = BLADDR(vdo.read(0xE2A2A00, 4), vdo)
block_packed = vdo.get_block(bla_bl)
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


# vdoRu  08a06b02 ru34 packed
#bla_bl = BLADDR(UINT_struct.pack(0x08a06b02), vdo)  # 08a06b02 ru34 packed
# block_packed = vdo.get_block(bla_bl.next_block_offset())
# # unk beg pack = 0x0e00 0900
block_packed = vdo.get_block(0)        # unk beg pack = 0x0e00 0900
with open("c:/temp/bmw txt 0x12.txt", "w") as f:
    f.write(block_packed.hex)

with open("c:/temp/0x08a06b02.txt", "bw") as f:
    f.write(block_packed._raw)
"""
# 08a06b02 ru34 packed
01 00 00 44
65 01 00 6c
67 01 00 7c
00 00 00 8c
05 20 00 9c 40 04 5a a0 09 3c ac fb 0b e5 61 6f 00 00 05 18
00 00 04 ac 00 00 00 00 00 00 00 00 00 00 00 00 00 00 05 1c
> а следующий - распакованные линии.

> p_str_name > 0520
> ptr_vrtx ?? == 04ac?
> word id ?? (есть ли проверка на существование?)
> ptr_linesign > tst 0518  (? < str 0520 ??)
> word or_b_or_c - какое-то число?
> ptr_tstr     p_p_str_name ??
> word or_38_or_0_b_country

cat 0034:0003 cnt:3
shp 0044:0001 cnt:1
lin 006C:0002 cnt:2
poi 0000:0000 cnt:0
vrt 009C:011F cnt:287
tst 0518:0002 cnt:2
str 0520
"""


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
