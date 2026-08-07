"""
block_basegeo - Базовый тип для - карт   00 16 15 1c 14 1d 1e # noqa: E116
"""
from __future__ import annotations

from typing import Iterator


# from bitarray import bitarray   # https://pypi.org/project/bitarray/
# # https://github.com/ilanschnell/bitarray/blob/master/doc/buffer.rst
# from bitarray.util import ba2int

from QGIS_VDO import bitarray, ba2int

from QGIS_VDO.vdo.block_base import block_base
from QGIS_VDO.vdo.datatypes import BLADDR, LIST, BYTESTRUCT
from QGIS_VDO.vdo.enums import en_GEO_CATEGORY, en_DRAW_TYPE
from QGIS_VDO.vdo.geotypes import (MAP_AREA,
                                   GEO_CATEGORY,
                                   GEO_SHAPE,
                                   GEO_LINE,
                                   VERTEX,
                                   TSTR)
from QGIS_VDO.vdo.consts import (struct_UINT,
                                 struct_WORD)

from .bitstream import bitstream


OFFSET_LI_GEOCATEGORY = 0x08    # geodata types (categories)
OFFSET_LI_GEOSHAPE = 0x0c       # гео SHAPES - замкнутые полигоны
OFFSET_LI_GEOLINE = 0x10        # линии
OFFSET_LI_VERTEX = 0x14         # точки word, word
OFFSET_LI_POI = 0x18            # poi`s`
OFFSET_LI_TSTR = 0x1c           # ptrs read_tstr - индексы строк en_GEO_OBJ

OFFSET_PACKED_DATA = 0x34  # ТИПЫ БЛОКОВ archived type_1_vdo_pack
                            # bmw ee bnl:  00 16 15 1c 14 1d 1e # noqa: E116
                            # в них незапакованы первые 0х34 # noqa: E116


TSTR_ITEM_SIZE = 4


