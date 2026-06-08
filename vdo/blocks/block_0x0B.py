"""
CH_country = 0x0b  # fully parsed chars idxs
0x0B -> 0x0D 0x0F 0x11
"""

from vdo.block_base import block_base
from vdo.datatypes import BLADDR, LIST, CH_IDX, OFFSET_TOC


class block_0x0B(block_base):
    """ CH_country type 0x0b  # fully parsed chars idxs """

    def __init__(self, bl_addr: BLADDR) -> None:
        super().__init__(bl_addr)

    @property
    def li_toc(self):
        """ LIST to table of contents """
        return self.list(OFFSET_TOC)

    def get_chidxs(self, li: LIST) -> dict:
        """
        Словарь {'CH_IDX.ch' : CH_IDX}
        Args:
            li: LIST - ptr-cnt массива ch_idx
        Returns:
            array: of ch_idx
        """
        res = {}
        for chi in self.get_indexes(li):
            res[chi.ch] = chi
        return res

    def find_chidxs(self, li: LIST, find_char) -> CH_IDX | None:
        """
        Перебор CH_IDX из li, пока не найдётся ch
        Args:
            li: LIST - ptr-cnt массива ch_idx
            find_char: char for find
        Returns:
            CH_IDX: or None
        """
        for chi in self.get_indexes(li):
            if chi.ch == find_char:
                return chi
        return None

    def get_indexes(self, li: LIST) -> CH_IDX:
        """ Генератор ch_idx из li: ptr-cnt
        Args:
            li: LIST - ptr-cnt массива ch_idx
        Returns:
            array: of ch_idx
        Example:
            for ci in ch_country_block.get_indexes( ch_country_block.list_toc ):
                print(ci.ch, ci.hex())
        """
        offset = li.ptr
        for _ in range(li.cnt):
            chidx = self.ch_idx(offset)
            offset += CH_IDX.size
            yield chidx


# -------------------------------------------------------------------------

if __name__ == '__main__':
    from vdo.datatypes import VDO_FILE
    from vdo.blocks import block_0x12

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
    #vdo = vdo34
    #vdo = vdoRu
    #vdo = vdo30
    bla = BLADDR(b'\x00\x00\x00\x01', vdo)

    tos = block_0x12(vdo)

    # ba0x13 = tos.bladdr_bibliogr
    # ba0x07 = tos.bladdr_scales
    ba0x0b = tos.bladdr_ch_country
    # ---------------------------------------------

    fl_ch_country = tos.get_farlist_ch_country()
    ch_country = block_0x0B(ba0x0b)

    arr = []
    for ch in ch_country.get_indexes(ch_country.li_toc):
        arr.append(ch)

    # то же, но с 3-им элементом - noway, там 0А блок

    ch_3 = block_0x0B(arr[0].bladdr)
    arr3 = []
    for ch in ch_country.get_indexes(ch_country.li_toc):
        arr3.append(ch)

    # vdo30  len=20
    # rus = 17
    # bnl = 3
    # bmw = 17
    pass


'''
# noqa: E501, W291

//------------------------------------------------
//--- 010 Editor v13.0.1 Binary Template
//
//      File: vdo_0x0B.bt

//------------------------------------------------
#ifndef H_VDO_INC_0x0B
#define H_VDO_INC_0x0B
/*
BT_0x0B_0x0D_0x0F_0x11

*/

// --------------------------------------------------------------------
//{BT_0x0B_0x0D_0x0F_0x11
typedef struct{
    BL_HEAD head; // заголовок
// local size-offset для LIST
    local ushort size <format=hex, hidden=true> = head.addr.size * 0x800; // size of this block  
    local uint   offset < hidden=true> = head.addr.offset;     // absolute block offset

    LIST       ch_data; // near-указатель - счетчик инфоблоков
    CH_IDX     char_of[ch_data.cnt] <optimize=false>;
    byte   marker_after_all <bgcolor=cPurple, fgcolor=cWhite>;
}BT_0x0B_0x0D_0x0F_0x11<read = Read_BT_0x0B_0x0D_0x0F_0x11>;
string Read_BT_0x0B_0x0D_0x0F_0x11(BT_0x0B_0x0D_0x0F_0x11 &a){
    local string s;
    SPrintf(s, "%i(0x%x) chars inside", a.ch_data.cnt, a.ch_data.cnt);
    return s;
}
// --------------------------------------------------------------------

#endif


//{CH_IDX size = 3 * DWORD
/*
DWORD - bl_postaddr адрес блока
byte    ch    собственно буква
byte    is_ptr_out - flag 0 - на индекс (CH_idx 0b,0d,0f,11)ж 1 - на описание (0a,0c,0e,10)
LIST    pointer-counter в bl_postaddr
WORD       align
*/



struct CH_IDX;      //объявление для рекурсивного вызова внутри описываемой
typedef struct{
    BL_ADDR   bl_postaddr;
    char      ch <fgcolor=cYellow, bgcolor=cDkGreen>; // char
    local     en_BL_TYPE en_curr_bl_type <format=hex, hidden=false> = head.type; // current bl type
    // is_ptr_out - boolean
    if(bl_postaddr.type == (en_curr_bl_type-1) ){ // outer link
        ubyte is_ptr_out <bgcolor=cLtBlue, fgcolor=cYellow,hidden=true>;
    }else{                                          // innler link
        ubyte is_ptr_out <bgcolor=cLtBlue, fgcolor=cBlue, hidden=true>;
    }
    // next for LIST far_away, have use size and offset - from bl_type_0c
    local uint size   <format=hex, hidden=true> = bl_postaddr.size * DB_BLOCK_SIZE; // size in blocks, * 0x800
    local uint offset <format=hex, hidden=true> = bl_postaddr.offset;  
    LIST       pl_postaddr <optimize=false>; 
    WORD       align <bgcolor=cWhite, fgcolor=cLtGray>;    //CONST_S    align_s(0);

/*        if(align_s.value)     // тут ноль не ноль
            Printf("Warn, %X align_s = %i( %X )\n", 
                FTell(), // offset where happened
                align_s.value, align_s.value);
*/
//BAD WAY - MAY NOT ENOUGHT MEMORY FOR BIG BLOCKS
    if(!is_ptr_out){
        // jmp and recursive declare children struct
        local uint return_addr <hidden=true> = FTell();
        FSeek(pl_postaddr.offset);
           CH_IDX childs[pl_postaddr.cnt]<optimize=false>;
        FSeek(return_addr);
    }
}CH_IDX <read = Read_CH_IDX>;
string Read_CH_IDX(CH_IDX &a){
    local string brif_str;
    local uchar MAX_CNT_STR_getPStrList = 5;
    if(a.is_ptr_out){ 
        // get str list of brif strnames
        SPrintf(brif_str, " block(0x%06X); //of:%X '%c' [%i]>%02x(%s)>%s", 
            a.bl_postaddr.raw, a.pl_postaddr.offset,
             
            a.ch, a.pl_postaddr.cnt, 
            a.bl_postaddr.type, EnumToString(a.bl_postaddr.type),
            getPStrList(a.bl_postaddr.offset, 
                a.pl_postaddr, MAX_CNT_STR_getPStrList) );
    }else{ //if(!is_ptr_out){
        // get chars list
        SPrintf(brif_str, "%c [%i]>%s", a.ch, 
            a.pl_postaddr.cnt,  getChList(a.pl_postaddr));
    }      //if(is_ptr_out)
    return brif_str;
}
//}CH_IDX

'''
