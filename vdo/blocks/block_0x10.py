"""
# noqa:
block_0x10
перечень POI, POI list
PREAMBULA_BLOCK = 0x30 - размер заголовка
S0_BRIFS - краткая информация
S1_MORE - детальная информация
S4_FAR - отсылка к точке роутинга

Сам по себе не используется, является справочником для
a) 0x07 -> 0x09 -> 0x08 -> 0x06 -> 0x10
b) 0x0b -> 0x0a -> 0x10 poi countris
c) 0x0d -> 0x0c -> 0x10 poi cities
d) 0x0f -> 0x0e -> 0x10 poi streets
???e) 0x0? -> 0x11 -> 0x10 ??? houses
"""

from typing import TYPE_CHECKING, Iterator
# from typing import TYPE_CHECKING, Union, Any, Optional, Iterator

if TYPE_CHECKING:       # pragma: no cover
    # Этот блок видит только Pylance, интерпретатор Python его игнорирует
    from _typeshed import ReadableBuffer
else:
    # Запасной вариант для рантайма, чтобы не было NameError
    ReadableBuffer = bytes


from QGIS_VDO.vdo.block_base import block_base
# from QGIS_VDO.vdo.enums import en_CARINET_LANGUAGE
from QGIS_VDO.vdo.geotypes import POI_BRIF, POI, POI_DETAILS     # COORD,
from QGIS_VDO.vdo.datatypes import (
    BYTESTRUCT,
    BLADDR,
    # LIST,
)


OFFSET_S0_BRIFS = 0x08      # LIST brif info
OFFSET_S1_MORE = 0x0c            # LIST more info
# OFFSETs 2,3,5,6,7 === 0
OFFSET_S4_FAR = 0x18            # FARLISTSs to 0x00 ?
OFFSET_S8_PREV0x10 = 0x28       # prev 0x10 in file
OFFSET_S9_NEXT0x10 = 0x2C       # next 0x10 in file
# 0x30... - BRIFs


# ===============================================


