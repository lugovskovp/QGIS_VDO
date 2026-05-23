import struct       # noqa: F401
from vdo.datatypes import VDO_FILE, UINT_struct, BLADDR


def get_vdo():
    fpath30 = 'c:\\DIY\\VDO\\db_src\\NAV_DB\\carindb'
    vdo30 = VDO_FILE(fpath30)       # noqa: F841

    fpath34 = 'c:\\DIY\\VDO\\db_src\\1. BNL_13_14\\carindb'
    vdo34 = VDO_FILE(fpath34)       # noqa: F841

    fpathRu = 'c:\\DIY\\VDO\\db_src\\ru_2013\\ru\\carindb'
    vdoRu = VDO_FILE(fpathRu)       # noqa: F841

    fpathbmw = 'c:\\DIY\\VDO\\db_src\\bmw34-2010\\DB\\DB_0'
    vdobmv = VDO_FILE(fpathbmw)       # noqa: F841

    vdo = vdobmv
    #vdo = vdo34
    #vdo = vdoRu
    vdo = vdo30
    return vdo


#--------------------------------------

vdo = get_vdo()
# ru 0x1E6EA000 === 03cdd401 14 0000 [14:MAP__05k200]
geo_bl = vdo.get_block(0x1E6EA000)      # ru 0x1E6EA000

blnum = UINT_struct.pack(0x03c68a03)    # bl_addr(0x03c68a03); // 0x 1e345000 - 0x1c kaliningrad = 0 # noqa: E501
blak = BLADDR(blnum, vdo)
geo_bl = vdo.get_block(blak)


ss = geo_bl.read(geo_bl.toc.li_str.ptr, 16)  # облом 0x7c - b'\x00\x80\x02\x00atlantic oce' # noqa: E501
st = geo_bl.read_tstr(geo_bl.toc.li_str.ptr)
#


# buf = b'\x02\x01\x01\x01\x04\x05\x10\x01'
# (cat, draw, ptr, next_ptr) = struct.unpack(">bbH2xH", buf)

all_categories = geo_bl.get_all_categories()

# GEO_SHAPE_struct = struct.Struct(">HHL8x2xHxxH16x")

# buf = geo_bl.read(geo_bl.toc['li_shp'].ptr, 0x14 * 2)
# (ptr_str, ptr_vrtx, id, ptr_tstr, next_ptr_vrtx) = GEO_SHAPE_struct.unpack(buf)

shape1 = geo_bl.shape(geo_bl.toc.li_shp.ptr, all_categories[0])
sss = shape1.__repr__()


# buf = geo_bl.read(geo_bl.toc['li_lin'].ptr, 0x10 * 2)

# GEO_LINE_struct = struct.Struct(">HHLHHHHxxH12x")
# (   prt_str,
#     ptr_vrtx,
#     id,
#     ptr_linesign,
#     ptr_unk2,
#     ptr_tstr,
#     ptr_unk3,
#     next_ptr_vrtx) = GEO_LINE_struct.unpack(buf)

line_river = geo_bl.line(geo_bl.toc.li_lin.ptr, all_categories[3])  # bl_addr(0x03c68a03) # noqa: E501
lss = line_river.__repr__()

max_vrt_val = geo_bl.map.max_vrt_val

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
