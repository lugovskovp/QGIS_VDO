"""
Самый первый, 0й блок type = 0x12

08  LIST    ptr to FAR_LIST to bl_07 -
    almanach OFFSET_LIST_PTR_07_LST_WORLD_SCALES = 0x08
0c  FAR_LIST bl_0b - ch_list_countries          OFFSET_FARLIST_0B_CH_COUNTRYES = 0x0C
14  BLADDR bl_13    - bibliografy block -       OFFSET_BLADDR_13_BIBLIOGR = 0x14
18  const_word  0001    sense unknown
1a  word    DB version  -                       OFFSET_DB_REVISION = 0x1a
1c  dword   may by max segs in packed block = 0000000c ?????? unknown
20  const_word  0001    sense unknown
22  word    max segs in block after unarc (08h, 60h)
24  LIST    posible block types? 1f, without 05         OFFSET_KNOWN_BLOCK_TYPES = 0x24
28  LIST unknown, pairs word values like num-val   OFFSET_MAY_BE_HUFFMAN_THREE = 0x28
2c  word    segment size in bytes   0800h or 0200h      OFFSET_ONE_SEG_SIZE
2e  word  0001 in dbrev=22, 0002 in dbrev=1e    sense unknown
30  const_dword     0,   sense unknown
далее в 30 и 34 версиях - разные значения
    ____DB_REV == 30/0x1E
34  BLADDR  07_LST_WORLD_SCALES (сюда из off=08 OFFSET_LIST_PTR_07_LST_WORLD_SCALES)
    - альманах
38  const_dword     00010000,   sense unknown
3c word[1f] - похоже на отсортированный по возрастанию  перечень возможных типов блоков
     (сюда из off=24 OFFSET_KNOWN_BLOCK_TYPES)
7a  const_word[0d] - 0,   sense unknown
94  массив пар word, (сюда из off=28)
    ____DB_REV == 34/0x22
34  Rectangle(area?) A: coo left bott + coo right up
44  FAR_LIST    bl_0b - ch_list_countries (=off=08)
4c  LIST содержимое CD,  (021c 0019)- 25 типов (word type, 0000-align, bladdr idxidx08,
    bl_type_start, bl_type_end)
50  Rectangle(area?) B: coo left bott + coo right up
60  BLADDR  07_LST_WORLD_SCALES (сюда из off=08 OFFSET_LIST_PTR_07_LST_WORLD_SCALES)
    - альманах
64  const_dword     00010000,   sense unknown
68  word[1f] - похоже на отсортированный по возрастанию  перечень возможных типов
    блоков (сюда из off=24 OFFSET_KNOWN_BLOCK_TYPES)
a6  массив пар word, (сюда из off=28 OFFSET_MAY_BE_HUFFMAN_THREE)
21a const_word = 0000, align?    sense unknown
21c карта размещения групп блоков на CD, кроме 08, 09, 19, 1a, 1b, 1f
    word type, const_word = 0 align, bladr_08, first_bl, end_bl (size=0x10)
"""
# noqa: E501

from vdo.enums import BlockType
from vdo.datatypes import VDO_FILE, BLADDR, FAR_LIST
from vdo.datatypes import OFFSET_ONE_SEG_SIZE, OFFSET_DB_REVISION
from vdo.geotypes import COORD
from vdo.block_base import block_base


OFFSET_LIST_PTR_07_LST_WORLD_SCALES = 0x08      # 00 34 00 01

OFFSET_FARLIST_0B_CH_COUNTRYES = 0x0C       # RU 00 00 03 01 00 0c 00 14
OFFSET_FARLIST_0B_CH_COUNTRYES_num2 = 0x44  # only in dbrev 34

OFFSET_BLADDR_13_BIBLIOGR = 0x14      # RU 00 00 01 01 00 01 00 1e

OFFSET_ALLWAYS_12 = 0x1e
OFFSET_MAX_SEGS_UNPACKED_SH = 0x22

# only in dbrev 34
OFFSET_CD_MAP_BLOCKS = 0x4c
OFFSET_AREA_A = 0x34
OFFSET_AREA_B = 0x50

