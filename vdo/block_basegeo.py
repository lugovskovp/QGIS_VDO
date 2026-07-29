"""
block_basegeo - Базовый тип для - карт   00 16 15 1c 14 1d 1e # noqa: E116
bitstream - class wrapper for bitarray
"""

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
                                 struct_WORD,
                                 struct_4BYTES,
                                 BITS_IN_ASCII,
                                 BITS_IN_BYTE,
                                 BITS_IN_WORD,
                                 BITS_IN_UINT,
                                 LOOKUP_CHAR_BYTES)


OFFSET_LI_GEOCATEGORY = 0x08    # geodata types (categories)
OFFSET_LI_GEOSHAPE = 0x0c       # гео SHAPES - замкнутые полигоны
OFFSET_LI_GEOLINE = 0x10        # линии
OFFSET_LI_VERTEX = 0x14         # точки word, word
OFFSET_LI_POI = 0x18            # poi`s`
OFFSET_LI_TSTR = 0x1c           # ptrs tstr - индексы строк en_GEO_OBJ

OFFSET_PACKED_DATA = 0x34  # ТИПЫ БЛОКОВ archived type_1_vdo_pack
                            # bmw ee bnl:  00 16 15 1c 14 1d 1e # noqa: E116
                            # в них незапакованы первые 0х34 # noqa: E116

BITS_IN_CATEGORY_TYPE = BITS_IN_BYTE - 1   # packed cat type len = 7 bit

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
            #    self.toc.li_vrtx,    # не ошибка, нужен offset vrtx
            #    self.toc.li_tstr        # и list tstr тоже надо
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