class block_0x10(block_base):
    """
    Справочник POI
    """
    # Жестко фиксируем слоты.
    __slots__ = ("s0_li_brif", "s1_li_more", "s4_li_far", "prev", "next")

    def __init__(self, bladdr: BLADDR) -> None:
        super().__init__(bladdr)

        self.s0_li_brif = self.read_list(OFFSET_S0_BRIFS)
        self.s1_li_more = self.read_list(OFFSET_S1_MORE)
        self.s4_li_far = self.read_list(OFFSET_S4_FAR)
        self.prev = self.read_bladdr(OFFSET_S8_PREV0x10)
        self.next = self.read_bladdr(OFFSET_S9_NEXT0x10)

    def get_poi(self, offset: int) -> POI:
        """
        Full POI info
        """
        # TODO: li_road after 0x00 block

        poi = POI(self._raw[offset:offset + POI_BRIF.size])

        poi.name = self.read_str(poi._ptr_name).upper()
        poi.locality = self.read_str(poi._ptr_locality).upper()

        if not poi._ptr_more:
            raise NotImplementedError(f"poi._ptr_more: {poi._ptr_more}")
        # если есть ссылка на детальную информацию
        det: POI_DETAILS = POI_DETAILS(self._raw[poi._ptr_more: poi._ptr_more + POI_DETAILS.size])

        poi.brand = self.read_str(det._ps_brand).upper()
        poi.postcode = self.read_str(det._ps_postcode)
        poi.phone = self.read_str(det._ps_phone)
        poi.houseno = self.read_str(det._ps_house)
        poi.country = self.read_str(det._ps_country).upper()
        poi.region = self.read_str(det._ps_region).upper()
        poi.city = self.read_str(det._ps_city).upper()
        poi.street = self.read_str(det._ps_street).upper()
        poi.coord = det.coord
        poi.id = det.id
        poi._zero1 = det.zero1

        #
        ptr = det.li_road.ptr
        for _ in range(det.li_road.cnt):
            poi.raw_road.append(BYTESTRUCT(self._raw[ptr:ptr + 8]))
            ptr += 8
        return poi
    
    # def get_poi_far(self, offset: int) -> POI_BRIF:
    #     """
    #     Возвращает один экземпляр класса POI_BRIF
    #     Args:
    #         offset: int - inblock offset
    #         is_with_details: bool - POI_BRIF или полный объект, с деталями
    #     Returns:
    #         poi: POI_BRIF ()
    #     """
    #     poi = read_far_poi(self.vdo, self.head.bladdr.value, offset)
    #     return poi
    
    #     poi = POI_BRIF(self.read(offset, POI_BRIF.size))
    #     if poi._ptr_name:
    #         poi.name = self.read_str(poi._ptr_name)
    #     if poi._ptr_city:
    #         poi.city = self.read_str(poi._ptr_city)

    #     # if is_with_roite

    #     return poi

    # -------------------------------------------------------
    #
    # def get_poi_old(self, offset: int) -> POI_BRIF:
    #     """
    #     """
    #     poi = POI_BRIF(self.read(offset, POI_BRIF.size))
    #     if poi._ptr_name:
    #         poi.name = self.read_str(poi._ptr_name)
    #     if poi._ptr_city:
    #         poi.city = self.read_str(poi._ptr_city)

    #     det = POI_DETAILS(self.read(poi._ptr_more, POI_DETAILS.size))
    #     if det._ps_brand:
    #         det.brand = self.read_str(det._ps_brand)
    #     if det._ps_postcode:
    #         det.postcode = self.read_str(det._ps_postcode)
    #     if det._ps_phone:
    #         det.phone = self.read_str(det._ps_phone)
    #     if det._ps_house:
    #         det.house = self.read_str(det._ps_house)
    #     if det._ps_country:
    #         det.country = self.read_str(det._ps_country)
    #     if det._ps_region:
    #         det.region = self.read_str(det._ps_region)
    #     if det._ps_city:
    #         det.city = self.read_str(det._ps_city)
    #     if det._ps_street:
    #         det.street = self.read_str(det._ps_street)

    #     poi.details = det
    #     return poi

    #
    def get_all_brifs(self) -> Iterator[POI_BRIF]:
        """
        0x00   2   NAME_PTR
        0x02   1    is_alias flag (0/1)
        0x03   1    en_CARINET_LANGUAGE.value
        0x04   2   LOCALITY_PTR  or 0; shown after the post-town initial ("S.-LOCALITY")
        0x06   2   DETAIL_PTR    byte offset of an S1 record
        """
        ptr = self.s0_li_brif.ptr
        for _ in range(self.s0_li_brif.cnt):
            brif = POI_BRIF(self._raw[ptr: ptr + POI_BRIF.size])
            brif.name = self.read_str(brif._ptr_name)
            brif.locality = self.read_str(brif._ptr_locality)
            ptr += POI_BRIF.size
            yield brif


# ------------------------------------------------------

if __name__ == '__main__':
    #
    from QGIS_VDO.vdo.fixtures_vdo import vdo34bnl as vdo

    bla = vdo.get_bladdr(0x76bb08)
    blo: block_0x10 = vdo.get_block(bla)

    brifs = [brif for brif in blo.get_all_brifs()]

    pass


