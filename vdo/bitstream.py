"""
bitstream - class wrapper for bitarray

# from bitarray import bitarray   # https://pypi.org/project/bitarray/
# # https://github.com/ilanschnell/bitarray/blob/master/doc/buffer.rst
# from bitarray.util import ba2int
"""

from __future__ import annotations

from bitarray import bitarray
from bitarray.util import ba2int

from QGIS_VDO.vdo.geotypes import (
    GEO_CATEGORY,
    GEO_SHAPE,
    GEO_LINE,
    VERTEX,
    TSTR,
    # BYTESTRUCT,
)

from QGIS_VDO.vdo.consts import (
    struct_WORD,
    # struct_4BYTES,
    BITS_IN_ASCII,
    BITS_IN_BYTE,
    BITS_IN_WORD,
    BITS_IN_UINT,
    LOOKUP_CHAR_BYTES,
    bits_needed,
)

from QGIS_VDO.vdo.block_base import block_base


BITS_IN_CATEGORY_TYPE = BITS_IN_BYTE - 1   # packed cat type len = 7 bit

OFFSET_PACKED_DATA = 0x34  # ТИПЫ БЛОКОВ archived type_1_vdo_pack
                            # bmw ee bnl:  00 14 15 16 1c 1d 1e # noqa: 00 +sc4-11
                            # в них незапакованы первые 0х34 # noqa: E116

CONST_BA_11 = bitarray([1, 1])
CONST_BA_10 = bitarray([1, 0])
CONST_BA_01 = bitarray([0, 1])
CONST_BA_00 = bitarray([0, 0])


# --------- bitstream - Class wrapper for bitarray

"""
https://github.com/fdemusso/OpenCarin/blob/main/docs/carindb/04-cf1-codec.md

9.11.2 Primitives (offsets in CC-93 pbp)
0x3660  uncompressed_sectors(hdr)   bit 0 of hdr[6] -> hdr[7] otherwise blockid&0xff
0x3698  dispatch: if hdr[6]&1 -> init + switch on BLOCK_TYPE:
        - 0x00:                 branch 0x36b4 -> bsr 0x3ea0 (decode_type00)
        - 0x0E:                 branch 0x36be -> bsr 0x4320 (decode_type0E)
        - 0x14, 0x15, 0x16:     branch 0x36c8 -> bsr 0x46aa
        - others > 0x0E (0x10, 0x12, etc.): branch 0x36d2 -> pass length*2048, bsr 0x6a06
            (memset 0 — buffer zeroed because non-rendered)
        otherwise (CF=0): branch 0x3726 (memcpy raw sectors)
0x4798  init(src)        PTRBITS = bits_needed(usize * SECTOR)   [CC-93: SECTOR=2048]
0x47da  copy_raw(dst,n)  memcpy from raw cursor, cursor += n
0x4800  copy_section(base, entry, recsize, plus1)
0x49a8  bits_init()      base = current cursor, bitpos = 0
0x49bc  getbits(n)       BFEXTU (a0){bitpos:n}  -> MSB-first
0x4a68  bits_needed(n)   bits to represent 0..n-1, 16-bit arithmetic
"""