class block_basegeo(block_base):
    """
        BL_HEADER   block;          // block.data - list of geo_types
    struct{
        toc:
            PTR_CNT     p_all_shapes <bgcolor=cLtYellow>;
            PTR_CNT     p_all_lines  <bgcolor=cLtYellow>;
            PTR_CNT     p_all_vertexes <bgcolor=cLtYellow>;
            PTR_CNT     p_all_pois;
            PTR_CNT     p_all_pgeo_str <bgcolor=cLtYellow>;
        geo_area    map_area;
        CONST_WORD       unkn_eq_1(0x1) <hidden=true>;  
        en_SCALES   en_scale <hidden=false>;  // VertexXY left shift value for coordinate value equal # noqa E501
            local WORD vrtx_max_x, vrtx_max_y;
        vrtx_max_x =  map_area.h_size  >> en_scale;
        vrtx_max_y =  map_area.v_size >> en_scale;
    }head;
    """

    # shapes = []
    # lines = []
    # cats = []
    categ = {}
        
    def __init__(self, addr: BLADDR) -> None:   # noqa
        class toc:
            li_cat: LIST
            li_shp: LIST
            li_lin: LIST
            li_vrtx: LIST
            li_poi: LIST
            li_tstr: LIST
        super().__init__(addr)
        OFFSET_MAP_AREA = 0x20  # прямоугольник карты COORD * 2 = bott left, top right
        OFFSET_SCALE = 0x32   # значение левого битового сдвига коорд вертексов - чтобы получились координаты # noqa:
        self.map = MAP_AREA(self.read(OFFSET_MAP_AREA, MAP_AREA.size))
        self.shift_scale = self.ushort(OFFSET_SCALE)
        self.toc = toc()        # new TOC
        self.setup_toc()        # toc - table of contents
        # а вот дальше - распаковка, если необходимо
        if not self.is_unpacked:
            # нет, запаковано...
            CUT_ZERO_BYTES_CNT = 8
            barray = self._raw
            # с конца убрать нулевые байты, оставив менее 4х
            while barray[-CUT_ZERO_BYTES_CNT:] == b'\x00' * CUT_ZERO_BYTES_CNT:
                barray = barray[:-int(CUT_ZERO_BYTES_CNT / 2)]
            del self._raw       # в _raw - будут именно распакованные данные
            del CUT_ZERO_BYTES_CNT
            self._raw = barray[:OFFSET_PACKED_DATA]    # до 0x34 - не запакованы, потом идёт непонятный ?? DWORD # noqa
            # остальное в buffer - поток битов, которые будем распаковывать
            buffer = bitstream(barray[OFFSET_PACKED_DATA:],  # + unk_beg_arch_dword # noqa
                               OFFSET_PACKED_DATA,      # вот с этого офсета будем заполнять
                               self)                    # себя - в качестве родителя
            #    self.max_PTR_bits(),
            #    self.toc.li_vrtx,    # не ошибка, нужен offset read_vrtx
            #    self.toc.li_tstr        # и list read_tstr тоже надо
            #    )

            # суммарная уже известная на данный момент информация
            self.show_main_info()
            print(f"\tMax VERTEX bites: {buffer.max_bits_num_vrtx}")
            begin_word = f"{buffer.max_bits_id_line_if_0:02X} {buffer.max_bits_id_shape_if_0:02X}"
            begin_word += f" {buffer.max_bits_in_vertex_delta:02X} {buffer.word_d:02X}"
            print(f" begin word :: {begin_word}")
            del begin_word

            # <<<<<<<<<< GEO_CATEGORY
            '''
            BYTE  en_GEO_CATEGORY <--- 7 bits
            BYTE 0poligon_1poliline en_DRAW_TYPE <--- 1 bit
            WORD ptr_to_category PTR <--- max_PTR_bits-1 bits
            '''
            if self.toc.li_cat.cnt:
                # Для каждой геокатегории
                for _ in range(self.toc.li_cat.cnt + 1):     # +1 - всегда есть завершающий итем, нулевой # noqa
                    buffer.unpack_category()
                    print(BYTESTRUCT(buffer.result))
                    self._raw += buffer.result
                    buffer.clear_result()

            # <<<<<<<<<< GEO_SHAPE
            # '01 00 00 44 65 01 00 6c 67 01 00 7c 00 00 00 8c'
            '''
            # noqa
            WORD - ptr2string <--- word, ptr 2 zero-ended string
            WORD ptr2firstVertex  <--- запакованы не offs, а номера вертексов, vertnum, надо расчитывать ptr - offset
            DWORD id <----- read bit, if 1 - read next32bits as id, if not - so, not
            COORD - qword <--- coord 64bits
            ZeroWord align <--- no in arc
            WORD ptr_to_table_to_strings, unarc by calculate CURR_PTR_PTSTR +4 - next ptstr
            == # в хвостовом vertex = ptrStrTable, последний pstrt = pstrt + 4*pstr.cnt
            '''
            # если есть shapes - замкнутые полигоны - распаковываем
            if self.toc.li_shp.cnt:
                # raise ValueError("toc.li_shp: ", self.toc.li_shp, " но GEO_SHAPE еще не реализован")
                # ------------------------------ <debug
                print("\n p_str  p_vrtx  id  coord_lon  cood_lat  align  p_tstr")
                # ------------------------------ debug>
                # Для каждого шейпа (полигона) из toc.list_shape:
                next_will_increment = False     # - самый первый не инкрементировать для распаковки
                for _ in range(self.toc.li_shp.cnt + 1):     # +1 - всегда есть завершающий итем, нулевой # noqa
                    next_will_increment = buffer.unpack_shape(next_will_increment)
                    #однако для самого последнего шейпа - следующего нет
                    if _ == self.toc.li_shp.cnt:
                        next_will_increment = False
                    #----------------
                    bs = buffer.result     # _for_print
                    pp = f"{struct_WORD.unpack(bs[0:2])[0]:04X} {struct_WORD.unpack(bs[2:4])[0]:04X}"
                    pp += f" {struct_UINT.unpack(bs[4:8])[0]:08x}"
                    pp += f"  {struct_UINT.unpack(bs[8:12])[0]:08X} {struct_UINT.unpack(bs[12:16])[0]:08X}"
                    pp += f"  {struct_WORD.unpack(bs[16:18])[0]:04X} {struct_WORD.unpack(bs[18:20])[0]:04X}"
                    print(pp)
                    #---------------
                    self._raw += buffer.result
                    buffer.clear_result()

            # <<<<<<<<<< GEO_LINE
            if self.toc.li_lin.cnt:
                # для каждой полилинии
                """
                Geo segment of line - poligon
                0:  2h - PTR         p_str_name - ptr на 0-ended str; =max_ptr_bit_len
                2:  2h - PTR         ptr_vrtx - vrtx num; =max_vrtx_num_bits_len
                4:  4h - DWORD       id; 1 =32; 0 =max_bits_id_line_if_0 (word_a)
                8:  2h - PTR   ptr_linesign? ptr2firstPOI
                10: 2h - (CALCULATE == \x00 ?(if not POI) )
                12: 2h - PTR ptr2StrTable (CALCULATE == если p_str_name ПРЕДЫДУЩЕГО == 0, то НЕ инкрементируется.
                        (Самый первый - 34B4 из последнего shp
                14: 2h -# (CALCULATE == 2 байта страны ,
                    при распаковке - константу, пусть FFFF
                """
                # а пока что не реализовано
                #raise ValueError("toc.li_lin: ", self.toc.li_lin, " но GEO_LINE еще не реализован")
                # ------------------------------ <debug
                print("\n p_str  p_vrtx  id  p_beg_tstr  align  p_tstr  unkn")
                # ------------------------------ debug>
                next_will_increment = False  # last shp ptstr =0, so, not uncrement first line
                for _ in range(self.toc.li_lin.cnt + 1):     # +1 - всегда есть завершающий итем, нулевой # noqa
                    next_will_increment = buffer.unpack_line(next_will_increment)
                    # ------------------------------ <debug
                    bs = buffer.result     # _for_print
                    pp = f"{struct_WORD.unpack(bs[0:2])[0]:04X} {struct_WORD.unpack(bs[2:4])[0]:04X}"
                    pp += f" {struct_UINT.unpack(bs[4:8])[0]:08x}"
                    pp += f" {struct_WORD.unpack(bs[8:10])[0]:04X} {struct_WORD.unpack(bs[10:12])[0]:04X}"
                    pp += f" {struct_WORD.unpack(bs[12:14])[0]:04X} {struct_WORD.unpack(bs[14:16])[0]:04X}"
                    print(pp)
                    # ------------------------------ debug>
                    self._raw += buffer.result
                    buffer.clear_result()

            # <<<<<<<<<< VERTEX
            # а вот дальше запакованы вертексы, и, вероятно, delta-coding
            if self.toc.li_vrtx.cnt:
                # первые2 значения - рассматриваем, как xy начальных точек.
                prev_x = int(buffer._unpack_word(), 16)                       # x
                prev_y = int(buffer._unpack_word(), 16)       # y
                self._raw += buffer.result
                buffer.clear_result()
                # ==================== debug print last 10h values
                # self.print_last8word()
                # ==================== debug print last 10h values
                # распаковка дельта-кодированных локальных координат
                for num in range(self.toc.li_vrtx.cnt - 1):     # minus 1st xy
                    # x
                    prev_x = int(buffer._unpack_half_vertex(prev_x), 16)
                    # y
                    prev_y = int(buffer._unpack_half_vertex(prev_y), 16)
                    self._raw += buffer.result
                    buffer.clear_result()

                    # ==================== debug print last 10h values
                    if not self.data_size & 0b1111:      # последние 4 bit == 0, т.е 0x10, 0x20 etc
                        head_offs = self.data_size - 0x10
                        last_vals = self._raw[head_offs:]
                        hex_val = ''
                        for i in range(0, 0x10, 2):
                            hex_val += f"{struct_WORD.unpack(last_vals[i:i + 2])[0]:04x} "
                        # print(f"{head_offs:04x}: {hex_val}")
                    # ==================== debug print last 10h values

                # ==================== debug print last 10h values
                las_vrtxes = self.data_size - head_offs - 0x10
                head_offs = head_offs + 0x10
                last_vals = self._raw[head_offs:]
                hex_val = ''
                for i in range(0, las_vrtxes, 2):
                    hex_val += f"{struct_WORD.unpack(last_vals[i:i + 2])[0]:04x} "
                # debug
                # print(f"{head_offs:04x}: {hex_val}")
                # ==================== debug print last 10h values
                pass

            # TODO: в raw после vrtx идут poi (if exists)
              
            # <<<<<<<<<< zero ended strings unpack, but write only after TSTRrs
            """
                В запакованном блоке сначала идут строки. И только потом - запакованые tstr.
                .
                Max_PTR_bits - начальный адрес строк
                Max_PTR_bits - окончание строк, адрес конца всех строк
                6 сокращений - преамбула.
                собственно запакованный текст
                заканчивается множественными 0-ми
                подробно - см. bitstream.unpack_str
            """
            if self.toc.li_tstr.cnt:
                # нет tstr - нет и строк для распаковки
                unpacked_bin_strings = buffer.unpack_str()
                unic = unpacked_bin_strings.replace(b"\x00", b".")
                unic = unic.decode('cp1250')
                print(f"\n{unpacked_bin_strings}\n\n{unic}\n")
                del unic

            # <<<<<<<<<< POI после вертексов в raw, НО в запакованном виде -
            if self.toc.li_poi.cnt:
                # а пока что не реализовано
                # raise ValueError("toc.li_poi: ", self.toc.li_poi, " но POI еще не реализован")
                """
                WORD like   0006 or 0007 or 0008
                WORD like 0A1E 0A1D   10D2   13EC   1673
                WORD like 0E1C 0A1C   0D77   0FB2   1FB2
                    первые 4 бита - 1 или 0?
                Сначала переменной длинны заголовок
                Потом переменной длинны сами poi (это НЕ poi, но пока не понятно, что это - пусть так)
                распаковать я не могу.
                НО после запакованных poi идёт 41(?)*'0', поэтому можно вычистить, и raw
                заполнить '00 07 01 02 03 04'

                """
                # поиск окончания запакованных poi
                # первый - tos.li_poi.ptr в количестве max ptr bites
                marker_POI = f"{self.toc.li_poi.ptr:0{buffer.max_PTR_bits}b}"
                empty_zero = buffer.buffer.find(bitarray(marker_POI))  # + len(marker_TSTR)
                buffer._pop(empty_zero)   # выкинуть всё
                del empty_zero, marker_POI
                # заmockать '00 07 01 02 03 04'
                for mock in range(self.toc.li_poi.cnt):
                    a = struct_WORD.pack(7)
                    b = struct_UINT.pack(mock)
                    self._raw += a
                    self._raw += b
                del mock, a, b
                """
                - bmw  bl_addr = 0x05412901
                - poi 01F4:0010 cnt:16    next ptr: 02C0
                - strs from 0268
                - Max PTR bites: 10
                - начальный адрес строк 0268 001001101000



                """

            # если нет POI, то сейчас в буфере лидирующие нули
            if not self.toc.li_poi.cnt:
                # <<<<<<<<< Убрать незначащие нули, необходимые для обеспечения
                #  пространства использования преамбульных сокращений, а потом будет ptr на вертексы?
                zero = buffer._touch(1)
                Z = bitarray('0')
                while zero == Z:
                    buffer._pop(1)
                    zero = buffer._touch(1)
                del Z, zero
            
            # <<<<<<<<<< запакованные ссылки ptr на POI для lin (?)
            # если есть линии - то дальше их количество +1 значения
            #  8:  2h - PTR   ptr_linesign? ptr2first TSTR (CALCULATE == tos.li_tstr.ptr) # noqa
            """
bitarray('
01111100110100 0000
011111001101000000
011111001101000000
011111001101000000
011111001101000000
0111110011010000000111110011010000000111110011010000000111110011010000000111110011010000000111110011010000000111110011010001110111110100000010110111110100110010110111110101100000001011111110011001000101011000001011111110110100010111111110100100101111111110110001011111111111100011000000000011000110000000010001001100000000110010011000000010100100110000000110001001100000001110010011000000100001000110000001001011001100000010100000011000000101100000110000001010000001100000011000000011000000110011100110000001101101001100000011101000011000000111110100110000010000100001100000011001110011000001000111100110000010011001001100000010100000011000001010100110000000011000000000001111101011000111110101110011111011000001111101100100111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101100111110110110011111011011001111101110000111110111010011111011101001111101111000111110111100011111011111001111110000000111111000010011111100010001111110001100111111001000011111100101001111110011000111111001100011111100110001111110011100111111010000011111101001001111110101000111111010110011111101100001111110110100111111011100011111101111001111111000000111111100010011111110010001111111001100010000000000000000000000000010000000010110001001000000000000000000000000000000000000000000000000000000000000000')
            """
            if cnt := self.toc.li_lin.cnt:
                # 'bytes' object does not support item assignment
                mutable = bytearray(self._raw)
                INNER_OFFSET_POI = 8
                for num in range(cnt + 1):
                    ptr = ba2int(buffer._unpack(16, buffer.max_PTR_bits, 0, False))
                    item_offset = self.toc.li_lin.ptr + num * GEO_LINE.size + INNER_OFFSET_POI
                    mutable[item_offset:item_offset + 2] = ptr.to_bytes(2, byteorder='big')
                    print(f"ptr2poi: {ptr:02X}")
                    # если есть POI, то еще 4 бита неясного назначения - 0000,
                    if self.toc.li_poi.cnt:
                        buffer._pop(4)      # strange = buffer._pop(4)
                        pass
                self._raw = bytes(mutable)
                del INNER_OFFSET_POI, mutable, ptr, item_offset, num, strange

            # <<<<<<<<<< TSTRs
            """
                # noqa
                071515 04  BlockType.MAP__10k400: 0x1d
                Max PTR bits: 12
            самый хвост
                0000000000000000000000000000000000000000001100011000000100010101100000110001101001100110001110010100110001111011000100010110001000101101010001011100100010111101000110000000000000000000000000000000000000000000000000000000

                8c0 15 00   delta 13/19
                1 100011000000 1 00010101 1 00000     1100011000000100010101100000
                1 100011010011 00   8D3  delta 12/18 
                1 100011100101 00   8E5  delta 11/17
                1 100011110110 00   8F6  delta e/14     'more laptevykh' ? 'tauyskaya guba' 'okhotskoe more'
                8B0 <<1        8B4<<1        8B8<<1    8BC<<1      8c0
                10001011000 10001011010 10001011100 10001011110 100011000000
                12-1 len(align word), 4 stucks

                4 штуки
                1 - флаг загружать, или 0 использовать прошлые
                ptr = max_ptr_bits
                lang = 8 bit
                last_byte = 5 bit

                затем идут адреса, в которые надо перенести сгенерированные
                эти адреса выровнены по границе word, поэтому достаточно max_ptr_bits-1 
                (фактически важен только самый первый, в него выгрузить сгенерированный bytearray)
                самое последнее - адрес, на котором окончится tstr и начнётся массив строк
            """
            
            # далее собственно TSTR TODO: а не pois?
            s_ptr = '0'
            s_lang = '0'
            s_type = '0'
            for _ in range(self.toc.li_tstr.cnt):
                off_from = buffer.av_offs
                # ptr_2_str
                if ba2int(buffer._pop(1)):
                    s_ptr = buffer._unpack_ptr()
                else:
                    # use prev value
                    buffer.result += struct_WORD.pack(int(s_ptr, 16))
                # language
                if ba2int(buffer._pop(1)):
                    s_lang = buffer._unpack_byte(8)
                else:
                    # use prev value
                    buffer.result += int(s_lang, 16).to_bytes()
                # type - last byte
                if ba2int(buffer._pop(1)):
                    s_type = buffer._unpack_byte(5)
                else:
                    # use prev value
                    buffer.result += int(s_type, 16).to_bytes()
                # ------------------------- debug
                print(f"TSTR {off_from}: {s_ptr} {s_lang} {s_type}")
                # ------------------------- debug
            del s_ptr, s_lang, s_type, off_from
            self._raw += buffer.result
            buffer.clear_result()

            # texts
            self._raw += unpacked_bin_strings

            # далее - значения ptr2table <<1  cnt = +1, +1
            #  Max PTR bites: 14-1 - т.к. выравнивание по чётному, со сдвигом на
            # shp - WORD ptr_to_table_to_strings, unarc by calculate CURR_PTR_PTSTR +4 - next ptstr
            # lin - 12: 2h - PTR ptr2table (CALCULATE == если p_str_name ПРЕДЫДУЩЕГО == 0, то НЕ инкрементируется.
            """
            bitarray('11011100000110111000101101110010011011100110000000000100000000001000000000010001000000000000000000000000000000000000000000000000')
            11011100000 DC0
            11011100010 DC4
            11011100100 DC8
            11011100110 DCC
            00000000010 4
            00000000010 4
            00000000010 4
            00100000000 200

            000
            cat 0034:0002 cnt:2     next ptr: 0040
            shp 0040:0003 cnt:3     next ptr: 0090
            lin 0090:0002 cnt:2     next ptr: 00C0
            poi 0000:0000 cnt:0
            vrt 00C0:0340 cnt:832   next ptr: 0DC0
            tst 0DC0:0003 cnt:3     next ptr: 0DCC
            strs from 0DCC
            Max PTR bites: 12
                    Max VERTEX bites: 10
            begin word :: 0D 00 08 00

            """
            # fill shp tstr (блин, а и не надо было пытаться рассчитывать)
            if cnt := self.toc.li_shp.cnt:
                # 'bytes' object does not support item assignment
                mutable = bytearray(self._raw)
                INNER_SHP_OFFSET_TSTR = 18
                for num in range(cnt + 1):
                    # ptr выровнен по word -> max_ptr_bits - 1
                    ptr = ba2int(buffer._unpack(16, buffer.max_PTR_bits - 1, 1, False))
                    item_offset = self.toc.li_shp.ptr + num * GEO_SHAPE.size + INNER_SHP_OFFSET_TSTR
                    mutable[item_offset:item_offset + 2] = ptr.to_bytes(2, byteorder='big')
                    print(f"shp ptr2tstr: {ptr:02X}")
                self._raw = bytes(mutable)
                del INNER_SHP_OFFSET_TSTR, mutable, ptr, item_offset, num

            # fill lines ptr2tstr
            """
            12: 2h - PTR ptr2StrTable (CALCULATE == если p_str_name ПРЕДЫДУЩЕГО == 0, то НЕ инкрементируется.
                        (Самый первый - 34B4 из последнего shp
                14: 2h -# (CALCULATE == 2 байта страны

            """
            if cnt := self.toc.li_lin.cnt:
                # 'bytes' object does not support item assignment
                mutable = bytearray(self._raw)
                INNER_LIN_OFFSET_TSTR = 12
                for num in range(cnt + 1):
                    # ptr выровнен по word -> max_ptr_bits - 1
                    ptr = ba2int(buffer._unpack(16, buffer.max_PTR_bits - 1, 1, False))
                    item_offset = self.toc.li_lin.ptr + num * GEO_LINE.size + INNER_LIN_OFFSET_TSTR
                    mutable[item_offset:item_offset + 2] = ptr.to_bytes(2, byteorder='big')
                    print(f"lin ptr2tstr: {ptr:02X}")
                self._raw = bytes(mutable)
                del INNER_LIN_OFFSET_TSTR, mutable, ptr, item_offset, num

            # buffer ('001000000000000000000000000000000000000000000000000')
            self.bit_tail = buffer
            # локально константами

            # чтобы при частичной распаковке нормально работал сетап - добиваем нулями
            self._raw += b'\x00' * (self.head.sizeofblock - len(self._raw))
        # =====================================================
        
        # записать распакованное
        self.write_raw()
        if not self.is_unpacked:
            print(f"Save tail into tail_{self.head.bladdr}.bin")
            with open(f"tail_{self.head.bladdr}.bin", "bw") as f:
                f.write(self.bit_tail.buffer.tobytes())
            print(f"Save unpacked into raw_{self.head.bladdr}.bin")
            with open(f"raw_{self.head.bladdr}.bin", "bw") as f:
                f.write(self._raw)
        # и, наконец, всё содержимое
        self.arr_shapes = []
        # self.lines = []
        # self.cats = []
        self.setup_objects()
        #self.setup_all_objects()
        pass

    @property
    def data_size(self) -> int:
        """
        Размер уже распакованных данных, начиная с 0
        """
        return len(self._raw)

    @property
    def max_bounds(self):
        x_b = self.max_x()
        y_b = self.max_y()
        return f"{x_b:04X} x {y_b:04X}"

    def max_x(self):
        """ максимально возможное значение x """
        delta = self.map.rigth_top._hlat - self.map.left_bottom._hlat
        delta = delta >> self.shift_scale
        return delta

    def max_y(self):
        """ максимально возможное значение x """
        delta = self.map.rigth_top._hlon - self.map.left_bottom._hlon
        delta = delta >> self.shift_scale
        return delta
        
    def max_PTR_bits(self):
        '''
         # noqa
        Max число значащих бит в near offs в блоке из 
        seg_cnt сегментов размером по seg_size
        Максимальная длинна указателя в битах 
        (по размеру блока, на 1 меньше - word wrap)

         преобразовывать строчную букву в прописную путём вычитания 32 из её кода, а прописную — в строчную путём добавления 32
        '''
        #max_addr = self._const_segsize  * seg_cnt - 1
        # # Максимально возможное значение адреса; 2 -> 0x800*2-1=0xfff
        self_size = self.head.sizeofblock
        max_addr = self_size - 1    # self.size = self._const_segsize * self.unarc_segcn
        max_adr_bin = "{:b}".format(max_addr)
        max_ptr_bits = len(max_adr_bin)  # bin(0xfff)="0b111111111111", w|o '0b' len=12
        if max_ptr_bits > 16:
            max_ptr_bits = 16   # ptr is WORD, max 16 bit - FFFF
        return max_ptr_bits

    def show_main_info(self) -> None:
        """
        debug function for printing main information
        """
        print(f"\n{self.vdo.path}\n{self.head.bladdr}  {self.head.bltype}: 0x{self.head.bltype.value:02x}")
        end = f"\tnext ptr: {(self.toc.li_cat.cnt + 1) * 4 + self.toc.li_cat.ptr:04X}" if self.toc.li_cat.cnt else ""  # noqa
        print(f"cat {self.toc.li_cat} {end}")
        end = f"\tnext ptr: {(self.toc.li_shp.cnt + 1) * 0x14 + self.toc.li_shp.ptr:04X}" if self.toc.li_shp.cnt else ""  # noqa
        print(f"shp {self.toc.li_shp} {end}")
        end = f"\tnext ptr: {(self.toc.li_lin.cnt + 1) * 0x10 + self.toc.li_lin.ptr:04X}" if self.toc.li_lin.cnt else ""  # noqa
        print(f"lin {self.toc.li_lin} {end}")
        # size poi = 6, poi got after vrtx. There are no zero poi
        end = f"\tnext ptr: {(self.toc.li_poi.cnt) * 6 + self.toc.li_poi.ptr:04X}" if self.toc.li_poi.cnt else ""  # noqa
        print(f"poi {self.toc.li_poi} {end}")
        end = f"\tnext ptr: {(self.toc.li_vrtx.cnt) * 4 + self.toc.li_vrtx.ptr:04X}" if self.toc.li_vrtx.cnt else ""  # noqa
        print(f"vrt {self.toc.li_vrtx} {end}")
        end = f"\tnext ptr: {(self.toc.li_tstr.cnt) * 4 + self.toc.li_tstr.ptr:04X}" if self.toc.li_tstr.cnt else ""  # noqa
        print(f"tst {self.toc.li_tstr} {end}")
        print(f"   strs from {self.toc.START_TXT:04X}")
        print(f"Map_hex: {self.map.hex}")
        print(f"{self.map}")
        print(f"Максимальные Х и У: {self.max_bounds} \n")
        print(f"\nMax PTR bites: {self.max_PTR_bits()}")
        pass

    def setup_toc(self) -> None:
        """
        Returns:
            None
        """
        self.toc.li_cat = self.read_list(OFFSET_LI_GEOCATEGORY)
        self.toc.li_shp = self.read_list(OFFSET_LI_GEOSHAPE)
        self.toc.li_lin = self.read_list(OFFSET_LI_GEOLINE)
        self.toc.li_vrtx = self.read_list(OFFSET_LI_VERTEX)
        self.toc.li_poi = self.read_list(OFFSET_LI_POI)
        self.toc.li_tstr = self.read_list(OFFSET_LI_TSTR)
        self.toc.START_TXT = self.toc.li_tstr.ptr + TSTR.size * self.toc.li_tstr.cnt

    def setup_objects(self) -> None:
        """

        """
        # every cat
        pc = self.toc.li_cat.ptr
        for i in range(self.toc.li_cat.cnt):
            curr_cat = self.read_category(pc)
            pc += GEO_CATEGORY.size
            print(curr_cat)
            self.arr_shapes.append(curr_cat)
            geos = []
            obj_ptr = curr_cat.ptr
            if curr_cat.draw == en_DRAW_TYPE.SHAPE:
                obj_size = GEO_SHAPE.size
                func = self.read_shape
            else:
                obj_size = GEO_LINE.size
                func = self.read_line
            for j in range(curr_cat.cnt):
                ob = func(obj_ptr, curr_cat)
                obj_ptr += obj_size
                geos.append(ob)

            self.categ[curr_cat] = geos
        return

    def read_category(self, offset: int) -> GEO_CATEGORY:
        """
        Создание категории, буффер * 2, т.к. кол-во рассчетное
        """
        res = None
        if self.is_unpacked or True:
            buff = self.read(offset, GEO_CATEGORY.size * 2)
            res = GEO_CATEGORY(buff)
        return res

    def read_shape(self, offset: int, category: en_GEO_CATEGORY) -> GEO_SHAPE:
        """
        Geo read_shape - closed, filled poligon
            2h - ptr2str/0;
            2h - ptr2vertexes (first=first vert)
            4h - id [0000 7685]
            8h - LON_LAT
            2h = 00 00 - aligment (??? or POI?)
            2h - ptr2 list strPtr
        """
        res = None
        buff = self.read(offset, GEO_SHAPE.size * 2)
        # if hlat == 0 -> tail of read_category
        # '00 00 0a ac 00 00 00 00 00 00 00 00 00 00 00 00 00 00 12 18'
        # hlat = struct_UINT.unpack(buff[8:12])[0]
        # if hlat:
        #     res = GEO_SHAPE(buff, read_category)
        res = GEO_SHAPE(buff, category)
        if self.is_unpacked:
            res.name = self.read_str(res.p_str_name)
            offset = res.ptr_vrtx
            for _ in range(res.cnt_vrtx):
                # read vertexes
                res.vrtx.append(self.read_vrtx(offset))
                offset += VERTEX.size
        return res
        # else:
        #     return None

    def read_line(self, offset: int, category: en_GEO_CATEGORY) -> GEO_LINE:
        """
        # noqa
        Geo segment of line - poligon
            2h - PTR         p_str_name - ptr2str/0;
            2h - PTR         p_vertexes_obj; ptr2vertexes
            4h - DWORD       id
            2h - PTR   ptr_linesign, p_line_sign; // Or start pstr -=== POI
            2h - WORD  or_b_or_c;
            2h - PTR   p_p_str_name; // ptr to GEO_OBJ_STR
            4h - WORD   or_38_or_0_b_country;
        """
        res = None
        if self.is_unpacked:
            buff = self.read(offset, GEO_LINE.size * 2)
            res = GEO_LINE(buff, category)
            # TODO  '02F4 0158 0000673A  02A0 00 00 02 CE 00 00' - добавить cnt poi
        
            res.name = self.read_str(res.p_str_name)
            # res.tstr_regi = self.read_tstr(res.tstr_regi)  # 2 POI, НЕ регион... self.POI_regi
            res.tstr_name = self.read_tstr(res.tstr_name)

            offset = res.ptr_vrtx
            for _ in range(res.cnt_vrtx):
                # read vertexes
                res.vrtx.append(self.read_vrtx(offset))
                offset += VERTEX.size
        return res

    def read_vrtx(self, offset: int) -> VERTEX:
        """

        """
        res = None
        if True or self.is_unpacked:
            buff = self.read(offset, VERTEX.size)
            res = VERTEX(buff)
            # TODO - а может при создании вертекса сюда же еще и реальные координаты?
        return res

    def read_tstr(self, offset: int) -> TSTR:
        """

        """
        res = None
        if True or self.is_unpacked:
            buff = self.read(offset, TSTR.size)
            if offset < self.toc.START_TXT:
                res = TSTR(buff)
                res.name = self.read_str(res.p_str)
                #print(res.name)
            else:
                res = self.read_str(offset)
        return res

    # -------------------------------------------
    # -------------------------------------------
    def get_all_categories(self) -> Iterator[GEO_CATEGORY]:
        """
        Yeld:
            next category
        """
        offset = self.toc.li_cat.ptr
        # -1 -- самая последняя категория - нулевая с замыкающими ptr
        for i in range(self.toc.li_cat.cnt):
            res = self.read_category(offset)
            self.cats.append(res)
            offset += GEO_CATEGORY.size
            yield res

    def read_tstr_str(self, offset: int) -> str:
        """
        toc.li_str -  облом 0x7c - b'\x00\x80\x02\x00atlantic oce' # noqa: E501
        """
        # val = self.read(offset, 4)
        '''
        //GEO_OBJ_STR
        typedef struct{
            PTR p_str;
            en_LANGUAGE lang;
            en_GEO_OBJ_STR str_type;
            
        typedef enum <uchar>{
            __shape =   0,
            __alias =   2,
            __street =  8,
            __poliline =0x10
        }en_GEO_OBJ_STR

        '''
        offset_str = self.ushort(offset)
        result = self.read_str(offset_str)
        return result
