"""

# noqa:

from scale1?

PREAMBULA_BLOCK = 0x20 - размер заголовка
BLHEAD 
LIST S0_
LIST S1_const_zero?
MAP area

"""

import struct

from typing import TYPE_CHECKING, Iterator
# from typing import TYPE_CHECKING, Union, Any, Optional, Iterator

if TYPE_CHECKING:       # pragma: no cover
    # Этот блок видит только Pylance, интерпретатор Python его игнорирует
    from _typeshed import ReadableBuffer
else:
    # Запасной вариант для рантайма, чтобы не было NameError
    ReadableBuffer = bytes


from QGIS_VDO.vdo.block_base import block_base
from QGIS_VDO.vdo.datatypes import BYTESTRUCT, BLADDR
from QGIS_VDO.vdo.geotypes import MAP_AREA, COORD
from QGIS_VDO.vdo.enums import en_POI_CAT


OFFSET_S0_ITEMS = 0x08      # LIST items
OFFSET_S1_ZERO = 0x0c       # LIST? eq 00000000
OFFSET_MAP_AREA = 0x10


POI_ITEM_struct = struct.Struct(">LHHHHHHLLL")
# ------------------------------------------------------------------


# ------------------------------------------------------------------

class POI_ITEM(BYTESTRUCT):
    """
    (c) fdemusso
    off  size  field
    0x00   4   BLOCK_ID of the 0x10 block (POI parcel, §8.1.1) holding this POI's details
    0x04   2   byte offset, within that 0x10 block, of this POI's S0 index record (§8.1.1)
    0x06   2   LOCAL_X    position in tile, step 64        <- sorted ascending
    0x08   2   LOCAL_Y    position in tile, step 64
    0x0A   2   CATEGORY   (12 petrol, 21 hotels, 37 landmarks, 48 towns, …; 01-architecture.md §4.4.1)
    0x0C   2   BRAND      offset of the POI's brand in this block's name blob, 0 = no brand
    0x0E   2   0, or 1 on a few ports and airports (187 records on CD-ID 2952, 240 on CD-ID 21594)
    0x10   4   POI_ID     the 0x10 detail record's +0x1C (§8.1.1); read before as a "brand reference"
    0x14   8   0          DB-REL 34 only: the 20-byte form (DB-REL 22) ends at 0x14
    """
    size: int = 0x1c

    def __init__(self, buffer: ReadableBuffer):
        super().__init__(buffer)
        # 0x0E   2   0, or 1 on a few ports and airports - closed regular use flag?
        (self._bladr10, self._ptr10, self._LOCAL_X, self._LOCAL_Y,
            en_cat, self._p_brand, self.is_custom,
            self.id, zero1, zero2) = POI_ITEM_struct.unpack_from(self._raw, 0)  # (">LHHHHHHHLLL"
        self._cat = en_POI_CAT(en_cat)
        self.brand = ''
        self.bladdr = None
        if zero1 or zero2:
            raise NotImplementedError(f"z1: {zero1}, z2: {zero2}")
        self.coord = None
        self.poi = None

    def __repr__(self):
        s = f"{self.cat}: {self.brand}"
        return s

    @property
    def cat(self):
        return self._cat.name

# ------------------------------------------------------------------


class block_0x06(block_base):
    """

    """
    def __init__(self, bladdr: BLADDR) -> None:
        super().__init__(bladdr)

        self.s0_li_items = self.read_list(OFFSET_S0_ITEMS)
        self.area = MAP_AREA(self.read(OFFSET_MAP_AREA, MAP_AREA.size))
        zero = self.uint(OFFSET_S1_ZERO)
        if zero:
            raise NotImplementedError(f"Not zero: {zero}")

    #
    def get_all_items(self, is_load_extended=False) -> Iterator[POI_ITEM]:
        """
        Оптимизированная версия:
        - Предварительный срез буфера POI (zero-copy memoryview)
        - offset += size вместо умножения в цикле
        - Кэширование base_hlon/base_hlat вне цикла
        """
        base_ptr = self.s0_li_items.ptr
        cnt = self.s0_li_items.cnt
        size = POI_ITEM.size
        
        # Один zero-copy срез всего массива POI
        poi_buffer = self._raw[base_ptr : base_ptr + cnt * size]
        
        # Кэширование базовых координат вне цикла
        base_hlon = self.area.left_bottom._hlon
        base_hlat = self.area.left_bottom._hlat
        
        offset = 0
        for _ in range(cnt):
            item = POI_ITEM(poi_buffer[offset : offset + size])
            
            if item._p_brand:
                item.brand = self.read_str(item._p_brand).upper()
            
            # LOCAL_X/Y * 64 = << 8
            item.coord = COORD(
                base_hlon + (item._LOCAL_X << 8),
                base_hlat + (item._LOCAL_Y << 8)
            )
            
            if is_load_extended:
                item.bladdr = self.vdo.get_bladdr(item._bladr10)
                bl_0x10 = self.vdo.get_block(item.bladdr)
                item.poi = bl_0x10.get_poi(item._ptr10)
            
            yield item
            offset += size

        