OFFSET_KNOWN_BLOCK_TYPES = 0x24
OFFSET_MAY_BE_HUFFMAN_THREE = 0x28


class block_0x12(block_base):
    ''' Самый первый, 0й, уникальный блок type = 0x12 '''

    def __init__(self, vdo: VDO_FILE) -> None:
        """ --- """
        bladdr0x12 = BLADDR(b'\x00\x00\x00\x01', vdo)
        super().__init__(bladdr0x12)

        # в русской версии, где dbrev == 30  карты вообще нет
        if self.get_dbrev == 34:
            # карта размещения групп блоков на CD, кроме 08, 09, 19, 1a, 1b, 1f
            CD_MAP_ITEM_SIZE = 0x10
            self.cd_map = {}
            l_cd_map = self.list(OFFSET_CD_MAP_BLOCKS)
            for i in range(l_cd_map.cnt):
                # zTzz, BLADDR idxidx08, BLADDR firstBl, BLADDR lastBl; len=0x10
                raw = self.read(l_cd_map.ptr + i * CD_MAP_ITEM_SIZE, CD_MAP_ITEM_SIZE)
                type = BlockType(raw[1])       # второй байт - тип блока
                idxidx08 = BLADDR(raw[4:8], self.vdo)
                first = BLADDR(raw[8:12], self.vdo)      # BLADDR firstBlock
                last = BLADDR(raw[12:16], self.vdo)      # BLADDR lastBlock
                self.cd_map[type] = {"first" : first,
                                     "last" : last,
                                     "idxidx08" : idxidx08}

            # вероятно,

            pass
            
    # -------------------------------------------------------

    @property
    def get_segsize(self) -> int:
        """ size of one segment """
        return self.ushort(OFFSET_ONE_SEG_SIZE)

    @property
    def get_dbrev(self) -> int:
        """ carindb revision """
        return self.ushort(OFFSET_DB_REVISION)

    @property
    def likely_const_ALLWAYS_12(self) -> int:
        """ not sure: max segments in unpacked block """
        return self.ushort(OFFSET_ALLWAYS_12)

    @property
    def likely_MAX_SEGS_UNPACKED(self) -> int:
        """ вероятно, максимальное количество сегментов в распакованном"""
        return self.ushort(OFFSET_MAX_SEGS_UNPACKED_SH)

    @property
    def bladdr_bibliogr(self) -> BLADDR:
        """
        Return:
            BLADDR: BIBLIOGR type 0x13
        """
        return self.bladdr(OFFSET_BLADDR_13_BIBLIOGR)

    @property
    def bladdr_scales(self) -> BLADDR:
        """
        Return:
            BLADDR: SCALES type 0x07
        """
        li_scales = self.list(OFFSET_LIST_PTR_07_LST_WORLD_SCALES)
        return self.bladdr(li_scales.ptr)
        # 000002 01 : 0001:0000 cnt:0 34
        # 000002 01 : 0001:0000 cnt:0 30
        # 000003 04 : 0001:0000 cnt:0 bmw

    def get_farlist_ch_country(self) -> FAR_LIST:
        """
        Return:
            FAR_LIST: CH_country type 0x0b  and list of ch # fully parsed chars idxs
        """
        return self.farlist(OFFSET_FARLIST_0B_CH_COUNTRYES)

    @property
    def bladdr_ch_country(self) -> FAR_LIST:
        """
        Return:
            BLADDR: CH_country type 0x0b  # fully parsed chars idxs
        """
        return self.get_farlist_ch_country().bladdr

    @property
    def area_A(self):
        """

        """
        if self.dbrev != 34:
            # db_rev=30 - w|o rectangle area
            return None
        lb = self.coord(OFFSET_AREA_A)                    # left bottom
        rt = self.coord(OFFSET_AREA_A + COORD.size)       # right top
        return (lb, rt)

    @property
    def area_B(self):
        """

        """
        if self.dbrev != 34:
            # db_rev=30 - w|o rectangle area
            return None
        lb = self.coord(OFFSET_AREA_B)                    # left bottom
        rt = self.coord(OFFSET_AREA_A + COORD.size)       # right top
        return (lb, rt)
        

