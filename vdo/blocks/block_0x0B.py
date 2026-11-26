"""
CH_country = 0x0b  # fully parsed chars idxs
0x0B -> 0x0D 0x0F 0x11

Страны и их индексы символов.
Содержит список CH_IDX, каждый из которых указывает на блок с данными страны.
"""
from __future__ import annotations  # Обязательно на самой первой строчке файла

from typing import TYPE_CHECKING    # , Iterator, Optional

if TYPE_CHECKING:
    from QGIS_VDO.vdo.datatypes import LIST as LIST_TYPE    # , CH_IDX as CH_IDX_TYPE

from QGIS_VDO.vdo.block_base import block_base
from QGIS_VDO.vdo.datatypes import BLADDR, OFFSET_TOC       # CH_IDX,


class block_0x0B(block_base):
    """
    CH_country type 0x0b  # fully parsed chars idxs

    Содержит список стран и их символьных индексов.
    Каждый элемент CH_IDX указывает на блок данных страны (0x0D, 0x0F, 0x11).
    """

    __slots__ = ('vdo', '_li_toc_cache')

    def __init__(self, bl_addr: BLADDR) -> None:
        super().__init__(bl_addr)

        self.vdo = bl_addr.vdo
        self._li_toc_cache: LIST_TYPE | None = None

    @property
    def li_toc(self) -> LIST_TYPE:
        """LIST to table of contents (кэшированный)."""
        if self._li_toc_cache is None:
            self._li_toc_cache = self.read_list(OFFSET_TOC)
        return self._li_toc_cache

    # def get_chidxs(self) -> dict[str, CH_IDX_TYPE]:
    #     """
    #     Словарь {'CH_IDX.ch' : CH_IDX} для всех стран.

    #     Returns:
    #         dict: словарь символов -> CH_IDX
    #     """
    #     res: dict[str, CH_IDX_TYPE] = {}
    #     for chi in self.get_chidxs_iter():
    #         res[chi.ch] = chi
    #     return res

    # def find_chidx(self, find_char: str) -> Optional[CH_IDX_TYPE]:
    #     """
    #     Поиск CH_IDX по символу страны.

    #     Args:
    #         find_char: символ для поиска

    #     Returns:
    #         CH_IDX или None
    #     """
    #     for chi in self.get_chidxs_iter():
    #         if chi.ch == find_char:
    #             return chi
    #     return None

    # def get_chidxs_iter(self) -> Iterator[CH_IDX_TYPE]:
    #     """
    #     Итератор по CH_IDX из li_toc.

    #     Yields:
    #         CH_IDX: объекты индексных записей стран
    #     """
    #     li = self.li_toc
    #     offset = li.ptr
    #     for _ in range(li.cnt):
    #         chidx = self.read_ch_idx(offset)
    #         offset += CH_IDX.size
    #         yield chidx


# -------------------------------------------------------------------------

if __name__ == '__main__':
    from QGIS_VDO.vdo.blocks import block_0x12, block_0x0A  # noqa
    from QGIS_VDO.vdo.consts import struct_UINT        # noqa
    from QGIS_VDO.vdo.datatypes import LIST        # noqa
    from QGIS_VDO.vdo.fixtures_vdo import vdo30, vdo34ee, vdobmv, vdo34bnl, vdoRu  # noqa

    # vdo = vdo30
    vdo = vdo34ee
    # vdo = vdobmv
    # vdo = vdo34bnl
    vdo = vdoRu

    bl_toc: block_0x12 = vdo.get_block(0)
    # начало - в блоке 0 есть информация о расположении начала поиска стран
    fl_start = bl_toc.get_farlist_ch_country()

    curr_idx = vdo.get_ch_idxs(fl_start.bladdr.offset + fl_start.list.ptr, fl_start.list.cnt)

    chars = list(curr_idx)

    ch = 'p'    # choused interactive from UI from chars

    (int_bladr, ch, is_out, int_list) = curr_idx[ch]

    offset_bl = (int_bladr >> 8) * vdo.segsize
    offset_near = ((int_list & 0xFFFF0000) >> 16)
    # offset = (int_bladr >> 4) * vdo.segsize + ((int_list & 0xFFFF0000) >> 16)
    cnt = int_list & 0xFFFF
    if is_out:
        # farlist to address file (0x0a, 0x0c, 0x0e, 0x10)
        # /      curr_names = vdo.get_ch_names(offset_bl, offset_near, cnt)
        # пффф, 0x0a в ru34 - ziped
        block_addr: block_0x0A = vdo.get_block(offset_bl)
        li = LIST(struct_UINT.pack(int_list))
        curr_names = {x.name : x for x in block_addr.get_brifs(li)}
        pass
    else:
        # is_out == 0, to idxses
        curr_idx = vdo.get_ch_idxs(offset_bl + offset_near, cnt)

    #
    if len(curr_names) == 1:
        # only one choice
        pass

    pass
    fl = bl_toc.get_farlist_ch_country()
    bl_ch_country = vdo.get_block(fl.bladdr, fl.list)

    # Все страны
    all_chidxs = bl_ch_country.get_chidxs()
    print(f"Всего стран: {len(all_chidxs)}")

    # Найти конкретную страну
    ru = bl_ch_country.find_chidx('R')
    if ru:
        print(f"Найдена: {ru.ch} -> {ru}")

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
