"""
CH_country = 0x0b  # fully parsed chars idxs
0x0B -> 0x0D 0x0F 0x11

lzw packeble
"""
import struct

from typing import Iterator

from QGIS_VDO.vdo.block_base import block_base
from QGIS_VDO.vdo.datatypes import BYTESTRUCT, BLADDR, LIST, FAR_LIST, VDO_FILE
from QGIS_VDO.vdo.datatypes import OFFSET_TOC
from QGIS_VDO.vdo.enums import en_CARINET_LANGUAGE, en_POI_CAT, en_TeleAtlasRegion


class BRIF_0xA(BYTESTRUCT):
    '''
    BRIF_0xA    byte[8]
    Args:
        buffer: byteadday длиной >= 8
        baseoffset: offset блока, в котором работаем
    Attributes:
        0: PSTR    WORD pstr_name nearPtr to 0-ended str
        2: byte    is_alias - flag alias or main name
        3: byte    en_native_lang - enum country native language
        4: const ushort    zero(0)  allways 0
        6: WORD      p_moreinfo near ptr to item of MORE_INFO_0xA
        tst = BRIF_0xA(b'\x00\x10\x01\x07\x00\x00\x01\x00')
    '''
    size: int = 8

    def __init__(self, buffer: bytearray, parent: block_base) -> None:
        super().__init__(buffer, BRIF_0xA.size)       # 8 - self.bytescnt
        self.parent = parent
        
    @property
    def ptr_name(self) -> int:
        """ pointer to zero-ended string (?) - name """
        return self.ushort(0)
    
    @property
    def is_alias(self) -> bool:
        """ Brif - is alias (oesterreich is alias for österreich """
        return self.uchar(2) == 1
    
    @property
    def native_lang(self) -> str:
        """ На каком языке разговаривают в стране """
        en = self.uchar(3)
        try:
            enl = en_CARINET_LANGUAGE(en).name
        except ValueError:          # Exception as e:
            enl = f"ValueError: {en} < not found in CARINET_LANGUAGE"
        return enl
    
    @property
    def p_MORE_INFO_0xA(self) -> int:
        """ ptr на блок с большим количеством информации """
        return self.ushort(6)

    def get_name(self) -> str:
        """
        Return:
            str: строковое имя
        """
        return self.parent.read_str(self.ptr_name)


# -------------------------------------------------------------------------