"""
# noqa: E501
def print_huff(self):
        ''' DEBUG '''
        print("Huffman three")
        l_ht = self.list(OFFSET_MAY_BE_HUFFMAN_THREE)       #LIST(self.read(OFFSET_MAY_BE_HUFFMAN_THREE, LIST.bytescnt))
        #for ch, val in self.get_huf_pair():
        #    print(f"{hex(ch)}  {hex(val)}\t {ch} {val}")
        print("")
        for ch, val in self.get_huf_pair():
            print(f"({hex(ch)},{hex(val)}), ",end="")
    ''' ee
    (0x1,0xc), (0x2,0x10), (0x3,0x8), (0x4,0x1c), (0x5,0x8), (0x6,0x10), (0x7,0x8), (0x8,0x20), (0x9,0x1a),\
        (0xa,0x6), (0xb,0x74), (0xc,0x6), (0xd,0x4), (0xe,0x30), (0xf,0x8), (0x10,0x8), (0x11,0x3c), (0x12,0x4),\
        (0x13,0x6), (0x14,0x8), (0x15,0x6), (0x16,0x6), (0x17,0x174), (0x18,0x1c), (0x19,0x160), (0x1a,0xc),\
        (0x1b,0x60), (0x1c,0x54), (0x1d,0x4), (0x1e,0x8), (0x1f,0x18), (0x20,0x38), (0x21,0x10), (0x22,0x4),\
        (0x23,0x4), (0x24,0x4), (0x25,0x14), (0x26,0x4), (0x27,0x8), (0x28,0xc), (0x29,0xc), (0x2a,0x4),\
        (0x2b,0x30), (0x2c,0x8), (0x2d,0x8), (0x2e,0x20), (0x2f,0x28), (0x30,0xc), (0x31,0x8), (0x32,0x1c), (0x33,0x20),\
        (0x34,0x10), (0x35,0x8), (0x36,0x10), (0x37,0xa), (0x38,0x4), (0x39,0x4), (0x3a,0x14), (0x3b,0x4), (0x3c,0x10),\
        (0x3d,0x34), (0x3e,0x14), (0x3f,0x18), (0x40,0xa), (0x41,0x6), (0x42,0x18), (0x43,0x1c), (0x44,0x4), (0x45,0x10),\
        (0x46,0x64), (0x47,0x10), (0x48,0x4), (0x49,0x4), (0x4a,0x8), (0x4b,0x14), (0x4c,0x8), (0x4d,0xc), (0x4e,0x1c),\
        (0x4f,0x4), (0x50,0x10), (0x51,0x28), (0x52,0x10), (0x53,0x4), (0x54,0x4), (0x55,0x8), (0x56,0x18), (0x57,0xc),\
        (0x58,0x4), (0x59,0x4), (0x5a,0x2), (0x8a,0x1), (0x97,0x10), (0x9d,0x16)
    '''

    def get_huf_pair(self):
        ''' DEBUG '''
        l_ht = self.list(OFFSET_MAY_BE_HUFFMAN_THREE)
        PAIR_REC_LEN = 4
        for off in range(l_ht.ptr, l_ht.ptr+(PAIR_REC_LEN * l_ht.cnt), PAIR_REC_LEN):
            (ch, val) = (self.ushort(off), self.ushort(off+2))
            yield (ch, val)
"""
# -------------------------------------------------------------------------