# ------------------------------------------------------

if __name__ == '__main__':
    #
    from QGIS_VDO.vdo.fixtures_vdo import vdo34bnl as vdo

    # bnl 0x8f4a06
    bla = vdo.get_bladdr(0x8f4a06)
    blo: block_0x06 = vdo.get_block(bla)

    items = [item for item in blo.get_all_items(is_load_extended=True)]

    # arr_more = []
    # for it in items:
    #     bl_details = blo.vdo.get_block(it.bladdr)
    #     poi = bl_details.get_poi(it._ptr10)
    #     it.de
    #     arr_more.append[det]
    pass

"""
# noqa: (C) 
## 8. Georeferenced Record Formats

### 8.1 Type `0x06` — POI Record, **`T[0x32]` bytes** (28 on DB-REL 34, 20 on DB-REL 22)

```
 off  size  field
 0x00   4   BLOCK_ID of the 0x10 block (POI parcel, §8.1.1) holding this POI's details
 0x04   2   byte offset, within that 0x10 block, of this POI's S0 index record (§8.1.1)
 0x06   2   LOCAL_X    position in tile, step 64        <- sorted ascending
 0x08   2   LOCAL_Y    position in tile, step 64
 0x0A   2   CATEGORY   (12 petrol, 21 hotels, 37 landmarks, 48 towns, …; 01-architecture.md §4.4.1)
 0x0C   2   BRAND      offset of the POI's brand in this block's name blob, 0 = no brand
 0x0E   2   0, or 1 on a few ports and airports (187 records on CD-ID 2952, 240 on CD-ID 21594)
 0x10   4   POI_ID     the 0x10 detail record's +0x1C (§8.1.1); read before as a "brand reference"
 0x14   8   0          DB-REL 34 only: the 20-byte form (DB-REL 22) ends at 0x14
```

Checked on every record: the brand matches the `0x10` detail's brand (64,433 / 64,433 on CD-ID
2952, 466,310 / 466,310 on CD-ID 21594), and so does the POI ID. Every block is sorted by
`LOCAL_X` (730 / 730, 1,652 / 1,652).

**Exact local scale = 64:**

```
X_abs = X_min + LOCAL_X * 64
Y_abs = Y_min + LOCAL_Y * 64
```

Verified across 2,395 blocks: for each tile size, `max(LOCAL_X) = (X_max−X_min)/64 − 1`.

| tile side (units) | 98304 | 196608 | 393216 | 786432 | 1572864 | 3145728 |
|---|---|---|---|---|---|---|
| measured `max(LOCAL_X)` | 1535 | 3071 | 6143 | 12287 | 24575 | 49151 |
| expected `side/64 − 1` | 1535 | 3071 | 6143 | 12287 | 24575 | 49151 |

POI resolution: 64 units = 1.15e−5° ≈ **1.2 m**. Name blob (Latin-1, `\0`-terminated)
follows the records: the brands used in the block (`BRAND`), **173 distinct names across the
whole DB**, all chains (banks, fuels, hotels). **2,048,403 POIs** extracted.

**Record size is `T[0x32]`, not a constant.** On CD-ID 2952 (DB-REL 22) the record is
**20 bytes**: the same fields up to `POI_ID`, without the trailing 8 zero bytes of the
28-byte form. Of the five `RECORD_SIZE_TABLE`
candidates for 28 bytes listed in `01-architecture.md` (`0x04`, `0x18`, `0x32`,
`0x43`, `0x4e`), `T[0x32]` is the only one that equals 20 on that disc (28 on
CD-ID 21594, DB-REL 34).

Every `0x06` record points at exactly one POI in a `0x10` block, and its tile
position equals that POI's stored absolute coordinate (§8.1.1) to the unit:

| disc | `0x06` blocks | records | tile position == 0x10 coordinate |
|---|---|---|---|
| CD-ID 2952 (DB-REL 22) | 730 | 64,433 | 64,433 |
| CD-ID 21594 (DB-REL 34) | 1,652 | 466,310 | 466,310 |

The `0x06` blocks are therefore a **spatial index over the `0x10` POI parcels**:
finding the POIs near a position is a bbox lookup plus one read per tile, with no
geometry involved.

A branded POI is stored twice in `0x10`, in a category copy and a brand copy (`01-architecture.md`
§4.4.2). On CD-ID 2952 the `0x06` record points at the brand copy for every branded POI
(11,643 / 11,643) and at the category copy for the rest; on CD-ID 21594 it points at the
category copy for all of them.

On a CNI1 (CD-ID 2952), with every `0x06` block's record count set to 0 (and the cities' POI
roots cut, §4.4.2 of `01-architecture.md`) the unit runs normally but draws no POI icons, and its
POI category menus come up empty. A block rewritten with our own records (sorted by `LOCAL_X`,
brands in its name blob) draws and lists them.

"""