class MORE_INFO_0xA(BYTESTRUCT):
    '''
    # noqa: E501, W291
    MORE_INFO_0xA  2+4+1+2+1+1 |+ 3 *DWORD (byte[56=38h]in34, 
    Args:
        buffer: byteadday длиной >= 8
        baseoffset: offset блока, в котором работаем
    Attributes:
        0: +QWORD   idx_ch_cityes - FAR_PTR 
        8: const DWORD =11; 12: const DWORD =22; 
        16: const DWORD =33; 20: const DWORD =44  (00 00 00 0b 00 00 00 16 00 00 00 21 00 00 00 2c )
        24: +DWORD   pl_addinfo LIST на POI_CATEGORY (напр, архитектура, музеи, порты, парки и т.п)
        28: const DWORD =0x01f4012c(dec 32768300); 32768 2^{15}, max short integer
        32: const DWORD =0x03e801f4(dec 65536500) (2^{16} = 65536)
        36: +WORD    is_island   1 - Это же остров!
        38: +WORD    is_DeutchBorder       1 - Страна - часть Евросоюза (или шенгена? вопрос...)
        40: +WORD    en_eng_strname - enum United Nations - номер в списке стран ООН 
                                (на актуальный составлению год) United Nations
        WORD align
        if ver 34
            44: WORD align
            46: DWORD alpha_2_ISO3166_1 - 2-3 ch и 0 последний (nl, pl, ru, cz и т.п.)
            50 const DWORD =0x2d2d2d00 (str='---\0')
            WORD align
    '''
    
    size: int = 44

    def __init__(self, buffer: bytearray, parent: block_base) -> None:
        self.size = 56 if parent.dbrev == 34 else 44
        super().__init__(buffer, self.size)       # 8 - self.bytescnt
        self.parent = parent

    @property
    def ch_idx_cityes(self) -> FAR_LIST:
        """
        ch_idx - на НАИМЕНОВАНИЯ городов страны (каждый может писаться по-разному)
        offset 0: FAR_LIST на блок CH_city = 0x0d, ch_idx_cityes
        """
        # return self.parent.farlist(0)
        return FAR_LIST(self._raw[:FAR_LIST.size], self.parent.vdo)

    @property
    def c1c2c3c4(self) -> tuple:
        """ offset 8
        Returns:
            8: const DWORD =11; 12: const DWORD =22
            16: const DWORD =33; 20: const DWORD =44
        Example:
            (00 00 00 0b 00 00 00 16 00 00 00 21 00 00 00 2c )

            а не MAP_AREA ли это??????
        """
        (c1, c2, c3, c4) = struct.unpack(">LLLL", self._raw[8:24])
        if c1 != 11 or c2 != 22 or c3 != 33 or c4 != 44:
            # вообще это константы
            raise ValueError(c1, c2, c3, c4, "траблема: 11, 22, 33, 44?")
        return (c1, c2, c3, c4)
    
    @property
    def li_poi_categories(self) -> LIST:
        """
        offset 24
        24: +DWORD   pl_addinfo LIST на POI_CATEGORY
        (напр, архитектура, музеи, порты, парки и т.п)
        """
        return LIST(self.read(24, LIST.size))

    @property
    def co1co2(self) -> tuple:
        """ offset 28
        Returns:
            28: const DWORD =0x01f4012c(dec 32768300); 32768 2^{15}, max short integer
            32: const DWORD =0x03e801f4(dec 65536500) (2^{16} = 65536)
        Example:
            ( 01f4012c 03e801f4 )
        """
        (co1, co2) = struct.unpack(">LL", self._raw[28:36])
        if co1 != 32768300 or co2 != 65536500:
            # вообще это константы
            raise ValueError(co1, co2, "траблема: 32768300, 65536500?")
        return (co1, co2)

    @property
    def is_island(self) -> bool:
        """
        36: +WORD    is_island   1 - Это же остров!
        """
        return self.ushort(36) == 1

    @property
    def is_DeutchBorder(self) -> bool:
        """
        38: +WORD    is_DeutchBorder
            1 - Страна - часть Евросоюза (или шенгена? вопрос...)
        bmw - 2013 - Дания=0, но в ЕС с 1973
        Дания - страна 1го въезда по шенгену
        вообще общего - только что граничат с Германией и все в шенгене
        """
        return self.ushort(38) == 1

    @property
    def en_region(self):
        """
        40: +WORD    en_eng_strname - enum United Nations - номер в списке стран ООН 
                                (на актуальный составлению год) United Nations
        # noqa: E501, W291
        vdoRu
        Предоставленный вами список база данных европейских стран из автомобильной 
        навигационной системы (вероятнее всего, карт семейства TeleAtlas).
        Это можно легко определить по техническим признакам структуры списка:
        Наличие Ватикана (id 229), Монако (id 141), Сан-Марино (id 183) и Андорры (id 5): 
        Эти микрогосударства включены в список, так как они нанесены на дорожные карты Европы, 
        хотя Ватикан не является членом ООН (имеет статус постоянного наблюдателя).
        Специфические ID: Числа рядом с названиями — это внутренние системные идентификаторы 
        регионов навигационного диска или прошивки, а не официальные коды ООН или ISO.
        Ошибки кодировки: Символы вроде espańa (Испания) и cittŕ (Ватикан) выдают классический 
        сбой расширенной кодировки ASCII (Latin-1 / ISO-8859-1), которая использовалась в старых 
        бортовых компьютерах автомобилей в конце 2000-х — первой половине 2010-х годов
        """
        ret = en_TeleAtlasRegion(self.ushort(40))
        return ret

    @property
    def get_ISO_code(self) -> str:
        """
        46: DWORD alpha_2_ISO3166_1 - 2-3 ch и 0 последний (nl, pl, ru, cz и т.п.)
            const DWORD =0x2d2d2d00 (str='---\0')
        """
        return self.read_str(46, 4)

    @property
    def get_c_tail(self) -> str:
        """
        50: const DWORD =0x2d2d2d00 (str='---\0')
        """
        return self.read_str(50, 4)

    def get_poi_categories(self) -> list:
        """ Список категорий географических POI """
        res = []
        offset = self.li_poi_categories.ptr
        for i in range(self.li_poi_categories.cnt):
            res.append(self.parent.get_poi_category(offset))
            # POI_CATEGORY 3*DWORD = 12
            offset += 12
        return res