if __name__ == '__main__':
    from vdo.datatypes import VDO_FILE

    vdo2 = VDO_FILE()

    fpath30 = 'c:\\DIY\\VDO\\db_src\\NAV_DB\\carindb'
    vdo30 = VDO_FILE(fpath30)

    fpath34 = 'c:\\DIY\\VDO\\db_src\\1. BNL_13_14\\carindb'
    vdo34 = VDO_FILE(fpath34)

    fpathRu = 'c:\\DIY\\VDO\\db_src\\ru_2013\\ru\\carindb'
    vdoRu = VDO_FILE(fpathRu)

    fpathbmw = 'c:\\DIY\\VDO\\db_src\\bmw34-2010\\DB\\DB_0'
    vdobmv = VDO_FILE(fpathbmw)

    vdo = vdobmv
    vdo = vdo34
    vdo = vdoRu
    bla = BLADDR(b'\x00\x00\x00\x01', vdo)

    tos = block_0x12(vdo)
    li0 = tos.list(b'\x01\x00\x00\x10')
    li_WORLD_SCALES = tos.list(OFFSET_LIST_PTR_07_LST_WORLD_SCALES)

    ba0x13 = tos.bladdr_bibliogr
    ba0x07 = tos.bladdr_scales
    ba0x0b = tos.bladdr_ch_country

    coo1 = tos.read(OFFSET_AREA_A, 8)
    # b'\x06\xe6y\xaa\x0b\xb1\xde\x1f'
    # b'\nlvM\x10_\xf3\xf9'
    coo2 = tos.read(OFFSET_AREA_B + 8, 8)
    # b'(\xc7\xb2\xb8\x17)\x94p'
    # b'\x0cS\xbd\xcb\x11\xb7\x02='

    fl_CH_COUNTRYES = tos.farlist(OFFSET_FARLIST_0B_CH_COUNTRYES)
    fl_CH_COUNTRYES2 = tos.farlist(OFFSET_FARLIST_0B_CH_COUNTRYES_num2)
    
    # bmw
    # a (35.317104N 9.161808W, 70.479517N 93.151702E)
    # b (41.282694N 19.767135E, 70.479517N 93.151702E)
    # bnl
    # a (49.450295N 1.478463E, 55.251335N 7.226644E)
    # b (49.450295N 2.555703E, 55.251335N 7.226644E)
    # rus
    # a (35.317104N 9.161808W, 70.479517N 149.996368E)
    # b (41.282694N 19.767135E, 70.479517N 149.996368E)
    pass