"""
#noqa:
---------------------------------------------------------
(c)
#### 8.1.1 Type `0x10` — POI parcel (name, address, phone, absolute position)

All `0x10` blocks on both CD discs are CF=0. The section descriptor at `0x08` has the
shape `[(o0, n0), (o1, n1), (0,0), (0,0), (o4, n4), (0,0)]`; `o0` is 40 on DB-REL 22
and 48 on DB-REL 34, so read it from the descriptor. On DB-REL 22 the header ends with two
`u32 BLOCK_ID`s at `+0x20` / `+0x24`: the next and the previous `0x10` block (620 / 620 chain
back). Measured over CD-ID 2952 (92,774 detail records) unless noted. S4 holds one
8-byte road link per detail record: `u32 BLOCK_ID` of a `0x00` tile, `u16` offset of the
segment record (in the decoded tile if it is packed), `u16` 0 or 1 (unknown; perhaps the side
of the road). On CD-ID 2952 the linked segment's name is the detail's street (445 / 445 sampled).
The strings follow S4. **Every string pointer below is a
plain byte offset from the start of the block** (header included) to a Latin-1,
`\0`-terminated string; `0` means absent.

S0 — `n0` index records, 8 bytes:

```
 off  size  field
 0x00   2   NAME_PTR
 0x02   2   TYPE          (2 in 94% of records on DB-REL 22, >99% on DB-REL 34)
 0x04   2   LOCALITY_PTR  or 0; shown after the post-town initial ("S.-LOCALITY")
 0x06   2   DETAIL_PTR    byte offset of an S1 record
```

`n0 >= n1`: several index records can share one detail record (alternate names).

S1 — `n1` detail records, 40 bytes (`T[0x2f]`; the other candidate, `T[0x51]`, is 28
on DB-REL 22):

```
 off  size  field
 0x00   4   X             absolute, same frame as §7
 0x04   4   Y
 0x08   2   LINK_PTR      byte offset of an S4 road link (the record's own in 77,711 / 92,774)
 0x0A   2   1             (92,305 / 92,774 on CD-ID 2952)
 0x0C   2   BRAND_PTR     or 0
 0x0E   2   STREET_PTR
 0x10   2   CITY_PTR
 0x12   2   COUNTY_PTR
 0x14   2   COUNTRY_PTR   (`england`, `scotland`, `wales`, `france`, …)
 0x16   4   0             (92,308 / 92,774)
 0x1A   2   HOUSE_NO_PTR
 0x1C   4   POI_ID        u16 prefix (0x0113, 0x0114, 0x0115, … on CD-ID 2952) + u16 serial;
                          the same in every copy of the POI and in its 0x06 records
 0x20   2   PHONE_PTR
 0x22   2   POSTCODE_PTR  (outward code + first inward digit, e.g. "sw7 2"; 0 on DB-REL 22)
 0x24   4   0             (all)
```

Measured over every `0x10` block:

| | CD-ID 2952 (DB-REL 22) | CD-ID 21594 (DB-REL 34) |
|---|---|---|
| blocks / S0 records | 620 / 119,006 | 4,787 / 844,749 |
| `DETAIL_PTR` lands on an S1 record boundary | 119,006 | 844,749 |
| `NAME_PTR` resolves to a string | 117,920 | 840,706 |
| (X, Y) inside Europe | 119,006 | 844,749 |
| `STREET_PTR` non-zero / resolves | 92,144 / 92,142 | 781,916 / 781,898 |
| `PHONE_PTR` non-zero / resolves | 33,992 / 33,992 | 688,901 / 688,901 |
| `POSTCODE_PTR` non-zero / resolves | 0 | 764,848 / 764,848 |

Example (CD-ID 21594, block at 2048-byte sector 54542, S0 record at `0x480`):
`royal albert hall` → street `kensington road`, phone `+442075898212`, postcode
`sw7 2`, X/Y → **51.50153 N, 0.17716 W**. The same POI is repeated in several `0x10`
blocks: a branded POI has a category copy and a brand copy (`01-architecture.md` §4.4.2).

On a CNI1 (CD-ID 2952) the POI lists show the brand in front of the name. Moving a POI (detail
X/Y and its `0x06` record) or pointing its road link at another road keeps it routable; renaming
it does too, as long as the name stays in order in its letter's `0x11` leaf
(`01-architecture.md` §4.4.2).

Positions agree with OpenStreetMap to within tens of metres for distinctive names
(median 52 m over the 28 name matches in one CD-ID 21594 parcel, a figure that
still includes common names such as chain pubs matched to an unrelated venue). CD-ID 2952 is
more coarsely geocoded: distinct POIs at one address can share a coordinate.

-------------------------------------------------------------------------------
//{ BT_0x10
typedef struct{
    BL_HEAD head; // заголовок
        local ushort size <format=hex, hidden=true> = head.addr.size * 0x800; // size of this block
        local uint   offset <hidden=true> = head.addr.offset;
        if(head.is_compressed){
            DWORD   q[4]<bgcolor=cLtPurple>;
            break;
        }
    LIST pl_brif;
    LIST pl_moreinfo;
    CONST_I hex0000(0);
    CONST_I hex0001(0);
    LIST    p_data0x00;
    CONST_I hex0002(0);
    CONST_I hex0003(0);
    CONST_I hex0004(0);
    BL_ADDR bl_next_0x10;
    BL_ADDR bl_prev_0x10;
    //-----end toc , :data from 0x30
    BRIF_0x10 brif[pl_brif.cnt] <optimize=false>;
    MORE_INFO_0x10  more_info[pl_moreinfo.cnt] <optimize=false>;

    FAR_LIST data0x00[p_data0x00.cnt] <optimize=false>;
    /*
    LIST data_zero_not2str;
    LON_LAT corner_bott_left, corner_upper_right;
    //====
    unk_main item[data.cnt]<optimize=false>;
    */
    byte end <bgcolor=cLtPurple>;
}BT_0x10 <read=Read_BT_0x10>;
string Read_BT_0x10(BT_0x10 &a ){
    local string s;
    /*if(a.head.is_compressed){
        SPrintf(s, "Block 0x10 compressed. STOP parsing!");
        SPrintf(s, "%08X %08X %08X %08X", a.q[0], a.q[1], a.q[2], a.q[3]);
    }else{
        //SPrintf(s, "DB ver. %i (0x%x) %s, %s", a.db_ver, a.db_ver,
            //a.label, a.description);
            */
    s = "0x10";
    //}
    return s;
}
// --------------------------------------------------------------------
/*
BRIF_0x10    byte[8]
    PSTR    WORD pstr_name nearPtr to 0-ended str
    byte    in 0xA is_synonim - flag alias or main mame
    byte    in 0xA en_lang - enum country native language
    const ushort    zero(0)  allways 0
    PTR      p_moreinfo near ptr to item of MORE_INFO_0xA
*/
typedef struct {
    local ushort size <format=hex, hidden=true> = head.addr.size * 0x800; // size of this block
    local uint   offset <hidden=true> = head.addr.offset; // absolute block offset
    PSTR    name;        //object name - nearPtr to 0-ended str
    en_TYPE_ADDR   is_synonim;  //in 0xA is_synonim - flag alias or main mame
    en_LANGUAGE en_lang;   ////in 0xA en_lang - enum country native language
    PSTR    name_city;      // city name?
    PTR     p_moreinfo;    // near ptr to item of MORE_INFO_0xA
}BRIF_0x10<read=ReadBRIF_0x10>;
string ReadBRIF_0x10(BRIF_0x10 &a){
    local string s;
    SPrintf(s, "%s= %s : %s",
    EnumToString(a.en_lang),
    a.name.str,
    a.name_city.str);
    return s;
    }


// MORE_INFO_0x10
typedef struct{
    local ushort size <format=hex, hidden=true> = head.addr.size * 0x800; // size of this block
    local uint   offset <hidden=true> = head.addr.offset; // absolute block offset
    LON_LAT     coord;
    LIST    p_fptr_0x00;
    PSTR    p_name;
    PSTR    p_post_addr_street;
    PSTR    p_post_addr_city;
    PSTR    p_post_addr_region;
    PSTR    p_post_addr_country;
    // is_multilang - а вот не факт, Сплит аэропорт многоязычный, но = 0
    ushort  is_multilang <bgcolor=cBlue,  fgcolor=cLtYellow>;   //0-no, 1- some items in brif to this addr
    CONST_S  align2(0);
    PSTR    p_post_addr_building;
    DWORD   id_poi  <bgcolor=cLtYellow, fgcolor=cLtBlue, format=hex>;
// id = id in bl_0x06:  03 06 4e 05
    PSTR  p_post_addr_phone;
    PSTR  p_post_addr_index;
    CONST_I align3(0);
}MORE_INFO_0x10<read=ReadMORE_INFO_0x10>;
string ReadMORE_INFO_0x10(MORE_INFO_0x10 &a){
    local string s;
    SPrintf(s, "%s : %s, %s, %s, %s",
        a.p_name.str,
        a.p_post_addr_country.str,
        a.p_post_addr_city.str,
        a.p_post_addr_street.str,
        a.p_post_addr_building.str
        );
    return s;
    }
"""