bitarray('011110011100101100011111001110100000111001100101100011111001100100000111001000111100011111010000000011110011100111100011111001110100000111001001101100011111001100101000100010100111100011111010000000011110011100111100011111
000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
110001011100000011000101110000001100010111001100110001101110110011001000000010111100100100101011110010010010101111001001001010111100100100101011110010010010000011100110100101000101011000001110011100011001110011101111001110011110110001110100000000001110100010001100001110000011101000111101000101010000000000111010010111010000000011000000000011101001100110011101001101110011001001001110010010111100100110111001001111110010011111100100111111001001111110010100011100101001111001010101110010101111100101100111001011011110010111011100101111111001011111110010111111100101111111001100001110011000111100110010111001100101110011001011100110011111001101001001000000000000000001000000001010000000100000000101100010001000000000000000000000000000000000000')

01111
0011100101100011111
001110100000111001100101100011111
0011001000001110010001111000111110
100000000111100111001111000111110
011101000001110010011011000111110
011001010001000101001111000111110
100000000111100111001111000111110

01111 00111 0010 1100011111
001110100000111001100101100011111
00110 01000001 1100100011 1100011111
01000 000001111001110011 1100011111
00111 01000001 1100100110 1100011111
00110 010100010001010011 1100011111
01000 000001111001110011 1100011111

bitarray('1000000110110100010110001100001001000001000100100010110010000000010001011110100100010110001100001001000000110100100010110001110001001000000100110100010110010000000010001011110100100010110001110001001000000010110100010110001100001001000000100100100010110010000000010001011110100100010110001110100011110110010111000011110001100100010001010010101000011110010000100110010011100101000011110010000100011110011000101000011110000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001100011010000001100011010000001100011010000001100011010000001100011010000001100011010000001100011010010111100100011010111100101100010111100110101010111101000001000001110110000101000001111000001110110010010011101101010000111011100100001110111011000011101111100100111011111111000000001111000010101000011000000000111100010111100000000110000000000111100011010001101000001110100001111010001011101000101110100011111010010011101001011110100110111010011111101010001110101001111010100111101010101110101011111010110011101011001110101100111010110011101011011110101110111010111111101100001001000000000000000000000100000000010010000010000000011001100100000000000000000000000000000000')

100000011011010001011000110000100100000100010010001011001000000001000101111010010001011000110000100100000011010010001011000111000100100000010011010001011001000000001000101111010010001011000111000100100000001011010001011000110000100100000010010010001011001000000001000101111010010001011000111010001111011001011100001111000110010001000101001010100001111001000010011001001110010100001111001000010001111001100010100001111

10000
0011011010001011000110000100100000100010010001011001000000001000101111010010001011000110000100100000011010010001011000111000100100000010011010001011001000000001000101111010010001011000111000100100000001011010001011000110000100100000010010010001011001000000001000101111010010001011000111010001111011001011100001111000110010001000101001010100001111001000010011001001110010100001111001000010001111001100010100001111


1000 13/11/9
00011011010001011
000110000100100000100010010001011
001000000001000101111010010001011
000110000100100000011010010001011
000111000100100000010011010001011
001000000001000101111010010001011
000111000100100000001011010001011
000110000100100000010010010001011
001000000001000101111010010001011
000111010001111011001011100001111
000110010001000101001010100001111
001000010011001001110010100001111
001000010001111001100010100001111

bitarray('00101100=2c/44 20/13/10
011001011111101101101000101100
011101011111110001001000101100
100000100000010001101000101100
100000100000000001101000101100
011111001001110010101011010001
011000110010111111011010010001
011001000001000000100010010001
011001000001000000000010010001
011000110110010011100101010110
100010110001110101111110110100
100010110010000010000001000110
100010110010000010000000000110
100010110001111100100111001010
001101000101100011011001001110
010101010010001011001000001000
000100010010001011001000001000
000000010010001011000000000000
000000000000000000000000000000
000000000000000000000000000000
000000000000000000000000000000
000000000000000000000000000000

000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000100001111010000001000011110100000010000111101000000100001111010000001000011110100000010000111101000000100001111010000001000011110100000010000111101001011100010000110010111000100100100101110001001111001011100010101010010111000101101100000011000110110100100001100100000110001110000000011000111001100001100011101010110001010101100011101111110000110001100011110011000110001111100001000101010110001111110011000011000110010000000101000101010110010000101001000011000110010000111100011001000101011001100100011010100110010010000001000000001100000000000000001000101101101000101101101000101110001000101110101000101111001000101111101000110000001000110000101000110001001000110001101000110001101000110001101000110010001000110010101000110011001000110011101000110100001000110100001000110100001000110100101000110101001000110101101000110110001000110110100010000000000000000000000010000000001001000000010000000000000000000000000000000000')

0010110
001100101111110110110100010110
001110101111111000100100010110
010000010000001000110100010110
010000010000000000110100010110
00111110010011100101010110100010110001100101111110110100100010110010000010000001000100100010110010000010000000000100100010110
00110110010011100101010110100010110001110101111110110100100010110010000010000001000110100010110010000010000000000110100010110001111100100111001010001101000101100011011001001110010101010010001011001000001000000100010010001011
010000010000000000100100010110

bitarray('Max PTR bites: 13   Max VERTEX bites: 11    begin word :: 10 11 09 00
10010010111011101110100000010101000110101110111011001000000101001001001011101110111010000001010110111010111011101100100000010101000100101110111011101000000101100001101011101110110010000001010110010010111011100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000

05b1f8 0d  ('Max PTR bites: 14        Max VERTEX bites: 11    begin word :: 10 12 09 00
poi 1F34:0006 cnt:6     next ptr: 1F58
101110111
0110010000001010000100101110111
0111010000001010100110101110111
0110010000001010010100101110111
000000000000000000

bitarray('1011101110110010000001010000100101110111011101000000101010011010111011101100100000010100101001011101110000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000111110011010000000111110011010000000111110011010000000111110011010000000111110011010000000111110011010000000111110011010000000111110011010000000111110011010000000111110011010000000111110011010000000111110011010001110111110100000010110111110100110010110111110101100000001011111110011001000101011000001011111110110100010111111110100100101111111110110001011111111111100011000000000011000110000000010001001100000000110010011000000010100100110000000110001001100000001110010011000000100001000110000001001011001100000010100000011000000101100000110000001010000001100000011000000011000000110011100110000001101101001100000011101000011000000111110100110000010000100001100000011001110011000001000111100110000010011001001100000010100000011000001010100110000000011000000000001111101011000111110101110011111011000001111101100100111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101100111110110110011111011011001111101110000111110111010011111011101001111101111000111110111100011111011111001111110000000111111000010011111100010001111110001100111111001000011111100101001111110011000111111001100011111100110001111110011100111111010000011111101001001111110101000111111010110011111101100001111110110100111111011100011111101111001111111000000111111100010011111110010001111111001100010000000000000000000000000010000000010110001001000000000000000000000000000000000000000000000000000000000000000')

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
        self.toc.li_cat = self.list(OFFSET_LI_GEOCATEGORY)
        self.toc.li_shp = self.list(OFFSET_LI_GEOSHAPE)
        self.toc.li_lin = self.list(OFFSET_LI_GEOLINE)
        self.toc.li_vrtx = self.list(OFFSET_LI_VERTEX)
        self.toc.li_poi = self.list(OFFSET_LI_POI)
        self.toc.li_tstr = self.list(OFFSET_LI_TSTR)
        self.toc.START_TXT = self.toc.li_tstr.ptr + TSTR.size * self.toc.li_tstr.cnt

    def setup_objects(self) -> None:
        """

        """
        # every cat
        pc = self.toc.li_cat.ptr
        for i in range(self.toc.li_cat.cnt):
            curr_cat = self.category(pc)
            pc += GEO_CATEGORY.size
            print(curr_cat)
            self.arr_shapes.append(curr_cat)
            geos = []
            obj_ptr = curr_cat.ptr
            if curr_cat.draw == en_DRAW_TYPE.SHAPE:
                obj_size = GEO_SHAPE.size
                func = self.shape
            else:
                obj_size = GEO_LINE.size
                func = self.line
            for j in range(curr_cat.cnt):
                ob = func(obj_ptr, curr_cat)
                obj_ptr += obj_size
                geos.append(ob)

            self.categ[curr_cat] = geos
        return

    def category(self, offset: int) -> GEO_CATEGORY:
        """
        Создание категории, буффер * 2, т.к. кол-во рассчетное
        """
        res = None
        if self.is_unpacked or True:
            buff = self.read(offset, GEO_CATEGORY.size * 2)
            res = GEO_CATEGORY(buff)
        return res

    def shape(self, offset: int, category: en_GEO_CATEGORY) -> GEO_SHAPE:
        """
        Geo shape - closed, filled poligon
            2h - ptr2str/0;
            2h - ptr2vertexes (first=first vert)
            4h - id [0000 7685]
            8h - LON_LAT
            2h = 00 00 - aligment (??? or POI?)
            2h - ptr2 list strPtr
        """
        res = None
        buff = self.read(offset, GEO_SHAPE.size * 2)
        # if hlat == 0 -> tail of category
        # '00 00 0a ac 00 00 00 00 00 00 00 00 00 00 00 00 00 00 12 18'
        # hlat = struct_UINT.unpack(buff[8:12])[0]
        # if hlat:
        #     res = GEO_SHAPE(buff, category)
        res = GEO_SHAPE(buff, category)
        if True or self.is_unpacked:
            res.name = self.read_str(res.p_str_name)
            #
            vrtx = []
            offset = res.ptr_vrtx
            for vrt in range(res.cnt_vrtx):
                # read vertexes
                vrtx.append(self.vrtx(offset))
                offset += VERTEX.size
            res.vrtx = vrtx
            # пара неизвестных???
        return res
        # else:
        #     return None

    def line(self, offset: int, category: en_GEO_CATEGORY) -> GEO_LINE:
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
            # res.tstr_regi = self.tstr(res.tstr_regi)  # 2 POI, НЕ регион... self.POI_regi
            res.tstr_name = self.tstr(res.tstr_name)

            vrtx = []
            offset = res.ptr_vrtx
            for vrt in range(res.cnt_vrtx):
                # read vertexes
                vrtx.append(self.vrtx(offset))
                offset += VERTEX.size
            res.vrtx = vrtx
        return res

    def vrtx(self, offset: int) -> VERTEX:
        """

        """
        res = None
        if True or self.is_unpacked:
            buff = self.read(offset, VERTEX.size)
            res = VERTEX(buff)
            # TODO - а может при создании вертекса сюда же еще и реальные координаты?
        return res

    def tstr(self, offset: int) -> TSTR:
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
            res = self.category(offset)
            self.cats.append(res)
            offset += GEO_CATEGORY.size
            yield res

    def read_tstr(self, offset: int) -> str:
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


# --------- bitstream - Class wrapper for bitarray

class bitstream():
    ''' Class wrapper for bitarray '''
    buffer: bitarray        # входной поток битов
    result: bytes           # распакованные данные

    def __init__(self, barray: bytes,
                 offset: int,
                 parent) -> None:
        """
        Args:
            barray: bytes
            offset: int         offset от начала блока, который сейчас будет распаковываться
            parent:        base_geo, в котором инициализируется
        """
        # Похоже работает только в конкретном наборе 0500 0900, 0516 0900
        # первый dword - назначение неизвестно. 83888384 = 500 900
        (word_a, word_b, word_c, self.word_d) = struct_4BYTES.unpack(barray[:4])
        barray = barray[4:]
        # [x] 05: a - ? id line, сколько бит читать, если флаг показывает отсутствие - 1-32, 0-this
        self.max_bits_id_line_if_0 = word_a
        # [x] 12: b - для id shape (+line?) - сколько бит читать, если флаг показывает отсутствие - 1-32, 0-this
        self.max_bits_id_shape_if_0 = word_b
        # [x] 09: c - 9 -столько бит в дельте XY (8, 9, a)
        self.max_bits_in_vertex_delta = word_c
        # [ ] 00: d - ?   пока только 00 встречался. повесить raise

        # debug raises
        if word_a not in [5, 0xc, 0xd, 0xe, 0xf, 0x11, 0x10]:
            raise ValueError(word_a, f"0x{self.word_a} .word_a")
        if word_c not in [8, 9, 0x0a]:
            raise ValueError(word_c, f"0x{self.word_c} .word_c")
        if self.word_d not in [0]:
            raise ValueError(self.word_d, f"0x{self.word_d} .word_d")

        #
        self.parent = parent

        # Первый DWORD распакован. В буфер - всё, что далее
        self.buffer = bitarray(buffer=barray, endian='big').copy()    # copy - else read only memory # noqa
        self.result = bytearray()   # empty

        self.offset_start = offset      # текущий offset складывается из _raw и buffer.result
        self.counter_tstr_table_str = 0

        # 05576f 02  BlockType.MAP__07k40: 0x16:: max_bit_ptr = 11, but maxnum vrtx = FF (8, not 9) # noqa
        self.max_bits_num_vrtx = len(f"{parent.toc.li_vrtx.cnt:b}")
        self.max_PTR_bits = parent.max_PTR_bits()    # max possible bits in near offset
        self.start_vrtx_ptr = parent.toc.li_vrtx.ptr           # start_vrtx_ptr стартовый offset vertexes
        self.offset_tstr = parent.toc.li_tstr.ptr    # tstr стартует с этого смещения, каждый объект - + 1  # noqa

        pass    # __init__
    
    @property
    def av_head(self):
        """ Начало битов - 40 штук """
        res = self._touch(40).to01()
        return res
    
    def clear_result(self):
        """ Актуализирует стартовый оффсет и очищает результат """
        self.offset_start = int(self.av_offs, 16)
        self.result.clear()

    @property
    def av_offs(self):
        current_offset = self.offset_start + len(self.result)
        res = f"{current_offset:04x}"
        return res

    @property
    def res(self):
        ''' online see result values'''
        return " ".join("{:02x}".format(c) for c in self.result)
    
    def _pop(self, qty_bits: int) -> bitarray:
        '''_pop qty_bits from begin (left) buffer qty bites'''
        val = self.buffer[:qty_bits]   # взять первые qty_bits бит
        del self.buffer[:qty_bits]      # удалить qty_bits из начала
        return val
    
    def _touch(self, qty_bits: int, start: int = 0) -> bitarray:
        ''' Return qty bits from start Without deleting'''
        val = self.buffer[start:start + qty_bits].copy()
        return val

    def next_bit_true(self):
        """
        pop бит, и если = 1 вернуть True, else False
        """
        if self._pop(1) == bitarray('1'):
            return True
        return False

    def _unpack(self, bit_goal: int, bit_compressed: int, left_shift: int=0, bool_save: bool=True) -> str | bitarray:  # noqa:
        """
        Args:
            bit_goal: int  bits in result
            bit_compressed: int how many bits _pop from self
            left_shift: int=0 - qty left shift result
            bool_save: bool save into self.result
        Returns:
            str: String with hex value, f.e. '00a8'
        """
        res = self._pop(bit_compressed)  # _pop bits from buffer
        val = bitarray((bit_goal - (res.nbytes * 8 - res.padbits)) * '0')  # leading zeroes  # noqa
        val += res                      # append lead zero with result
        val <<= left_shift              # left shift if lsch > 0
        # можно не сохранять - если значение надо интерпретировать перед сохранением
        if not bool_save:
            return val  # но тогда возвращать bitarray
        # в последовательность байтов   bres = val.tobytes() - только значащие байты, увы.  # noqa
        bres = val.tobytes()
        self.result += bres
        str_res = ''
        for h in bres:
            str_res += "{:02x}".format(h)   # str_res - for debug ))))
        return str_res   # bres

    def _unpack_byte(self, bit_compressed: int, left_shift: int = 0) -> str:
        """
        unpack one byte from bit_compressed to self.buffer
        Args:
            bit_compressed:  Количество бит для интерпретации, как байт
            left_shift: сдвиг влево после распаковки
        """
        if bit_compressed > BITS_IN_BYTE:
            raise ValueError(bit_compressed, f"Значение больше {BITS_IN_BYTE}, _unpack_byte")
        str_res = self._unpack(BITS_IN_BYTE, bit_compressed, left_shift)
        return str_res
    
    def _unpack_word(self, bit_compressed: int = BITS_IN_WORD) -> str:
        """
        Распаковывает BITS_IN_WORD(16 бит), как short и добавляет значение в self.result.
        Args:
            bit_compressed: int - количество бит, которые преобразуются в результат
        Returns:

        """
        if bit_compressed > BITS_IN_WORD:
            raise ValueError(bit_compressed, f"Значение больше {BITS_IN_WORD}, _unpack_word")
        res = self._unpack(BITS_IN_WORD, bit_compressed, 0)
        return res

    def _unpack_uint(self, bit_compressed: int = BITS_IN_UINT) -> str:
        """
        Распаковывает BITS_IN_UINT (32 бита) и добавляет значение в self.result.
        Args:
            bit_compressed: int - количество бит, которые преобразуются в результат
        """
        if bit_compressed > BITS_IN_UINT:
            raise ValueError(bit_compressed, f"Значение больше {BITS_IN_UINT}, _unpack_uint")
        res = self._unpack(BITS_IN_UINT, bit_compressed, 0)
        return res

    def _unpack_ptr(self, left_shift: int = 0) -> str:
        """
        unpack word (packed len=max_bits_ptr) to self.buffer
        Args:
            qty_bit:  Количество бит для интерпретации, как байт
            left_shift: сдвиг влево после распаковки
        Returns:
            str: string with hex value
        """
        str_res = self._unpack(BITS_IN_WORD, self.max_PTR_bits, left_shift)
        return str_res

    def _unpack_vertex_offset(self) -> int:
        """
        Упакованы не смещения, а номера вертексов в общем списке.
        """
        # номер самого первого, 0-го vrtx объекта не сохранять в result!  # noqa
        # -2: надо в 4 раза меньше бит, т.к. ptr vrtx кратен 4 -> self.max_PTR_bits - 2
        # UPD: no, need calc max till init
        num_vrtx = self._unpack(BITS_IN_WORD, self.max_bits_num_vrtx, 0, False)  # не сохранять в result!  # noqa
        num_vrtx = ba2int(num_vrtx)     # номер 0-го vrtx объекта
        # 4* num  = offset from start vertexes, + tos.li_vrtx.ptr = near offset
        vrtx_offset = self.start_vrtx_ptr + VERTEX.size * num_vrtx
        print(f"    start_vrtx num: {num_vrtx} offset: {vrtx_offset:04x}")
        self.result += struct_WORD.pack(vrtx_offset)     # vertx offs 2word, save
        return vrtx_offset

    def _unpack_half_vertex(self, prev: int) -> int:
        """
        Декодирует одну из координат (short x или y) vertex и добавляет значение в self.result.
        В зависимости от первых 2-х префиксных бит:
         - '11' - read 16 bit, считать все 16 бит, как значение.
         - '10' - read 9 бит, вычесть значение из предыдущего
         - '01'
         - '00'
        Args:
            prev: short int - Предыдущее значение дельты.
        Returns:
            int: short значение координаты x или y
        """

        # if self.word_B == 0x900:        # 500 900, 512 900, 516 900
        #     bits_to_read = 9   # wtf? why?
        # elif self.word_B == 0x800:        #  512 800,
        #     bits_to_read = 8
        # elif self.word_B == 0xA00:        #  0557A302 00 16 01: 513 a00
        #     bits_to_read = 10
        # else:
        #     raise ValueError(self.word_B, f"{self.word_B} self.word_B")
        
        # третий байт первого uint - к-во бит
        bits_to_read = self.max_bits_in_vertex_delta

        prefix = self._pop(2).to01()
        
        if prefix == '11':
            # load full short
            res = self._unpack_word()
            return res

        if prefix == '10':
            # read 9 бит, вычесть значение из предыдущего
            val = -ba2int(self._unpack(BITS_IN_WORD, bits_to_read, 0, False))

        elif prefix == '01':
            # read 8 бит, и +добавить ~9й~ старший
            val = ba2int(self._unpack(BITS_IN_WORD, bits_to_read - 1, 0, False))
            val = (1 << bits_to_read) | val       # 0b100000000 | val

        elif prefix == '00':
            # read 8 бит, и 9й - всё равно 0
            val = ba2int(self._unpack(BITS_IN_WORD, bits_to_read - 1, 0, False))

        # 0 - сложить, 10-вычесть, 11 - уже вернули
        val = prev + val
        res = struct_WORD.pack(val)
        self.result += res
        ret = ""
        for h in res:
            ret += "{:02x}".format(h)   # str_res - for debug ))))
        return ret
        
    def _unpack_ptr_word(self, left_shift: int = 0) -> None:
        """
        ptr, выровненный по word
        unpack word (len=max_bits_ptr - 1) to self.buffer
        Args:
            left_shift: сдвиг влево после распаковки
        """
        str_res = self._unpack(BITS_IN_WORD, self.max_PTR_bits - 1, left_shift)
        return str_res

    # def DELETE_THIS_ptr_dword(self, left_shift: int = 0) -> None:
    #     """
    #     ptr, выровненный по dword
    #     unpack word (len=max_bits_ptr - 2) to self.buffer
    #     Args:
    #         left_shift: сдвиг влево после распаковки
    #     """
    #     str_res = self._unpack(BITS_IN_WORD, self.max_PTR_bits - 2, left_shift)
    #     return str_res

    #---------------------------------------------------
    def unpack_category(self) -> None:
        """
        BYTE  en_GEO_CATEGORY <--- 7 bits
        BYTE  0poligon_1poliline en_DRAW_TYPE <--- 1 bit
        WORD  ptr_to_category PTR <--- max_PTR_bits-1 bits
        """
        # /0/
        # res = self._unpack_byte(BITS_IN_CATEGORY_TYPE)    # 7 bit на
        self._unpack_byte(BITS_IN_CATEGORY_TYPE)    # 7 bit на
        
        # en_GEO_CATEGORY
        # /1/
        self._unpack_byte(1)    # 1 бит на полигон0/полилиния1
        
        # en_DRAW_TYPE
        # /2/
        # left shift 1 - т.к. last = 0 always in this ptr
        self._unpack_ptr_word(1)    # максимальное к-во бит для near ссылки word

    def unpack_shape(self, this_will_increment: bool) -> None:
        """
        Args: 
            this_will_increment: bool - инкрементировать текущий ptrst?
        Returns:
            do_next_increment bool:   инкрементировать следующий ptrst

        # noqa
        WORD - ptr2string <--- word, ptr 2 zero-ended string
        WORD ptr2firstVertex  <--- запакованы не offs, а номера вертексов, vertnum, надо расчитывать ptr - offset
        DWORD id <----- read bit, if 1 - read next32bits as id, if not - so, not
        COORD - qword <--- coord 64bits
        ZeroWord align <--- no in arc
        WORD ptr_to_table_to_strings, unarc by calculate CURR_PTR_PTSTR +4 - next ptstr
        == # в хвостовом vertex = ptrStrTable, последний pstrt = pstrt + 4*pstr.cnt
        """

        # /0/ WORD - ptr2string <--- word, ptr to zero-ended string
        # if 0 - zero tail ptr2table str -- вот кстати вопрос - на точно ли так надо ваще????
        # flag_calc_ptr2tstr = self.unpack(BITS_IN_WORD, self.max_PTR_bits, 0) != '0000'
        do_next_increment = self._unpack_ptr() != '0000'
        #
        """
        begin word = 0500:0900   self.ptr()
        WORD - ptr2string
        tst 08B0:0004 cnt:4     next ptr: 8c0  strs from 08c0  100011000000  max_PTR_bits=12
        '100011000000 0000000000 101000000000000011'
        """

        # /1/ word, ptr 2 first vertex
        # запакованы не offs, а номера вертексов vertnum,
        # v_off = self._unpack_vertex_offset()
        self._unpack_vertex_offset()

        # /2/  dword, id
        #id - если следующий бит = 1, ЕСТЬ 32бит ID, иначе bits_to_unpack_then_zero
        if self.next_bit_true():
            self._unpack_uint()
        else:
            self._unpack_uint(self.max_bits_id_shape_if_0)

        # /3/  dword dword - coord, here '08 c0 00 a0 40 01 8d 00'
        # координаты - они есть, всегда. Просто лежат без упаковки  '0010010001110101000001011000010011100010'
        self._unpack_uint()        # _lon
        self._unpack_uint()        # _lat
        """
        ptr2string, ptr2firstVertex, id, coord
        begin word = 0500:0900   self.ptr(), calc_vrtx_offs, 2*uint
        #map = '3C6D9000 137A5000  3F6D9000 167A5000   00 01 00 0A  '
        # '08c0 00a0 40018d00  3e8b4ff4 14629e01'
        # '08d3 0298 40023ff0  3fd40fe0 143eb269'
        # '08e5 0344 40042b13  3e757994 13e8ef5a'
        # '08f6 0770 4012e8aa  3b0ebb42 12266183'
        #

        8d3 (prev str + 13), vrtx_n = 7e
        '100011010011 0001111110 101000000000000100'
        """

        # /4/  word align
        self.result += b'\x00' * 2
        
        # /5/ word - ptr2table
        # WORD ptr_to_table_to_strings, unarc by calculate CURR_PTR_PTSTR +4 - next ptstr  # noqa
        
        if this_will_increment:
            self.offset_tstr += TSTR.size
        self.result += struct_WORD.pack(self.offset_tstr)

        return do_next_increment
    # -------------------------- unpack shp

    def unpack_line(self, this_will_increment: bool) -> None:
        """
        Args: 
            this_will_increment: bool - инкрементировать текущий ptrst?
        Returns:
            do_next_increment bool:   инкрементировать следующий ptrst

        # noqa
            Geo segment of line - poligon
            0:  2h - PTR         p_str_name - ptr на 0-ended str; =max_ptr_bit_len
            2:  2h - PTR         ptr_vrtx - vrtx num; =max_vrtx_num_bits_len
            4:  4h - DWORD       id; 1 =32; 0 =max_bits_id_line_if_0 (word_a)
            8:  2h - PTR   ptr_POI, но если POI нет, то на ptr2first TSTR (CALCULATE == tos.li_tstr.ptr)
            10: 2h - (CALCULATE == \x00 ?(if not POI) )
            12: 2h - PTR ptr2StrTable (CALCULATE == если p_str_name ПРЕДЫДУЩЕГО == 0, то НЕ инкрементируется. 
                    (Самый первый - 34B4 из последнего shp
            14: 2h -# (CALCULATE == 2 байта страны , 
                при распаковке - константу, пусть FFFF
            для распакованного: EO_LINE_struct = struct.Struct(">HHLHHHHxxH12x")
            print(f"\n p_str  p_vrtx  id  p_beg_tstr  align  p_tstr  unkn")
        """
        # /0/  p_str_name - ptr на 0-ended str; =max_ptr_bit_len
        do_next_increment = self._unpack_ptr() != '0000'

        # /1/  ptr_vrtx ??, запакованы не offs, а ПОРЯДКОВЫЕ номера вертексов vertnum,
        # vrtx_off = self._unpack_vertex_offset()
        self._unpack_vertex_offset()

        # /2/ > dword id ?? (полный ли DWORD? если нет, то сколько бит грузить?)
        if self.next_bit_true():
            self._unpack_uint(BITS_IN_WORD)       # TODO 16??? Почему???
        else:
            self._unpack_uint(self.max_bits_id_line_if_0)    # bits_to_unpack_then_zero???
        
        # /3/ CALC  ptr_POI, но если POI нет, то на ptr2first TSTR (CALCULATE == tos.li_tstr.ptr)
        self.result += struct_WORD.pack(self.parent.toc.li_tstr.ptr)

        # /4/  align? max_speed? 0x0b, 0x0c, 0x00 etc
        self.result += b'\x00' * 2      # word_or_b_or_c word align?

        # /5/ ptr2table CALC  this_will_increment  CALC если p_str_name ПРЕДЫДУЩЕГО == 0, то НЕ инкрементируется.
        # WORD ptr_to_table_to_strings, unarc by calculate CURR_PTR_PTSTR +4 - next ptstr  # noqa
        # TODO или зависит от типа категории? или типа блока?
        # PS: после распаковки строк - сюда распакуются p2tstr
        if this_will_increment:
            self.offset_tstr += TSTR.size
        self.result += struct_WORD.pack(self.offset_tstr)
        # если p_str_name ПРЕДЫДУЩЕГО == 0, то НЕ инкрементируется. Самый первый - 34B4 из последнего shp
        
        # /6/ CALC 2 байта , в 16, 15 - код страны en_TeleAtlasRegion.
        # TODO: При "распаковке" - подставлять страну ?
        self.result += b'\xff' * 2      # при распаковке - константу, пусть FFFF

        pass
        # print(BYTESTRUCT(self.result))

        return do_next_increment

        pass

    def unpack_str(self) -> bytes:
        """
        Распаковывает все строки
        Returns:
            bin_str: бинарное представление строковой части zero-ended строк
        """
        # первыми 2 ptr - начало и окончание строки
        ptr_start = int(self._unpack_ptr(), BITS_IN_WORD)   # BITS_IN_WORD = 16
        ptr_end = int(self._unpack_ptr(), BITS_IN_WORD)
        strings_length = ptr_end - ptr_start
        del ptr_end, ptr_start
        
        # self.res на этом месте - 4 байта
        # clear. вааобще то сюда tstr надо, которые еще не распаковывались) # noqa 
        self.result.clear()

        # далее - подготовка преамбулы для хаффмановского декодирования
        # преамбула - словарь из 6 элементов с ключами от 110100001 до 110100110
        # но 11 это преамбула, поэтому от 0100001 до 0100110
        preambula = {}
        for k in range(0b0100001, 0b0100111):
            # первые 3 бита = 000
            if beg_marker := ba2int(self._pop(3)):             # val.to01() != '000':
                raise ValueError(f"WTF? В начале строк преамбулы ожидалось 000, а не '{beg_marker:3b}'")    # noqa
            del beg_marker

            # затем 2 бита - количество ascii chars для чтения
            if not (n := ba2int(self._pop(2))):         #  11 и 01 точно да, а остальные варианты - хз.  # noqa
                # Вроде 00 не может быть - иначе зачем 6 шт где не кодируется ничего?
                raise ValueError(f"WTF? В количестве ch преамбулы не ожидалось 00, а тут '{n:2b}'")    # noqa
            #теперь загрузить n chars
            val = b''
            for _ in range(n):
                # и грузятся ascii коды по 7 бит
                ascii = ba2int(self._pop(BITS_IN_ASCII))
                bch = ascii.to_bytes(1, byteorder='big')
                val += bch
            preambula[f"{k:07b}"] = val

        # и вот только теперь пошли буквы, закодированные ....эммм.
        # .. как бы хафманом, но с нюансами
        res = b''
        for _ in range(strings_length):
            prefix = self._pop(2)
            if prefix.to01() == '11':
                ba = self._pop(BITS_IN_ASCII)
                if ba.to01() in preambula:
                    # о, сокращённенькое из преамбулы
                    pre_chars = preambula[ba.to01()]
                    # но если из преамбулы возвращается А
                    if pre_chars == b'A':
                        res += ba2int(ba).to_bytes(1, byteorder='big')
                    else:
                        res += pre_chars
                elif ba2int(ba) < 32:       # похоже загрузить ascii до ' '
                    """
                    ISO 8859-2 xor win1250?
                    """
                    # а это 1250
                    code = 0xe0 + ba2int(ba)  # угу, эмпирическое волшебное число 0xe1, ацавить, 0xE0
                    # ascii = code.to_bytes(1, byteorder='big')
                    res += code.to_bytes(1, byteorder='big')
                else:
                    # или ascii код буквы
                    # ascii = ba2int(ba)
                    res += ba2int(ba).to_bytes(1, byteorder='big')
                continue        # всё, данные итерации загружены
            elif prefix.to01() == '00':
                prefix += self._pop(1)
            elif prefix.to01() == '01':
                prefix += self._pop(2)
            else:       # elif prefix.to01() == '10':
                prefix += self._pop(3)
            # вытаскиваем, что получилось, из дерева и добавляем к результату
            res += LOOKUP_CHAR_BYTES[prefix.to01()]
        # всё, упакованные буквы окончились

        # подрезать хвосты - по длинне могло подрасти из-за использования преамбулы
        res = res[:strings_length]
        # unic = res.replace(b"\x00", b".")
        # unic = unic.decode('cp1250')
        # print(f"{unic}\n")
        return res

    pass   # class unpack_type_one():