# -------------------------------------------------------------------------

class block_0x0A(block_base):
    """ CH_country type 0x0b  # fully parsed chars idxs """

    def __init__(self, bl_addr: BLADDR) -> None:
        super().__init__(bl_addr)

    @property
    def li_toc(self):
        """ LIST to table of contents """
        return self.read_list(OFFSET_TOC)

    def get_brifs(self, li: LIST) -> Iterator[BRIF_0xA]:
        """ Итератор BRIF_0xA из li: ptr-cnt
        Args:
            li: LIST - ptr-cnt массива BRIF_0xA
        Yelds:
            array: of BRIF_0xA
        Example:
            получение CH_IDX:\n
                for ci in country_block.get_brifs(country_block.li_toc ):
                    print(ci.ptr_name, ci.native_lang)\n

        """
        offset = li.ptr
        for _ in range(li.cnt):
            brif = BRIF_0xA(self.read(offset, BRIF_0xA.size), self)
            offset += BRIF_0xA.size
            yield brif

    def get_moreinfo(self, ptr: int) -> MORE_INFO_0xA:
        """ """
        mi_size = 56 if self.dbrev == 34 else 44
        buf = self.read(ptr, mi_size)
        moreinfo = MORE_INFO_0xA(buf, self)
        return moreinfo

    def get_poi_category(self, ptr: int) -> tuple:
        """
        POI_CATEGORY 3*DWORD = 12
            QWORD   POIs  FAR_LIST
            WORD    en_cat_places - enum тип, категория POI
            WORD    reference_addr_start
                    В bl type 0x0a - УКАЗЫВАЕТ НА НАЧАЛО СТРОКОВЫХ ДАННЫХ?????
        """
        fl_cat_poi = FAR_LIST(self.read(ptr, FAR_LIST.size), self.vdo)
        en_cat_poi = en_POI_CAT(self.ushort(ptr + 8))  # 8 = 0 + FAR_LIST.size
        ref_addr = self.ushort(ptr + 12)      # # 8 = 0 + FAR_LIST.size + 4
        return (fl_cat_poi, en_cat_poi, ref_addr)


# -------------------------------------------------------------------------

if __name__ == '__main__':

    from QGIS_VDO.vdo.datatypes import CH_IDX
    from QGIS_VDO.vdo.blocks import block_0x12
    from QGIS_VDO.vdo.blocks import block_0x0B

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
    vdo = vdo30
    bla = BLADDR(b'\x00\x00\x00\x01', vdo)

    tos = block_0x12(bla)

    # ba0x13 = tos.bladdr_bibliogr
    # ba0x07 = tos.bladdr_scales
    ba0x0b = tos.bladdr_ch_country

    fl_ch_country = tos.get_farlist_ch_country()
    ch_country = block_0x0B(ba0x0b)

    arr: CH_IDX = []
    for ch in ch_country.get_indexes(ch_country.li_toc):
        arr.append(ch)

    # block_0x0A
    # ---------------------------------------------

    country_block = block_0x0A(arr[2].bladdr)

    # BRIF_0xA
    brif: BRIF_0xA
    all_brifs = []
    for brif in country_block.get_brifs(country_block.li_toc):
        all_brifs.append(brif)
        
        # 2734 ROSSIJA ValueError: 21 < not found in CARINET_LANGUAGE
        more = country_block.get_moreinfo(brif.p_MORE_INFO_0xA)
        # (v1, v2, v3, v4) = more.c1c2c3c4
        # pc = more.li_poi_categories
        categories = more.get_poi_categories()
        #(co1, co2) = more.co1co2()
        #print(brif.get_name(), brif.native_lang, more.is_DeutchBorder)
        print(brif.get_name(), more.en_region.name)
        pass

    #
    pass