class bitstream():
    '''
    Распаковщик geo-блоков: @ 070EFB07 0014 01 09 [14:MAP__05k200]
    '''
    # __slots__ = ('vdo', 'is_unpacked', '_head_cached', 'type', 'type_name')
    # __slots__ = ('res', 'buffer', 'head', 'map', 'shift_scale', 'li_cat',
    #  'li_shp', 'li_lin', 'li_vrtx', 'li_poi', 'li_tstr')

    def __init__(self, archived_bock: block_base):
        
        # dbrev
        self.dbrev = archived_bock.dbrev

        # Максимальная длинна указателя в битах (по размеру распакованного блока, если на 1 меньше - word wrap align)
        # self._const_segsize * self.unarc_segcn Максимально возможное значение адреса; 2 -> 0x800*2-1=0xfff
        self.max_bits_in_ptr = bits_needed(archived_bock.head.sizeofblock)    # max possible bits in near offset

        # упакованы НОМЕРА вертексов, а не offs на них
        self.max_bits_in_vrtxnum = len(f"{(archived_bock.li_vrtx.cnt - 1):b}")

        # константы распаковки
        (
            self.max_bits_id_line_if_0,    # noqa id line, сколько бит читать, если флаг показывает отсутствие - 1-32, 0-this
            self.max_bits_id_shape_if_0,   # noqa для id shape (+line?) - сколько бит читать, если флаг показывает отсутствие - 1-32, 0-this
            self.max_bits_in_vertex_delta, # noqa столько бит в дельте XY (8, 9, a)
            unkn_zero
        ) = archived_bock._raw[OFFSET_PACKED_DATA:OFFSET_PACKED_DATA + 4]

        #

        # забираем данные block_basegeo для распаковки
        self.head = archived_bock.head
        self.map = archived_bock.map

        #

        # на сколько сдвинуть единицу координат в карте влево, чтобы получить порядок значений COORD
        self.shift_scale = archived_bock.shift_scale

        # таблица содержания
        self.li_cat = archived_bock.li_cat  # категории
        self.li_shp = archived_bock.li_shp     # полигоны
        self.li_lin = archived_bock.li_lin      # полилинии
        self.li_vrtx = archived_bock.li_vrtx     # x, y точек
        self.li_poi = archived_bock.li_poi          # хз, что это, но это не POI
        self.li_tstr = archived_bock.li_tstr        # наименования на разных языках

        # распаковывать ли lin{5} - характеристика дороги, предположительно макс скорость
        self.flag_unpack_lin5 = False

        self.tail_cutted_after_str = None

        # запакованное тело
        arc = archived_bock._raw[OFFSET_PACKED_DATA + 4:]

        CUT_ZERO_BYTES_CNT = 8
        # с конца убрать нулевые байты, оставив менее 4х
        while arc[-CUT_ZERO_BYTES_CNT:] == b'\x00' * CUT_ZERO_BYTES_CNT:
            arc = arc[:-int(CUT_ZERO_BYTES_CNT / 2)]

        # в буффер - запакованную часть блока, далее self.unpack полностью распакует
        self.buffer = bitarray(buffer=arc, endian='big').copy()    # copy - else read only memory # noqa

        # ----------------------------------------- 070CF805 0014 01 07 [14:MAP__05k200] id_line_if_0 = 0???
        # debug raises - временно для отладки, потом вообще закомментировать эти проверки
        # if self.max_bits_id_line_if_0 not in [0, 5, 0xa, 0xb, 0xc, 0xd, 0xe, 0xf, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15]:
        #     raise ValueError(self.max_bits_id_line_if_0, f"0x{self.max_bits_id_line_if_0:X} .max_bits_id_line_if_0")  # noqa 19/0x13 ?
        # if self.max_bits_in_vertex_delta not in [0, 7, 8, 9, 0x0a, 0xb, 0xc]:
        #     raise ValueError(self.max_bits_in_vertex_delta, f"0x{self.max_bits_in_vertex_delta:X} .max_bits_in_vertex_delta")  # noqa
        #     # bmw 07157901 001E 01 02 [1E:MAP__11k_11] = 0!! bits
        if unkn_zero not in [0]:        # unk_0 = 60 in _0x1d_0x07151504
            raise ValueError(unkn_zero, f"0x{unkn_zero} .unkn_zero")
        pass

        # 0x00, 0x0e и 0x14, 0x15, 0x16, 0x1c, 0x1d, 0x1e упакованы по-разному
        if archived_bock.type in [0x14, 0x15, 0x16, 0x1c, 0x1d, 0x1e]:
            # оставляем незапакованное начало
            self.unpacked = bytearray(archived_bock._raw[:OFFSET_PACKED_DATA])
            self._unpack14()
        else:
            raise TypeError(f"Block type {archived_bock.head.bltype} cant be packed CF=1")

    def decode(self):
        return self.unpacked
    
    def _unpack14(self) -> bytes:      # noqa 'bit_stream.unpack' is too complex (23)Flake8(C901)
        """
        функция, возвращает распакованный _raw
        для блоков типов 14 15 16 1c 1d 1e в архивах CF=1
        """
        # чтобы после распаковки нормально работал блок - добиваем размер нулями 10110001
        self.unpacked += b'\x00' * (self.head.sizeofblock - len(self.unpacked))

        # <<<<<<<<<< 1 GEO_CATEGORY     # S0 (T[0x3b]=4)
        # cat = self.__S0_unpack_categories()
        # h = cat.hex()
        self.__S0_unpack_categories()

        # <<<<<<<<<< 2 GEO_SHAPE    # S1 (T[0x3a]=20)
        # shp = self.__S1_unpack_shapes()
        # h = shp.hex()
        self.__S1_unpack_shapes()

        # <<<<<<<<<< 3 GEO_LINE     # S2 (T[0x3c]=16)
        self.__S2_unpack_lines()

        # <<<<<<<<<< 4 VERTEX, дальше запакованы вертексы, delta-coding
        self.__S3_unpack_vertexes()        # S3

        # <<<<<<<<<< 5 ZERO ENDED STRINGS unpack, but add to self.res only after TSTRrs e4 (T[0x15]=6)
        # floor = sections_end(ctx)
        self.__unpack_text()
        # self.__unpack_all_strings()

        if self.dbrev < 0x14:   # from FW
            return
        
        #  w5 = bytes(ctx.g(8) for _ in range(5))
        # Параметры распаковки from FW
        w5 = self.pop(8 * 5).tobytes()
        print(w5.hex())
        
        # >>>>>>>>>>>>>>>> PASS_20 fill shp and lin values and remove_zeroes
        
        #     _section(ctx, 4, t[T_REC_E4_141516], KIND_E4, PASS_20, st)
        # 4th entry of header (passata DB-REL>=20) item? li_poi?
        self.__KIND_E4_PASS_20_poi(w5)
        
        # fill   ZeroWord align??????
        # _section(ctx, 1, t[T_REC_S1_141516], KIND_S1, PASS_20, st)  #
        self.__fill_shp_PASS_20(w5)
        
        #
        # _section(ctx, 2, t[T_REC_S2_141516], KIND_S2, PASS_20, st)
        self.__fill_lin_PASS_20(w5)

        if self.dbrev < 0x17:                                      # FW +0x4f00
            return
        
        # <<<<<<<<<< TSTRs  - # далее в архиве запакованы собственно TSTR
        # _section(ctx, 5, t[T_REC_E5_141516], KIND_E5, PASS_23, st)
        self.__S5_unpack_tstrs()

        # >>>>>>>>>>>>>>>> PASS_23 fill shp and lin values
        
        # Fill shapes TSTR values
        # _section(ctx, 1, t[T_REC_S1_141516], KIND_S1, PASS_23, st)
        self.__fill_shp_PASS_23()

        # Fill lines - 2 last fields^ p_tstr and (in sc=5) country code
        self.__fill_lin_PASS_23()
        
        # >>>>>>>>>>>>>>>>
        if self.pop(1) == bitarray([1]):
            self.__unpack_text()
        # что? второй вызов? ДА! from FW
        if self.pop(1) == bitarray([1]):
            self.__unpack_text()

        # >>>>>>>>>>>>>>>>
        if self.dbrev > 0x17:        # seen on DB-REL 34; not read by RR 0101 (see _s2_tail)
            self.__S2_tail()

        return

    #

    def __S2_tail(self) -> None:
        """
        
        """
        if not self.li_lin.cnt:
            return
        
        offset = self.li_lin.ptr + 0x0E
        prev = None
        for k in range(self.li_lin.cnt + 1):
            if self.pop(1) == bitarray([1]):
                prev = self._unpack_short(BITS_IN_WORD)
            elif prev is None:
                raise ValueError(f"S2 GEO_LINE record at {offset - 0x0E}: first record inherits +0x0e")
            self.unpacked[offset:offset + 2] = prev
            offset += GEO_LINE.size
            
        return

    def __KIND_E4_PASS_20_poi(self, w5: bytes) -> None:
        """
        wtf? 1to1 from fw
        _section(ctx, 4, t[T_REC_E4_141516], KIND_E4, PASS_20, st)
         4th entry of
        T_REC_E4_141516 = 0x15   sezione 4 (passata DB-REL>=20) item?
        bmw t[0x15] = 6
        # w5'70 d0 40 00 00'
        ...
        def _flag_or(ctx: Cf1Context, width: int) -> int:
            # getbits(1) ? getbits(16) : getbits(width) — used by passes 0x14 (RR +0x46ec, +0x4880)
            return ctx.g(16) if ctx.g(1) else ctx.g(width)
            ...
        elif kind == KIND_E4 and pas == PASS_20:      # +0x4914
            for f in range(3):
                ctx.w(cur + 2 * f, _flag_or(ctx, st.w5[2 + f]))
        """
        if not self.li_poi.cnt:
            return b''

        offset = self.li_poi.ptr
        for _ in range(self.li_poi.cnt):
            # from fw
            for f in range(3):
                if self.pop(1) == bitarray([1]):
                    width = BITS_IN_WORD
                else:
                    width = w5[2 + f]
                self.unpacked[offset + 2 * f:offset + 2 * f + 2] = \
                    self._unpack_short(width)
            offset += 6     # size of 'POI'
        #
        return

    def __fill_shp_PASS_20(self, w5: bytes) -> None:
        """
        ...
        0x10: WORD ZeroWord
        
        _section(ctx, 1, t[T_REC_S1_141516], KIND_S1, PASS_20, st)

                ctx.w(cur + 0x10, ctx.g(pb - 1) << 1)
                _flag_or(ctx, st.w5[0])               # read, not stored
        """
        if not self.li_shp.cnt:
            return
        
        offset = self.li_shp.ptr + 0x10     # ZeroWord align
        for _ in range(self.li_shp.cnt + 1):
            ptr = self._unpack_short(self.max_bits_in_ptr - 1, 1)
            self.unpacked[offset:offset + 2] = ptr
            self._flag_or(w5[0])    # w5[0] read, not stored
            # debug = self._flag_or(w5[0])    # w5[0] read, not stored
            offset += GEO_SHAPE.size
        return

    def __fill_lin_PASS_20(self, w5: bytes) -> None:
        """
        _section(ctx, 2, t[T_REC_S2_141516], KIND_S2, PASS_20, st)
        ...
        elif pas == PASS_20:                      # +0x483c
            ctx.w(cur + 8, ctx.g(pb - 1) << 1)
            ctx.w(cur + 0x0A, _flag_or(ctx, st.w5[1]))
        """
        if not self.li_lin.cnt:
            return

        offset = self.li_lin.ptr + 8        # ptr_linesign
        for _ in range(self.li_lin.cnt + 1):
            self.unpacked[offset:offset + 2] = self._unpack_short(self.max_bits_in_ptr - 1, 1)
            if self.pop(1) == bitarray([1]):
                ptr2poi = self._unpack_short(BITS_IN_WORD)
            else:
                ptr2poi = self._unpack_short(w5[1])
            self.unpacked[offset + 2:offset + 4] = ptr2poi          # ptr2poi
            offset += GEO_LINE.size

        return

    def __fill_shp_PASS_23(self) -> None:
        """
        ...
        0x0c: WORD ptr_to_table_to_strings
        ctx.w(cur + 0x12, ctx.g(pb - 1) << 1)
        """
        if not self.li_shp.cnt:
            return

        offset = self.li_shp.ptr + 0x12
        for _ in range(self.li_shp.cnt + 1):
            self.unpacked[offset:offset + 2] = self._unpack_short(self.max_bits_in_ptr - 1, 1)
            offset += GEO_SHAPE.size
        
        return

    def __fill_lin_PASS_23(self) -> None:
        """
        ...
        12: WORD - PTR ptr2tstr на TSTR на p_str_name, наименование линии (мультиязычность?)
        14: WORD  in sc=5 this country code
        ctx.w(cur + 0x0C, ctx.g(pb - 1) << 1)
        """
        if not self.li_lin.cnt:
            return
        offset = self.li_lin.ptr + 0x0c
        for _ in range(self.li_lin.cnt + 1):
            self.unpacked[offset:offset + 2] = self._unpack_short(self.max_bits_in_ptr - 1, 1)
            offset += GEO_LINE.size
            
        return

    # ------------ ФУНКЦИИ РАСПАКОВКИ СЕКЦИЙ  -----------
    def __S0_unpack_categories(self) -> None:
        """
        S0 (T[0x3b]=4)  +0 u8 category (7 bits), +1 u8 draw flag, +2 u16 S1/S2 offset

        BYTE  en_GEO_CATEGORY                   <--- 7 bits
        BYTE  0poligon_1poliline en_DRAW_TYPE   <--- 1 bit
        WORD  ptr_to_category PTR               <--- max_PTR_bits-1 bits
        """
        if not self.li_cat.cnt:
            return
        result = b''
        # <<<<<<<<<< GEO_CATEGORY
        # Для каждой геокатегории - лишнее, нелогично паковать без категорий
        # +1 - всегда есть завершающий итем, нулевой
        for _ in range(self.li_cat.cnt + 1):      # noqa

            # /0/ en_GEO_CATEGORY
            category_type = self._unpack_byte(BITS_IN_CATEGORY_TYPE)    # 7 bit на

            # /1/ 0poligon_1poliline
            isLine = self._unpack_byte(1)    # 1 бит на полигон0/полилиния1

            # /2/ ptr_to_category
            # left shift 1 - т.к. last = 0 always in this ptr
            # max_bits_in_ptr - 1 максимальное к-во бит для near ссылки на word
            ptr2obj = self._unpack_short(self.max_bits_in_ptr - 1, 1)

            # cat = category_type + isLine + ptr2obj
            # h = cat.hex()  # DEBUG
            
            result += category_type + isLine + ptr2obj

        self.unpacked[self.li_cat.ptr:self.li_cat.ptr + (self.li_cat.cnt + 1) * GEO_CATEGORY.size] = \
            result
        return

    def __S1_unpack_shapes(self) -> None:
        """
        S1 (T[0x3a]=20) +0 name, +2 S3 offset, +4 u32, +8 i32 X, +12 i32 Y,
                +0x10 u16 (always 0 on plain blocks), +0x12 e5 offset

        WORD - ptr2string <--- word, ptr 2 zero-ended string
        WORD   ptr2firstObjVertex  <--- запакованы не offs, а номера вертексов, vertnum,
                    надо расчитывать ptr - offset
        DWORD  id <----- read bit, if 1 - read next32bits is id, if not - so, not
        COORD - qword <--- coord 64bits
        ZeroWord align <--- no in arc
        WORD ptr_to_table_to_strings, unarc by calculate CURR_PTR_PTSTR +4 - next ptstr
        == # в хвостовом vertex = ptrStrTable, последний pstrt = pstrt + 4*pstr.cnt
        """
        if not self.li_shp.cnt:
            return

        # если есть shapes - замкнутые полигоны - распаковываем
        bin_shapes = b''
        for _ in range(self.li_shp.cnt + 1):      # +1 - всегда есть завершающий итем, нулевой
            # <<<<<<<<<< GEO_SHAPE
            # /0/ WORD - ptr2string <--- word, ptr to zero-ended string
            ptr2string = self._unpack_short(self.max_bits_in_ptr)
    
            # /1/ WORD, ptr 2 first vertex (упакованы НОМЕРА vrtx)
            ptr2firstObjVertex = self._unpack_vrtx_ptr()
    
            # /2/  dword, id
            #id - если следующий бит = 1, ЕСТЬ 32бит ID, иначе bits_to_unpack_then_zero
            qty = BITS_IN_UINT if self.pop(1)[0] else self.max_bits_id_shape_if_0
            # int_id = ba2int(self.pop(qty))
            # id = struct_4BYTES.pack(int_id)
            id = self._unpack_uint(qty)
    
            # /3/  dword dword - coord, here '08 c0 00 a0 40 01 8d 00'
            # координаты - они есть, всегда. Просто лежат без упаковки  '0010010001110101000001011000010011100010'
            # lon = self._unpack_uint(BITS_IN_UINT)        # _lon
            # lat = self._unpack_uint(BITS_IN_UINT)        # _lat
            coord = self._unpack_uint(BITS_IN_UINT) + self._unpack_uint(BITS_IN_UINT)
    
            # >>>>>>>>>> - а ВСЁ, более ничего запакованного нет. Поэтому остальное добиваем нулями
            # /4/ WORD ZeroWord align
            # /5/ WORD ptr_to_table_to_strings (указатель на ПЕРВЫЙ TSTR, запаковано в другом месте)
            zeroTail = b'\x00' * 4    # 2 * word bytes -> размер GEO_SHAPE полный
    
            bin_shapes += ptr2string + ptr2firstObjVertex + id + coord + zeroTail

        self.unpacked[self.li_shp.ptr:self.li_shp.ptr + (self.li_shp.cnt + 1) * GEO_SHAPE.size] = \
            bin_shapes
        return
            
    def __S2_unpack_lines(self) -> None:
        """
        S2 (T[0x3c]=16) +0 name, +2 S3 offset, +4 u32, +8 e4 offset, +0x0a u16,
            +0x0c e5 offset, +0x0e u16 (_s2_tail)

        Geo - poligon
        0:  WORD - PTR    p_str_name - ptr на 0-ended str; =max_ptr_bit_len
        2:  WORD - PTR    ptr_vrtx - vrtx num; =max_vrtx_num_bits_len
        4:  DWORD         id; 1 =32; 0 =max_bits_id_line_if_0
        8:  WORD - PTR   ptr_linesign? ptr2первый TSTR? наименование области?
        10: WORD  -  ptr2poi? подозрение, *10=скорость sc=5
        12: WORD - PTR ptr2tstr на TSTR на p_str_name, наименование линии (мультиязычность?)
                (Самый первый - 34B4 из последнего shp
        14: WORD  _s2_lines_tail
        """
        if not self.li_lin.cnt:
            return

        bin_lines = b''
        # для каждой полилинии
        for _ in range(self.li_lin.cnt + 1):      # +1 - всегда есть завершающий итем, нулевой
            # <<<<<<<<<< GEO_LINE
            # /0/ p_str_name
            p_str_name = self._unpack_short(self.max_bits_in_ptr)

            # /1/ WORD, ptr 2 first vertex (упакованы НОМЕРА vrtx)
            ptr2firstObjVertex = self._unpack_vrtx_ptr()

            # /2/ > DWORD id ?? (полный ли DWORD? если нет, то сколько бит грузить?)
            if self.pop(1) == bitarray([1]):
                id = self._unpack_uint(BITS_IN_UINT)
            else:
                id = self._unpack_uint(self.max_bits_id_line_if_0)    # bits_to_unpack_then_zero

            # /3/ WORD CALC  ptr_POI, но если POI нет, то на ptr2first TSTR (CALCULATE == tos.li_tstr.ptr)
            # self.result += struct_WORD.pack(self.parent.li_tstr.ptr)
            # -----> просто нули.
            ptr_linesign = b'\x00' * 2

            # /4/  align? max_speed? 0x0b, 0x0c, 0x00 etc
            ptr2poi = b'\x00' * 2

            # /5/ ptr2table CALC  this_will_increment  CALC если p_str_name ПРЕДЫДУЩЕГО == 0, то НЕ инкрементируется
            ptr2tstr = b'\x00' * 2

            # /6/ CALC 2 байта , в 16, 15 - код страны en_TeleAtlasRegion.
            shrtEnd = b'\x00' * 2

            bin_lines += p_str_name + ptr2firstObjVertex + id + ptr_linesign + ptr2poi + ptr2tstr + shrtEnd
            # len(line) == GEO_LINE.size

        self.unpacked[self.li_lin.ptr:self.li_lin.ptr + (self.li_lin.cnt + 1) * GEO_LINE.size] = \
            bin_lines
        return

    def __S3_unpack_vertexes(self) -> None:
        """
        S3              8 B absolute i32 X, Y, or 4 B u16 local x, y (delta coded)
        Why 4B???? stop. coord vs vertex
        """
        if not self.li_vrtx.cnt:
            return                  # pragma: no cover imposibry

        # первые2 значения - рассматриваем, как xy начальных точек.
        prev_x = ba2int(self.pop(16))
        prev_y = ba2int(self.pop(16))
        # упаковываем to VRTX
        bin_vrtx = struct_WORD.pack(prev_x) + struct_WORD.pack(prev_y)
        # a_hex = bin_vrtx.hex()

        # распаковка дельта-кодированных локальных координат
        for _ in range(self.li_vrtx.cnt - 1):     # minus 1st xy
            prev_x = self._unpack_half(prev_x)      # x
            prev_y = self._unpack_half(prev_y)      # y
            # упаковка в vertex
            bin_vrtx += struct_WORD.pack(prev_x) + struct_WORD.pack(prev_y)
            # a_hex = vrtx.hex()
            # print(vrtx.hex())

        self.unpacked[self.li_vrtx.ptr:self.li_vrtx.ptr + self.li_vrtx.cnt * VERTEX.size] = \
            bin_vrtx
        return

    def _unpack_half(self, prev: int) -> int:
        """
        x и y упакованы дельта-кодированием с префиксным кодом:
        0 - сложить с prev, 10-вычесть из prev, 11 - прочитать и вернуть новое значение
        Args:
           prev: предыдущее значение
        Returns:
           расчитанное значение
        """
        if self.pop(1) == bitarray([0]):       # 0
            val = ba2int(self.pop(self.max_bits_in_vertex_delta))
        elif self.pop(1) == bitarray([0]):           # 10
            val = -ba2int(self.pop(self.max_bits_in_vertex_delta))
        else:                                # 11
            return ba2int(self.pop(BITS_IN_WORD))
        return prev + val

    def __unpack_text(self) -> None:
        """
        FW-like реализация распаковки строк
        """
        CHARMAP = bytes.fromhex(
            "61657374720020646768696c6e6f"
            "e0e1e2e3e4e5e7e8e9eaebecedeeeff1f2f3f4f5f6f8f9fafbfcfdac"
        )
        # ^^^ первыми запакованы 2 ptr - начало и окончание блока строк
        ptr_start = ba2int(self.pop(self.max_bits_in_ptr))
        ptr_end = ba2int(self.pop(self.max_bits_in_ptr))
        if ptr_start == 0 and ptr_end == 0:
            return b''  # а вот так в FW реализовано.
        # strings_length = ptr_end - ptr_start

        words = []
        for _ in range(6):
            n = ba2int(self.pop(5))
            bbb = b''
            for _ in range(n):
                bbb += self._unpack_byte(7)
            words.append(bbb)
        # if floor is None:
        #     floor = _sections_end(ctx)
        ok = ptr_start <= ptr_end   # < strings_length  # and start >= floor
        p = ptr_start
        while p <= ptr_end:      # and p < strings_length:
            code = self.pop(2)
            if code == CONST_BA_00:
                v = CHARMAP[ba2int(self.pop(1))]
            elif code == CONST_BA_01:
                v = CHARMAP[2 + ba2int(self.pop(2))]
            elif code == CONST_BA_10:
                v = CHARMAP[6 + ba2int(self.pop(3))]
            else:
                v = ba2int(self.pop(7))
                if v <= 0x26:
                    if v > 0x1B:
                        w = words[v - 0x21]
                        if ok:
                            self.unpacked[p : p + len(w)] = w
                        p += len(w)
                        continue
                    v = CHARMAP[14 + v]
            if ok:
                self.unpacked[p] = v
            p += 1
        # thats all folks
        return

    def __unpack_all_strings(self) -> None:
        """
        Распаковка текстовых строк. Весьма оригинальная реализация Хаффмана.
        Returns:
            (ptr_beg, ptr_end, bin_text)
            ptr_beg :   int - начальный адрес строк
            ptr_end :   int - - окончание строк, адрес конца всех строк
            bin_text:   bytes бинарное представление строковой части zero-ended строк
        
        :LOOKUP_CHAR_BYTES: Базовая константная таблица соответствия на 14 char,
        :preambula:  - хранит 6 сочетаний
        :ascii: Если символ ни там, ни там - win1250, причем, если ascii до ' ' - то = ascii + 0xe0
        """
       
        # ^^^ первыми запакованы 2 ptr - начало и окончание блока строк
        ptr_start = ba2int(self.pop(self.max_bits_in_ptr))
        ptr_end = ba2int(self.pop(self.max_bits_in_ptr))
        if ptr_start == 0 and ptr_end == 0:
            return b''  # а вот так в FW реализовано.
        strings_length = ptr_end - ptr_start

        #  ^^^  далее - подготовка преамбулы для хаффмановского декодирования
        # преамбула - словарь из 6 элементов с ключами от 110100001 до 110100110.
        # адаптивная по блокам таблица часто встречающихся до 3-х char
        # Причём "пустые" элементы = b'A'

        # но 11 это преамбула, поэтому от 0100001 до 0100110
        preambula = {}
        for k in range(0b0100001, 0b0100111):
            # первые 3 бита = 000
            if beg_marker := ba2int(self.pop(3)):             # val.to01() != '000':
                raise ValueError(f"WTF? В начале строк преамбулы ожидалось 000, а не '{beg_marker:3b}'")    # noqa

            # затем 2 бита - количество ascii chars для чтения
            if not (n := ba2int(self.pop(2))):         #  11 и 01 точно да, а остальные варианты - хз.  # noqa
                # Вроде 00 не может быть - иначе зачем 6 шт где не кодируется ничего?
                raise ValueError(f"WTF? В количестве ch преамбулы не ожидалось 00, а тут '{n:2b}'")    # noqa
            #теперь загрузить n chars
            val = b''
            for _ in range(n):
                # и грузятся ascii коды по 7 бит
                iso_ch = ba2int(self.pop(BITS_IN_ASCII))
                val += bytes((iso_ch,))          # короче и быстрее
            preambula[f"{k:07b}"] = val

        #   ^^^  и вот только теперь пошли буквы, закодированные ....эммм.
        # .. как бы хафманом, но с нюансами
        bin_str = b''
        # for _ in range(strings_length):  b'rolvs\xf5!stjern\xf5!$l\xf5!mager\xf5!seiland\x00s\xf5r\xf5'
        while len(bin_str) < strings_length:
            prefix = self.pop(2)
            if prefix == CONST_BA_11:           # prefix.to01() == '11':
                ba = self.pop(BITS_IN_ASCII)
                if ba.to01() in preambula:
                    # о, сокращённенькое из преамбулы
                    pre_chars = preambula[ba.to01()]
                    # но если из преамбулы возвращается А
                    if pre_chars == b'A':
                        bin_str += bytes((ba2int(ba),))    # просто добавить байт
                    else:
                        bin_str += pre_chars
                elif ba2int(ba) < 32:       # похоже загрузить ascii до ' '
                    """
                    ISO 8859-2 xor win1250?
                    ISO-8859-1 / Latin-1
                    """
                    # а это 1250
                    ascii = 0xe0 + ba2int(ba)  # угу, эмпирическое волшебное число 0xE0
                    # ascii = ascii.to_bytes(1, byteorder='big')
                    bin_str += bytes((ascii,))   # w1250 0xF5 символ ő 
                else:
                    # или ascii код буквы
                    # ascii = ba2int(ba)
                    bin_str += bytes((ba2int(ba),))   # bin_str += ba2int(ba).to_bytes(1, byteorder='big')
                continue        # всё, данные итерации загружены
            elif prefix == CONST_BA_00:         # prefix.to01() == '00':
                prefix += self.pop(1)
            elif prefix == CONST_BA_01:         # prefix.to01() == '01':
                prefix += self.pop(2)
            else:                               # elif prefix.to01() == '10':
                prefix += self.pop(3)
            # вытаскиваем, что получилось, из дерева и добавляем к результату
            bin_str += LOOKUP_CHAR_BYTES[prefix.to01()]

        # всё, упакованные буквы окончились
        self.unpacked[ptr_start:ptr_end] = bin_str

        # debug
        unic = bin_str.replace(b"\x00", b".")
        unic = unic.decode('cp1250')
        # print(unic)
        return

    def __S5_unpack_tstrs(self) -> bytes:
        """
        Каждый запакованный TSTR:
        1 - флаг загружать, или 0 использовать прошлые  <- 1 bit
        ptr =   <- max_ptr_bits
        lang =   <-8 bit
        last_byte =   <- 5 bit -    __shape =   0,
                                    __alias =   2,
                                    __street =  8,
                                    __poliline =0x10

        # noqa
        071515 04  BlockType.MAP__10k400: 0x1d
        Max PTR bits: 12
                        самый хвост :
        0000000000000000000000000000000000000000001100011000000100010101100000110001101001100110001110010100110001111011000100010110001000101101010001011100100010111101000110000000000000000000000000000000000000000000000000000000
        но всё до ...0001 - незначимо
        8c0 15 00   delta 13/19
        1 100011000000 1 00010101 1 00000     1100011000000100010101100000
        1 100011010011 00   8D3  delta 12/18 
        1 100011100101 00   8E5  delta 11/17
        1 100011110110 00   8F6  delta e/14     'more laptevykh' ? 'tauyskaya guba' 'okhotskoe more'
        8B0 <<1        8B4<<1        8B8<<1    8BC<<1      8c0
        10001011000 10001011010 10001011100 10001011110 100011000000
        12-1 len(align word), 4 stucks
        """
        if not self.li_tstr.cnt:
            return
            
        all_tstrs = b''
        short_ptr = b'\x00\x00'
        byte_lang = b'\x00'
        byte_type = b'\x00'
        
        for _ in range(self.li_tstr.cnt):
            # for func, width, size in ((self._unpack_short, pb, 2),
            #                           (2, 8, 1),
            #                           (3, 5, 1)):
            #     b_val = b''
            #     if self.pop(1) == bytearray(1):

            # load or reuse ptr
            if ba2int(self.pop(1)):
                # read ptr
                short_ptr = self._unpack_short(self.max_bits_in_ptr)
            # else:       # use prev value tstr_ptr
            # language
            if ba2int(self.pop(1)):
                # read lang
                byte_lang = self._unpack_byte(8)
            # else:   # use prev language
            # type
            if ba2int(self.pop(1)):         # 07155F03 001E 01 04 [1E:MAP__11k_11] non-empty bitarray expected
                # read type
                byte_type = self._unpack_byte(5)
            # else:   # use prev type
                
            # "собираем" word + byte + byte: ptr + lang + type
            tstr = short_ptr + byte_lang + byte_type
            # a_hex = tstr.hex()
            all_tstrs += tstr

        self.unpacked[self.li_tstr.ptr:self.li_tstr.ptr + self.li_tstr.cnt * TSTR.size] = \
            all_tstrs
        return
    
    # ----------------------------
    # ------------ ФУНКЦИИ РАСПАКОВКИ ПРИМИТИВОВ - byte, short, uint, vrtx_nums -----------

    def pop(self, qty_bits: int) -> bitarray:
        '''POP qty_bits from begin (left) buffer qty bites'''
        if qty_bits == 0:
            return bitarray(0)
        val = self.buffer[:qty_bits]   # взять первые qty_bits бит
        self.buffer = self.buffer[qty_bits:]      # удалить qty_bits из начала
        return val

    def _flag_or(self, width: int) -> int:
        """
        from FW
        getbits(1) ? getbits(16) : getbits(width) — used by passes 0x14
        return ctx.g(16) if ctx.g(1) else ctx.g(width)
        """
        if self.pop(1) == bitarray([1]):
            width = 16

        width = min(width, len(self.buffer))
        return ba2int(self.pop(width))

    def touch(self, qty_bits: int, start: int = 0) -> bitarray:
        '''Return qty bits from start W/o(!) deleting'''
        val = self.buffer[start:start + qty_bits].copy()
        return val
  
    def _unpack_byte(self, bit_compressed: int, left_shift: int = 0) -> bytes:
        """
        Unpack one byte from bit_compressed to byte

        Args:
            bit_compressed:  Количество бит для интерпретации, как байт
            left_shift:      сдвиг влево после распаковки
        Returns:
            bytes
        Raises:
            Value Error При bit_compressed более чем 8 бита
        """
        if bit_compressed > BITS_IN_BYTE:
            raise NotImplementedError(bit_compressed, f"Значение больше {BITS_IN_BYTE}, _unpack_byte")
        
        res: bitarray = self.pop(bit_compressed)
        # добавить справа нолей на к-во сдвига
        res.extend(bitarray([0]) * left_shift)  # самый быстрый путь добавить справа
        # оставить только 8 правых бит
        res = res[-BITS_IN_BYTE:]
        # выровнять до word
        from_left = BITS_IN_BYTE - len(res)
        res = (bitarray([0]) * from_left) + res    # выровнять до word
        # br = res.tobytes()
        return res.tobytes()

    def _unpack_short(self, bit_compressed: int, left_shift: int = 0) -> bytes:
        """
        Unpack two bytes from bit_compressed bits
        
        Args:
            bit_compressed:  Количество бит для интерпретации, как word
            left_shift:      сдвиг влево после распаковки
        Returns:
            bytes
        Raises:
            Value Error При bit_compressed более чем 16 бита
        """
        if not bit_compressed:
            return b'\x00\x00'
        
        if bit_compressed > BITS_IN_WORD:
            raise ValueError(bit_compressed, f"Значение bit больше {BITS_IN_WORD}, _unpack_short")
        
        res: bitarray = self.pop(bit_compressed)
        # добавить справа нолей на к-во сдвига
        res.extend(bitarray([0]) * left_shift)  # самый быстрый путь добавить справа
        # оставить только 16 правых бит
        res = res[-BITS_IN_WORD:]
        # выровнять до word
        from_left = BITS_IN_WORD - len(res)
        res = (bitarray([0]) * from_left) + res
        # br = res.tobytes()
        return res.tobytes()
    
    def _unpack_uint(self, bit_compressed: int, left_shift: int = 0) -> bytes:
        """
        Unpack four bytes from bit_compressed bits

        Args:
            bit_compressed:  Количество бит для интерпретации, как word
            left_shift:      сдвиг влево после распаковки
        Returns:
            bytes
        Raises:
        Value Error При bit_compressed более чем 32 бита
        """
        if bit_compressed > BITS_IN_UINT:
            raise ValueError(bit_compressed, f"Значение больше {BITS_IN_UINT}, _unpack_uint")
        
        res: bitarray = self.pop(bit_compressed)
        # добавить справа нолей на к-во сдвига
        res.extend(bitarray([0]) * left_shift)  # самый быстрый путь добавить справа
        # оставить только 32 правых бит
        res = res[-BITS_IN_UINT:]
        # выровнять до word
        from_left = BITS_IN_UINT - len(res)
        res = (bitarray([0]) * from_left) + res
        # br = res.tobytes()
        return res.tobytes()

    def _unpack_vrtx_ptr(self) -> bytes:
        """
        Запакованы не offs, а номера вертексов, num_vrtx,
        бонус - надо в 4 раза меньше бит, чтобы сохранить
        ptr vrtx - выравнивается по WORD, кратен 4 -> self.max_PTR_bits - 2 (по факту нет, но порядок да)
        """
        num_vrtx = ba2int(self.pop(self.max_bits_in_vrtxnum))   # номер 0-го vrtx для распаковываемого объекта
        # offset = от первого li_vrtx.ptr + num_vrtx * size вертекса
        vrtx_offset = self.li_vrtx.ptr + VERTEX.size * num_vrtx
        # однако надо 2 bytes, а не int
        ptr2firstObjVertex = struct_WORD.pack(vrtx_offset)
        return ptr2firstObjVertex
