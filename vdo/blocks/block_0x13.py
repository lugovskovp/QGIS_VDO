
from vdo.block_base import block_base
from vdo.datatypes import BLADDR

OFFSET_LIST_STR_LABEL = 0x14
OFFSET_LIST_STR_DESCRIPTION = 0x18
OFFSET_LIST_STR_INFORMATION = 0x32


class block_0x13(block_base):
    '''
    class BlockType(enum.Enum):    BIBLIOGR = 0x13
    '''
    def __init__(self, bl_addr: BLADDR) -> None:
        super().__init__(bl_addr)

    @property
    def str_label(self):
        return self.read_li_str(OFFSET_LIST_STR_LABEL)

    @property
    def str_description(self):
        return self.read_li_str(OFFSET_LIST_STR_DESCRIPTION)

    @property
    def str_information(self):
        return self.read_li_str(OFFSET_LIST_STR_INFORMATION)


# -------------------------------------------------------------------------

if __name__ == '__main__':
    from vdo.datatypes import VDO_FILE, BYTESTRUCT
    from vdo.blocks import block_0x12

    fpath30 = 'c:\\DIY\\VDO\\db_src\\NAV_DB\\carindb'
    vdo30 = VDO_FILE(fpath30)

    fpath34 = 'c:\\DIY\\VDO\\db_src\\1. BNL_13_14\\carindb'
    vdo34 = VDO_FILE(fpath34)
    
    fpathbmw = 'c:\\DIY\\VDO\\db_src\\bmw34-2010\\DB\\DB_0'
    vdobmv = VDO_FILE(fpathbmw)

    fpathRu = 'c:\\DIY\\VDO\\db_src\\ru_2013\\ru\\carindb'
    vdoRu = VDO_FILE(fpathRu)

    vdo = vdobmv
    vdo = vdo34
    vdo = vdoRu
    bla = BLADDR(b'\x00\x00\x00\x01', vdo)

    #
    tos = block_0x12(vdo)
    inf = block_0x13(tos.bladdr_bibliogr)

    la = inf.read_str(OFFSET_LIST_STR_LABEL)

    #   c1(0x69f6bc7 0xd3ed78e)   dec111111111 dec222222222
    c1 = inf.coord(0x1c)        # 40.000004N 9.999998W
    #   c3(0x13de4355 0x1a7daf1c)  dec333333333  dec444444444
    c2 = inf.coord(0x24)        # 80.000008N 30.000006E

    interest = BYTESTRUCT(inf.read(0x2c, 0x10))
    
    print()
    print(inf.str_information)
    # bnl : 1.  name:                     bnl_nok_nok_12q4_20130128p.
    #       2.  content:                  benelux (benelux)
    #       3.  oem:                      nok
    # old : 1.  name:                     bal_ad_nod_45051_20050210k.
    #       2.  content:                  baltics (europe)
    #       3.  oem:                      aftersales
    # bmw : 1.  name:                     rus_hw_ntq_opel_09q4_20100305p21.
    #       2.  content:                  russia (russia)
    #       3.  oem:                      opel
    # rus : 1.  name:                     rus_hw_ntq_opel_11q4_20120416p23.
    #       2.  content:                  russia (russia)
    #       3.  oem:                      opel

    pass

# -------------------------------------------------------------------------

'''
# noqa: E501
//--- 010 Editor v13.0.1 Binary Template//      File: vdo_0x13.b
40.000004N, 9.999998W   https://www.openstreetmap.org/#map=19/40.000004/-9.999998  06 9f 6b c7
0020:  0d 3e d7 8e
80.000008N, 30.000008E  https://www.openstreetmap.org/#map=19/80.000008/30.000008 13 de 43 55 1a 7d af 1c
// --------------------------------------------------------------------
//{
typedef struct{
    BL_HEAD head; // заголовок
// local size-offset для LIST
    local ushort size <format=hex, hidden=true> = head.addr.size * 0x800; // size of this block
    local uint   offset < hidden=true> = head.addr.offset;     // absolute block offset
    if(head.is_compressed){
        DWORD   q[4]<bgcolor=cLtPurple>;
        break;
    }
    LIST data;
    LIST coord;
//:data
    CONST_S hex0001(1);
    WORD db_ver <comment="=bibliogr.DB-REL  (30/34) ex unkn_1Eh_or_22h", bgcolor=cLtBlue, fgcolor=cYellow>
    LIST   chr_label; // cnt = chrs + \0?
    LIST   chr_descr; // description string
//:coord
    // CONST_I c1(0x69f6bc7); CONST_I c2(0xd3ed78e); //DWORD   dec111111111, dec222222222
    // CONST_I c3(0x13de4355); CONST_I c4(0x1a7daf1c); //DWORD   dec333333333, dec444444444
    LON_LAT corner_bott_left, corner_upper_right;
    CONST_S hex0001(1);
    CONST_S hex0001(1);
    WORD db_ver_again <comment="=bibliogr.DB-REL  (30/34) ex unkn_1Eh_or_22h", bgcolor=cLtBlue, fgcolor=cYellow>;
    LIST   chr_all_least_str;
    CONST_S align(0);
    
    char label[chr_label.cnt]<bgcolor=cLtGreen, fgcolor=cBlue>;
    char description[chr_descr.cnt]<bgcolor=cLtGreen, fgcolor=cBlue>;
    char all_info[chr_all_least_str.cnt]<bgcolor=cLtGreen, fgcolor=cBlue>;

}BT_0x13<read=Read_BT_0x13>;

string Read_BT_0x13(BT_0x13 &a ){
    local string s;
    if(a.head.is_compressed){
        SPrintf(s, "Block 0x13 compressed. STOP parsing!");
        SPrintf(s, "%08X %08X %08X %08X", a.q[0], a.q[1], a.q[2], a.q[3]);
    }else{
        SPrintf(s, "DB ver. %i (0x%x) %s, %s", a.db_ver, a.db_ver,
            a.label, a.description);
    }
    return s;
}
// --------------------------------------------------------------------

#endif
/*
78daed51

*/
'''