"""
# noqa: E501, W291
POI_CATEGORY 3*DWORD
    QWORD   POIs  FAR_LIST
    WORD    en_cat_places - enum тип, категория POI 
    WORD    reference_addr_start  В 0X0a - УКАЗЫВАЕТ НА НАЧАЛО СТРОКОВЫХ ДАННЫХ
*/
// --------------------------------------------------------------------
struct BRIF_0xA;
struct MORE_INFO_0xA;
struct POI_CATEGORY;

//{BT_0x0A
typedef struct{
    BL_HEAD head; // заголовок
  local ushort size <format=hex, hidden=true> = head.addr.size * 0x800; // size of this block  
  local uint   offset <hidden=true> = head.addr.offset;   // absolute block offset  
    if(head.is_compressed){
        DWORD   q[8]<bgcolor=cLtPurple>;
        break;
    }
    LIST    pl_all_countries;  // brief geo info
    LIST    pl_all_moreinfo;   // more info, ptrs from briefs
    //pl_all_POIs - outer links to ch_idx file 0x11 type
    CONST_I zero(0); LIST pl_all_POIs;  CONST_I zero(0);  CONST_I zero(0); 
    CONST_I zero(0); CONST_I zero(0);   CONST_I zero(0);  CONST_I zero(0); 

    BRIF_0xA country[pl_all_countries.cnt] <optimize=false>;  // main data
/*
    MORE_INFO_0xA   more_info[pl_all_moreinfo.cnt] <optimize=false>;
NO NEED MADE THIS ARRAY - ALL ITEMS WILL BE CREATD FROM brief_geo ptrs
    FSeek(pl_all_POIs.offset); // pl_all_addinfo - byte after more_info
     COUNTRY_POI_0xA addinfo[pl_all_POIs.cnt] <optimize=false>;
NO NEED MADE THIS ARRAY - ALL ITEMS WILL BE CREATD FROM brief_geo ptrs
*/
    byte   marker_after_all <bgcolor=cPurple, fgcolor=cWhite>;
}BT_0x0A<read = Read_BT_0x0A>;

string Read_BT_0x0A(BT_0x0A &a ){
    local string s="block 0A";
    if(a.head.is_compressed){
        SPrintf(s, "Block 0x0A compressed. STOP parsing!");
        SPrintf(s, "%08X %08X\n%08X %08X %08X %08X\n", a.q[0], a.q[1], a.q[2], a.q[3], a.q[4], a.q[5]);
        SPrintf(s, "%s%08X %08X", s,  a.q[6], a.q[7]);
    }
    return s;
}
//}BT_0x0A

// --------------------------------------------------------------------
/*
BRIF_0xA    2*DWORD / byte[8]
    PSTR    WORD pstr_name nearPtr to 0-ended str
    byte    is_synonim - flag alias or main mame
    byte    en_lang - enum country native language 
    const ushort    zero(0)  allways 0
    WORD      p_moreinfo near ptr to item of MORE_INFO_0xA
*/
//{BRIF_0xA; main data 0xA - BRIF_0xA
typedef     struct{
    local ushort size <format=hex, hidden=true> = head.addr.size * 0x800; // size of this block  
    local uint   offset <hidden=true> = head.addr.offset; // absolute block offset
    PSTR        pstr_name;  // ptr to zero-ended str
    en_TYPE_ADDR   is_synonym;// !!! carindb_rus.0xA.osterreich = 1 
    en_LANGUAGE     en_lang;// language code
    CONST_S     zero(0);    // ushort allways 0
    PTR         p_moreinfo<hidden=true>; // ptr to item of LIST pl_all_moreinfo;
    // jump to MORE_INFO
    local uint return_here <hidden=true> = FTell();
    FSeek(p_moreinfo.ptr + offset);
        MORE_INFO_0xA more_info;    
    FSeek(return_here);
}BRIF_0xA<read=Read_BRIF_0xA>;
string Read_BRIF_0xA(BRIF_0xA &a){
    local string s;
    SPrintf(s, "%s: `%s`. Lang: %s, add_cnt:[%i]",
        EnumToString(a.more_info.en_eng_strname), 
        a.pstr_name.str, EnumToString(a.en_lang),
        a.more_info.pl_category_POI.cnt
        );
    return s;
}

//}BRIF_0xA;
// --------------------------------------------------------------------
/*
MORE_INFO_0xA  2+4+1+2+1+1 |+ 3 *DWORD
    QWORD   idx_ch_cityes - FAR_PTR 
    const DWORD =11; const DWORD =22; const DWORD =33; const DWORD =44
    DWORD   pl_addinfo LIST категорий POI (напр, архитектура, музеи, порты, парки и т.п)
    const DWORD =0x01f4012c(dec 32768300); const DWORD =0x03e801f4(dec 65536500) 
    WORD    is_island   1 - Это же остров!
    WORD    is_EU       1 - Страна - часть Евросоюза (или шенгена? вопрос...)
    WORD    en_eng_strname - enum - номер в списке стран ООН (на актуальный составлению год)
    WORD align
if ver 34
    WORD align
    DWORD alpha_2_ISO3166_1 - 2-3 ch и 0последний (nl, pl, ru, cz и т.п.)
    const DWORD =0x2d2d2d00 (str='---\0')
    WORD align
*/
//MORE_INFO_0xA; - call from BRIF_0xA
typedef struct{
    local ushort size <format=hex, hidden=true> = head.addr.size * 0x800; // size of this block  
    local uint   offset < hidden=true> = head.addr.offset;     // absolute block offset
    FAR_LIST     idx_ch_cityes;   // ch_idx with country cityes
    //make list ch
// try make citylist from ch_idx values
// TOOooooo slow - 5-10 seconds...
    if(idx_ch_cityes.pl_data.cnt){ // count>0
        local uint ret_city_here <hidden=true> = FTell();
        FSeek(idx_ch_cityes.pl_data.offset);
        struct{
                CH_IDX city[idx_ch_cityes.pl_data.cnt]<optimize=false>; // ch_idx type data elements
        }FoldedCityes<optimize=false>;
        FSeek(ret_city_here);
    }
    CONST_I dec_11(0x0B) <hidden=true>;
    CONST_I dec_22(0x16) <hidden=true>;
    CONST_I dec_33(0x21) <hidden=true>;
    CONST_I dec_44(0x2C) <hidden=true>;
    LIST    pl_category_POI; // LIST категорий POI (напр, архитектура, музеи, порты, парки и т.п)
    CONST_I hex01f4012c(0x01f4012c); // dec 32768300
    CONST_I hex03e801f4(0x03e801f4); // dec 65536500
    ushort       is_island <bgcolor=cLtBlue>;
    if((is_island & ~1)) {     // !=0, !=1
        Printf (" is_island = %i\n", is_island); // !=0, !=1
        FSeek(FTell()-2); ushort is_island <bgcolor=cRed, fgcolor=cAqua>;
    }
    ushort      is_EU <bgcolor=cLtBlue>;
    if(is_EU & ~1){      // !=0, !=1
        Printf (" is_EU = %i\n", is_EU);
        FSeek(FTell()-2); ushort is_EU <bgcolor=cRed, fgcolor=cAqua>;
    }
    en_GEO_COUNTRY      en_eng_strname<fgcolor=cDkGreen, bgcolor=cGreen>;
    CONST_S     aligment(0);
    if(IS_OFICIAL_MAP){
        CONST_S     zero2(0);
        //https://ru.wikipedia.org/wiki/ISO_3166-1
        string   alpha_2_ISO3166_1 <bgcolor=cLtGreen, fgcolor=cDkYellow>;
        CONST_B  aligment_b(0);
        string   const_triple_defice <bgcolor=cLtGreen,fgcolor=cDkYellow,hidden=true>;
        CONST_S  aligment_s(0); 
    }    
    // call ADDINFO_0xA
    if(pl_category_POI.cnt){ // if pl_addinfo != 0
        local uint return_here <hidden=true> = FTell();
        FSeek(pl_category_POI.offset);
            POI_CATEGORY country_POI[pl_category_POI.cnt] <optimize=false>;
        FSeek(return_here);
    }
}MORE_INFO_0xA<read=Read_MORE_INFO_0xA>;
string Read_MORE_INFO_0xA(MORE_INFO_0xA &a){
    local string s;
    if(a.head.is_compressed){
        SPrintf(s, "Block 0x13 compressed. STOP parsing!");
        SPrintf(s, "%08X %08X %08X %08X", a.q[0], a.q[1], a.q[2], a.q[3]);
    }else{
        SPrintf(s, "%s",EnumToString(a.en_eng_strname));
        if(exists(a.alpha_2_ISO3166_1)) SPrintf(s, "%s, '%s'", s, a.alpha_2_ISO3166_1);
        if(a.is_EU) SPrintf(s, "%s, EU", s);
        if(a.is_island) SPrintf(s, "%s, island", s); /// Iseland in rus map - not iseland))
        SPrintf(s,"%s . add_cnt:[%i]", s, a.pl_category_POI.cnt);
    }
    return s;
}
//}MORE_INFO_0xA;


"""
