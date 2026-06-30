"""
# noqa
утилита для полного прохода по файлу для поиска блоков 
"""

# import os
# import struct

from vdo.test_vdo import vdobmv as vdo
# from vdo.test_vdo import vdo30 as vdo

from vdo.consts import (struct_4BYTES,
                        struct_WORD
                        )
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
        
        #
        self.data: BYTESTRUCT
        self.curr_offset = 0
        self.data = BYTESTRUCT(self._block_info(self.curr_offset))
        #
        unkn_dword_bytes = self.data._raw[OFFSET_PACKED_DATA:OFFSET_PACKED_DATA + 4]
        (self.word_a, self.word_b, self.word_c, self.word_d) = struct_4BYTES.unpack(unkn_dword_bytes)  # noqa
        pass
        #

    @property
    def cnt_shp(self):
        offset_cnt = OFFSET_LI_GEOSHAPE + 2
        res = struct_WORD.unpack(v_search.data._raw[offset_cnt:offset_cnt + 2])[0]
        return res

    @property
    def cnt_lin(self):
        offset_cnt = OFFSET_LI_GEOLINE + 2
        res = struct_WORD.unpack(v_search.data._raw[offset_cnt:offset_cnt + 2])[0]
        return res

    @property
    def cnt_poi(self):
        offset_cnt = OFFSET_LI_POI + 2
        res = struct_WORD.unpack(v_search.data._raw[offset_cnt:offset_cnt + 2])[0]
        return res

    @property
    def delta_offset_to_next_block(self):
        if self.data.uchar(5) == 0x12:
            res = self.data.ushort(0x15) * self.vdo.segsize       # next0x13
            return res
        res = self.vdo.segsize * self.data.uchar(3)
        return res

    @property
    def is_unpacked(self):
        val = self.data.uchar(6) == 0  # only line packing
        return val

    @property
    def is_packed_1(self):
        val = self.data.uchar(6) == 1  # only line packing
        return val

    @property
    def is_empty_shapes(self):
        # val = self.data.ushort(OFFSET_LI_GEOSHAPE + 2) == 0
        val = self.cnt_shp == 0
        return val

    @property
    def is_empty_lines(self):
        # val = self.data.ushort(OFFSET_LI_GEOLINE + 2) == 0
        val = self.cnt_lin == 0
        return val

    @property
    def is_empty_pois(self):
        # val = self.data.ushort(OFFSET_LI_POI + 2) == 0
        val = self.cnt_poi == 0
        return val

    @property
    def is_valid_type(self):
        res = True
        if self.data.uchar(5) not in self.types4find:
            # не тот тип блока
            return False
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


# ===================================================================
if __name__ == "__main__":
    #

    v_search = searcher(vdo)

    i = 0
    for head in v_search.next_block():
        
        if not v_search.is_valid_type:  # поиск в 6-ти типах - картах
            continue

        if not v_search.is_packed_1:  # не запакованные "1" - не надо
            continue

        # if not v_search.is_unpacked:  # распакованные - не надо
        #     continue

        # if v_search.is_empty_lines:  # тут отбраковывались с линиями
        #     continue

        if v_search.is_empty_pois:
            continue

        hex_list = [f"{c:02X}" for c in v_search.data._raw[:OFFSET_PACKED_DATA]]
        str_bla = "".join(hex_list[0 : 4])
        str_bla_t = f"0x{str_bla}  # {hex_list[5]}"

        cnt_shp = v_search.cnt_shp
        cnt_lin = v_search.cnt_lin
        cnt_poi = v_search.cnt_poi

        if cnt_poi > 50 and False:
            continue

        hex_list = [f"{c:02X}" for c in v_search.data._raw[OFFSET_PACKED_DATA:OFFSET_PACKED_DATA + 4]]  # noqa
        unk_bytes = " ".join(hex_list)

        print(f"{str_bla_t}:  {unk_bytes}\t shp: {cnt_shp}\tlin: {cnt_lin}\tpoi: {cnt_poi}\t")  # noqa
        i += 1

        if i > 50:
            pass

        print(f"finded is_valid_type {i}")

    print("ok")
    pass

# bmw
# 0x06F55E02  # 1C:  01 00 00 48   shp: 1 lin: 10 poi: 7
# 0x06F8B703  # 1C:  05 00 00 44   shp: 12        lin: 7  poi: 10
