"""
# noqa
утилита для полного прохода по файлу для поиска блоков 
"""

# import os
# import struct

from vdo.test_vdo import vdobmv as vdo

# from vdo.consts import struct_UINT, struct_WORD
from vdo.datatypes import VDO_FILE, BYTESTRUCT

from vdo.block_basegeo import (OFFSET_LI_GEOSHAPE,
                               OFFSET_LI_GEOLINE,
                               OFFSET_LI_POI,
                               OFFSET_PACKED_DATA)

# FLAG_LZW_PACKED
# OFFSET_LZW_PACKED


class searcher():

    def __init__(self, vdo_file: VDO_FILE):
        # check existing filepath

        # init
        self.vdo = vdo_file
        self.types4find = [0x14, 0x15, 0x16, 0x1c, 0x1d, 0x1e]
        #
        find_mask = {}
        find_mask['type'] = 0
        find_mask['packed'] = 0
        # not 0 li cnt
        find_mask['cat'] = 1
        find_mask['shp'] = 1
        find_mask['lin'] = 0
        find_mask['vrtx'] = 1
        find_mask['poi'] = 0
        find_mask['tstr'] = 1

        find_mask['beg_pckd'] = 1
        self.mask = find_mask
        #
        self.data: BYTESTRUCT
        self.curr_offset = 0
        self.data = BYTESTRUCT(self._block_info(self.curr_offset))
        pass
        #

    @property
    def delta_offset_to_next_block(self):
        if self.data.uchar(5) == 0x12:
            res = self.data.ushort(0x15) * self.vdo.segsize       # next0x13
            return res
        res = self.vdo.segsize * self.data.uchar(3)
        return res

    @property
    def is_packed(self):
        val = self.data.uchar(6) == 1  # only line packing
        return val

    @property
    def is_empty_shapes(self):
        val = self.data.ushort(OFFSET_LI_GEOSHAPE + 2) == 0
        return val

    @property
    def is_empty_lines(self):
        val = self.data.ushort(OFFSET_LI_GEOLINE + 2) == 0
        return val

    @property
    def is_empty_pois(self):
        val = self.data.ushort(OFFSET_LI_POI + 2) == 0
        return val

    @property
    def is_valid_type(self):
        res = True
        if self.data.uchar(5) not in self.types4find:
            # не тот тип блока
            return False
        return res

    @property
    def signA(self):
        res = self.data.ushort(OFFSET_PACKED_DATA)
        return res

    @property
    def signB(self):
        res = self.data.ushort(OFFSET_PACKED_DATA + 2)
        return res

    def _block_info(self, offset):
        raw = self.vdo.read(offset, OFFSET_PACKED_DATA + 4)
        # data = BYTESTRUCT()
        return raw

    def next_block(self):
        offset = self.curr_offset
        while True:
            offset += self.delta_offset_to_next_block
            # self.curr_offset = offset
            data = self._block_info(offset)
            if not data:
                break       # EOF ?
            self.data = BYTESTRUCT(data)
            
            yield data

    # with open(file_path, 'r', encoding='utf-8') as file:
    #     while True:
    #         chunk = file.read(chunk_size)
    #         if not chunk:
    #             break  # End of file reached
    #         yield chunk


# ===================================================================
if __name__ == "__main__":
    #

    v_search = searcher(vdo)

    i = 0
    for head in v_search.next_block():
        i += 1
        if not v_search.is_valid_type:
            continue
        if not v_search.is_packed:
            continue

        if not v_search.is_empty_lines:
            continue

        print(f"{v_search.data.hex[:20]}: {v_search.signA:x} {v_search.signB:x}")

        if v_search.is_empty_pois:
            continue

        print(f"finded is_valid_type {i}")

    print("ok")
    pass