'''
# noqa: E501
b'\x00\x00\x02\x01'
b'\x00\x00\x01\x01'


    MAP__05k200 	= 0x14  # scale 5   14_MAP_POLI_5_k200	//[5] 5(9:200h)-0x14
    MAP__06k80 	= 0x15  	# scale 6   15_MAP_POLI_6_k80	//[6] 6(7:80h)-0x15
    MAP__07k40 	= 0x16  	# scale 7   16_MAP_POLI_7_k40	//[7] 7(6:40h)-0x16
                            #								//[8] - всегда всё 0.
    MAP__09k100 	= 0x1c  # scale 9   1c_MAP_POLI_9_k100	//[9]  9(8:100h)-0x1c
    MAP__10k400 	= 0x1d  # scale 10  1d_MAP_POLI_10_k400 //[10] a(a:400h)-0x1d
    MAP__11k_11	= 0x1e  # scale 11  1e_MAP_POLI_11			//[11] b(b:666h)-0x1e

//--- 010 Editor v13.0.1 Binary Template
#ifndef H_VDO_INC_0x12
#define H_VDO_INC_0x12

/*
BT_0x12 первый блок - размером х800, даже если потом переопределится
BTYPE_FORMAT
*/
struct BTYPE_FORMAT;
struct BLOCKS_ON_CD;
//---------------------------------------;
typedef struct{
//header start
    // local ushort DB_BLOCK_SIZE = 0x800;
    BL_HEAD head; // заголовок
    local ushort size <format=hex, hidden=true> = head.addr.size * 0x800; // size of this block
    local uint   offset <hidden=true> = head.addr.offset;     // absolute block offset

    LIST    ptr_to_07_LST_WORLD_SCALES;//ptr2 far ptr 2 - 07_LST_WORLD_SCALES
    FAR_LIST ch_countryes;//_0B_chars_countries
    FAR_LIST bd_description;//_13_carindb_info
    CONST_S zero(0);
    WORD    global_max_block_len <bgcolor=cLtGreen,fgcolor=cRed> ;
    // Maximal blocks qty in one block,  waz CONST_I mb_qty_scales_in_0x07(0x0c);

    CONST_I hz_10008(0x10008);//bmw - 10060
    LIST    mb_knownBlockTypes; // except: 5, 1f,
    LIST    like_askii_list; //1-c 2-10, 3-8 4-1c 5-8
    // 02 - no coords and addinfo
    WORD    global_block_size <bgcolor=cLtGreen,fgcolor=cRed> ;
    CONST_S is_34(1);
    CONST_I zero(0);
    if (IS_OFICIAL_MAP){  //DB v34 - 13_14 years files
        LON_LAT corner_bott_left, corner_upper_right;
// bnl 49,45N 1.5E - 55.25N 7.22E
// ee  41.26N 12.1E - 59.89N 29.7E
        FAR_LIST ch_countryes_again;
        LIST     CD_offsets_map;
        LON_LAT  corn_bott_left, corn_upper_right;
    }
    FAR_LIST almanach_07_LST_WORLD;

    struct{
        struct{
            byte zero;
            en_BL_TYPE type;
        }mb_bl_types [ mb_knownBlockTypes.cnt ]
            <format=hex,bgcolor=cLtBlue,fgcolor=cBlue, optimize=true>;
    }FoldTypes;

    if(!IS_OFICIAL_MAP){ struct{WORD z1; QWORD z1,z2,z3;}zero<fgcolor=cGray>;}

    BTYPE_FORMAT  items[ like_askii_list.cnt ]<format=hex, fgcolor=cBlue>;

    if (IS_OFICIAL_MAP){  //DB v34 - 13_14 years files
        WORD align;
        //BLOCKS_ON_CD cd1;
        //BLOCKS_ON_CD cd2;
        BLOCKS_ON_CD cd_map[CD_offsets_map.cnt]<optimize=false>;
    }
}BT_0x12<read=Read_BT_0x12>;
string Read_BT_0x12(BT_0x12 &a){
    return "database description";
}
//------------------------------------

// BTYPE_FORMAT pointer to data and data
// in carinds ee and bnl both ARRAYs[92] is equal
// but in rus - differs from ee and bnl starting from [22] item
// in all 3 - last (??) 3 items - not by ordered
typedef struct{
    WORD   num <format = hex>;
    WORD   val <format = hex, fgcolor=cDkGreen>;
}BTYPE_FORMAT <read=Read_BTYPE_FORMAT>;
string Read_BTYPE_FORMAT(BTYPE_FORMAT &a){
    local string s;
//    SPrintf(s, "%02i\t %02i %02X - %02X [%o] %i",
//            a.num-1, a.num, a.num, a.val, a.val, a.val);
SPrintf(s, "%02i\t %i", a.num, a.val);
Printf("%s\n",s);
    return s;
}
//BTYPE_FORMAT 346543 618610
// --------------------------------------------------------------------

typedef struct{
//bnl 4801800h - 00 90 03: 08 exist, type 08 only one rec
// bnl 4901800h - 00 92 03: 04 exist - 00 - 01 08 - crypted
// bnl 9006000h - 01 20 0c:03 exist -00- 0105 crypted Fg:Fg:0xFFFFE0 Bg:0xFF8080
    uchar align <fgcolor=0xFFFFE0, bgcolor=0xFF8080>;
    en_BL_TYPE  en_block_data_type<format=hex, fgcolor=0xFFFFE0, bgcolor=0xFF8080>;// <format=hex, fgcolor=0xFFFFE0, bgcolor=0xFF8080>;
    WORD    zero_value <fgcolor=cGray>; //, hidden=true
    BL_ADDR almanac_idxidx08;    //bnl 4801800h - 00 90 03: 08 exist, type 08 only one rec
    BL_ADDR first_block_data;    // bnl 4901800h - 00 92 03: 04 exist - 00 - 01 08 - crypted
    BL_ADDR last_block_data;    // bnl 9006000h - 01 20 0c:03 exist -00- 0105 crypted
//  08/03/03 1e;  ||||10/10 11; 11/11 12; 12/12 13; 13/13 17;  17/17 18; 18/18 00;
}BLOCKS_ON_CD <read=Read_BLOCKS_ON_CD>;
string Read_BLOCKS_ON_CD(BLOCKS_ON_CD &a){
    local string s;
    SPrintf(s, "Bl. from 0x%06X to 0x%06X - %02X--%s (idx: 0x%06X)",
        a.first_block_data.raw, a.last_block_data.raw,
        a.en_block_data_type, EnumToString(a.en_block_data_type),
        a.almanac_idxidx08.raw);
    return s;
}
// --------------------------------------------------------------------

#endif
'''
