"""
CH_city = 0x0d  # fully parsed chars idxs
0x0B -> 0x0D 0x0F 0x11
"""

from vdo.blocks import block_0x0B
from vdo.datatypes import BLADDR


class block_0x0D(block_0x0B):
    """
    CH_city type 0x0d  # буквы городов idxs
    """
    def __init__(self, bl_addr: BLADDR) -> None:
        super().__init__(bl_addr)


# -------------------------------------------------------------------------

if __name__ == '__main__':

    from vdo.datatypes import CH_IDX, FAR_LIST, VDO_FILE
    from vdo.enums import en_TeleAtlasRegion, BlockType
    from vdo.blocks import block_0x12
    
    from vdo.blocks import block_0x0A

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
    #vdo = vdoRu
    #vdo = vdo30
    bla = BLADDR(b'\x00\x00\x00\x01', vdo)

    tos = block_0x12(vdo)

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
    # brif: block_0x0A.BRIF_0xA
    all_brifs = []
    r_more = None

    for brif in country_block.get_brifs(country_block.li_toc):
        all_brifs.append(brif)
        # 2734 ROSSIJA ValueError: 21 < not found in CARINET_LANGUAGE
        more = country_block.get_moreinfo(brif.p_MORE_INFO_0xA)
        # (v1, v2, v3, v4) = more.c1c2c3c4
        # pc = more.li_poi_categories
        categories = more.get_poi_categories()
        #(co1, co2) = more.co1co2()
        #print(brif.get_name(), brif.native_lang, more.is_DeutchBorder)
        
        if more.en_region == en_TeleAtlasRegion.ROSSIYA:
            r_more = more
        print(brif.get_name(), more.en_region.name)
        pass

    # block_0x0D из последнего more
    # ---------------------------------------------
    if r_more is not None:
        more = r_more
    fl_ch_cities: FAR_LIST = more.ch_idx_cityes

    find_seq = 'moo   '
    find_seq = 'moskva'
    find_seq = 'leningrad'
    find_seq = 'novosibirsk'

    def find_ch(block, li, ch_str):
        next_chi_li = li
        ch_idx_block = block_0x0D(block)

        for ch_for_find in ch_str:
            print(ch_for_find)
            chi = ch_idx_block.find_chidxs(next_chi_li, ch_for_find)
            if not chi:
                raise ValueError()
            if chi.is_out:
                ch_idx_block = block_0x0D(chi.bladdr)
                if ch_idx_block.head.bltype == BlockType.CITY:
                    break
            next_chi_li = chi.list
        res = ch_idx_block.head.bladdr._raw + next_chi_li._raw
        res = FAR_LIST(res, ch_idx_block.vdo)
        return res

    fl_finded = find_ch(fl_ch_cities.bladdr, fl_ch_cities.list, find_seq)
    print(fl_finded.bladdr)
    print(fl_finded.list)

    pass
    
    import struct
    from vdo.datatypes import BYTESTRUCT, BLSTART
    #0x09D1AE00
    bl_num = vdobmv.read(0x09D1AE00, 8)
    bl_head = BLSTART(bl_num, vdobmv)
    blo = block_0x0A(bl_head.bladdr)


    pass



