"""
bitstream - class wrapper for bitarray
"""

from __future__ import annotations

from QGIS_VDO import bitarray, ba2int

from QGIS_VDO.vdo.geotypes import (
    VERTEX,
    TSTR,
    # BYTESTRUCT,
)

from QGIS_VDO.vdo.consts import (
    struct_WORD,
    struct_4BYTES,
    BITS_IN_ASCII,
    BITS_IN_BYTE,
    BITS_IN_WORD,
    BITS_IN_UINT,
    LOOKUP_CHAR_BYTES,
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

class bit_stream():
    '''
    Распаковщик geo-блоков: @ 070EFB07 0014 01 09 [14:MAP__05k200]
    '''
    # __slots__ = ('vdo', 'is_unpacked', '_head_cached', 'type', 'type_name')
    # __slots__ = ('res', 'buffer', 'head', 'map', 'shift_scale', 'li_cat',
    #  'li_shp', 'li_lin', 'li_vrtx', 'li_poi', 'li_tstr')

    def __init__(self, archive: block_base):
        # оставляем незапакованное начало
        self.res = bytearray(archive._raw[:OFFSET_PACKED_DATA])

        # забираем данные block_basegeo для распаковки
        self.head = archive.head
        self.map = archive.map

        # на сколько сдвинуть единицу координат в карте влево, чтобы получить порядок значений COORD
        self.shift_scale = archive.shift_scale

        # таблица содержания
        self.li_cat = archive.li_cat  # категории
        self.li_shp = archive.li_shp     # полигоны
        self.li_lin = archive.li_lin      # полилинии
        self.li_vrtx = archive.li_vrtx     # x, y точек
        self.li_poi = archive.li_poi          # хз, что это, но это не POI
        self.li_tstr = archive.li_tstr        # наименования на разных языках

        # Максимальная длинна указателя в битах (по размеру распакованного блока, если на 1 меньше - word wrap align)
        # self._const_segsize * self.unarc_segcn Максимально возможное значение адреса; 2 -> 0x800*2-1=0xfff
        max_bits_in_ptr = len("{:b}".format(archive.head.sizeofblock - 1))  # noqa bin(0xfff)="0b111111111111", w|o '0b' len=12
        if max_bits_in_ptr > 16:
            raise ValueError(f"max_ptr_bits > 16: {max_bits_in_ptr}")      # такое вообще хоть бывает???
        self.max_bits_in_ptr = max_bits_in_ptr    # max possible bits in near offset

        # упакованы НОМЕРА вертексов, а не offs на них
        self.max_bits_in_vrtxnum = len(f"{(archive.li_vrtx.cnt - 1):b}")

        # константы распаковки
        (
            self.max_bits_id_line_if_0,    # noqa id line, сколько бит читать, если флаг показывает отсутствие - 1-32, 0-this
            self.max_bits_id_shape_if_0,   # noqa для id shape (+line?) - сколько бит читать, если флаг показывает отсутствие - 1-32, 0-this
            self.max_bits_in_vertex_delta, # noqa столько бит в дельте XY (8, 9, a)
            unkn_zero
        ) = archive._raw[OFFSET_PACKED_DATA:OFFSET_PACKED_DATA + 4]

        # запакованное тело
        arc = archive._raw[OFFSET_PACKED_DATA + 4:]
        CUT_ZERO_BYTES_CNT = 8
        # с конца убрать нулевые байты, оставив менее 4х
        while arc[-CUT_ZERO_BYTES_CNT:] == b'\x00' * CUT_ZERO_BYTES_CNT:
            arc = arc[:-int(CUT_ZERO_BYTES_CNT / 2)]

        # в буффер - запакованную часть блока, далее self.unpack полностью распакует
        self.buffer = bitarray(buffer=arc, endian='big').copy()    # copy - else read only memory # noqa

        # -----------------------------------------
        # debug raises - временно для отладки, потом вообще закомментировать эти проверки
        if self.max_bits_id_line_if_0 not in [5, 0xc, 0xd, 0xe, 0xf, 0x10, 0x11, 0x13, 0x14, 0x15]:
            raise ValueError(self.max_bits_id_line_if_0, f"0x{self.max_bits_id_line_if_0:X} .max_bits_id_line_if_0")  # noqa 19/0x13 ?
        if self.max_bits_in_vertex_delta not in [8, 9, 0x0a, 0xb, 0xc]:
            raise ValueError(self.max_bits_in_vertex_delta, f"0x{self.max_bits_in_vertex_delta:X} .max_bits_in_vertex_delta")  # noqa
        if unkn_zero not in [0]:
            raise ValueError(unkn_zero, f"0x{unkn_zero} .unkn_zero")
        pass
        # 0x70F0E03 in bmv vdo
        #     C:/DIY/VDO/db_src/bmw34-2010/DB/DB_0
        # 070f0e 03  BlockType.MAP__05k200: 0x14
        # cat 0034:0002 cnt:2 	next ptr: 0040
        # shp 0040:0007 cnt:7 	next ptr: 00E0
        # lin 0000:0000 cnt:0
        # poi 0000:0000 cnt:0
        # vrt 00E0:0135 cnt:309 	next ptr: 05B4
        # tst 05B4:0007 cnt:7 	next ptr: 05D0
        # strs from 05D0
        # Map_hex: 396D900017FA5000  3AED9000197A5000   00010009
        # 72.410501N 143.426737E  76.940351N 147.956586E
        # Максимальные Х и У: C000 x C000
        # 2
        # Max PTR bites: 11
        #     Max VERTEX bites: 9
        # begin word :: 05 00 0A 00

    def unpack(self) -> bytearray:
        """основная функция, возвращает распакованный _raw"""
        # <<<<<<<<<< 1 GEO_CATEGORY
        if self.li_cat.cnt:     # Для каждой геокатегории
            # +1 - всегда есть завершающий итем, нулевой
            for _ in range(self.li_cat.cnt + 1):      # noqa
                category = self.__unpack_next_category()
                print(category.hex())
                self.res += category
        # 0x70F0E03 in bmv vdo
        # 0800 0040
        # 0100 0090
        # 0000 00cc
        print('----')

        # <<<<<<<<<< 2 GEO_SHAPE
        if self.li_shp.cnt:     # если есть shapes - замкнутые полигоны - распаковываем
            # Для каждого шейпа (полигона) из toc.list_shape:
            for _ in range(self.li_shp.cnt + 1):      # +1 - всегда есть завершающий итем, нулевой
                shape = self.__unpack_next_shape()
                print(shape.hex())
                self.res += shape
        # 0x70F0E03 in bmv vdo
        # 05d0 00e0 4000fe16 38e36d50185e9801 00000000
        # 05e1 0134 400115b9 3b5f766518d56e99 00000000
        # 05ef 026c 400249cb 3814139d18ebac33 00000000
        # 05ef 0384 400249cb 3814139d18ebac33 00000000
        # 05f9 03a8 400cd65c 3f57971718395941 00000000
        # 05f9 03c0 400cd65c 3f57971718395941 00000000
        # 05f9 03d0 400cd65c 3f57971718395941 00000000
        # 0000 05b4 00000000 0000000000000000 00000000

        # <<<<<<<<<< GEO_LINE
        if self.li_lin.cnt:
            # для каждой полилинии
            for _ in range(self.li_lin.cnt + 1):      # +1 - всегда есть завершающий итем, нулевой
                line = self.__unpack_next_line()
                print(line.hex())
                self.res += line
            pass

        # <<<<<<<<<< VERTEX
        # дальше запакованы вертексы, delta-coding
        if self.li_vrtx.cnt:
            # первые2 значения - рассматриваем, как xy начальных точек.
            prev_x = ba2int(self._pop(16))
            prev_y = ba2int(self._pop(16))
            # упаковываем to VRTX
            vrtx = struct_WORD.pack(prev_x) + struct_WORD.pack(prev_y)
            self.res += vrtx
            # a_hex = vrtx.hex()

            # распаковка дельта-кодированных локальных координат
            for num in range(self.li_vrtx.cnt - 1):     # minus 1st xy
                prev_x = self.__unpack_half_vertex(prev_x)      # x
                prev_y = self.__unpack_half_vertex(prev_y)      # y
                # упаковка в vertex
                vrtx = struct_WORD.pack(prev_x) + struct_WORD.pack(prev_y)
                # a_hex = vrtx.hex()
                # print(vrtx.hex())
                self.res += vrtx

        # <<<<<<<<<< ZERO ENDED STRINGS unpack, but add to self.res only after TSTRrs
        """
            В запакованном блоке сначала идут строки. И только потом - запакованые tstr.
            .
            ptr_beg - (len Max_PTR_bits) - начальный адрес строк
            ptr_end - (len Max_PTR_bits) - окончание строк, адрес конца всех строк
            6 сокращений - преамбула.
            собственно запакованный текст
            заканчивается множественными 0-ми
            подробно - см. bitstream.unpack_str
        """
        if self.li_tstr.cnt:
            # нет tstr - нет и строк для распаковки
            unpacked_bin_strings = self.__unpack_strings()
            # debug
            unic = unpacked_bin_strings.replace(b"\x00", b".")
            unic = unic.decode('cp1250')
            print(f"\n{unpacked_bin_strings}\n\n{unic}\n")

        # <<<<<<<<<< POI после вертексов в raw, НО в запакованном виде -
        # if self.toc.li_poi.cnt:
        #     # а пока что не реализовано
        #     # raise ValueError("toc.li_poi: ", self.toc.li_poi, " но POI еще не реализован")
        #     """
        #     WORD like   0006 or 0007 or 0008
        #     WORD like 0A1E 0A1D   10D2   13EC   1673
        #     WORD like 0E1C 0A1C   0D77   0FB2   1FB2
        #         первые 4 бита - 1 или 0?
        #     Сначала переменной длинны заголовок
        #     Потом переменной длинны сами poi (это НЕ poi, но пока не понятно, что это - пусть так)
        #     распаковать я не могу.
        #     НО после запакованных poi идёт 41(?)*'0', поэтому можно вычистить, и raw
        #     заполнить '00 07 01 02 03 04'

        #     """
        #     # поиск окончания запакованных poi
        #     # первый - tos.li_poi.ptr в количестве max ptr bites
        #     marker_POI = f"{self.toc.li_poi.ptr:0{buffer.max_PTR_bits}b}"
        #     empty_zero = buffer.buffer.find(bitarray(marker_POI))  # + len(marker_TSTR)
        #     buffer._pop(empty_zero)   # выкинуть всё
        #     del empty_zero, marker_POI
        #     # заmockать '00 07 01 02 03 04'
        #     for mock in range(self.toc.li_poi.cnt):
        #         a = struct_WORD.pack(7)
        #         b = struct_UINT.pack(mock)
        #         self._raw += a
        #         self._raw += b
        #     del mock, a, b
        #     """
        #     - bmw  bl_addr = 0x05412901
        #     - poi 01F4:0010 cnt:16    next ptr: 02C0
        #     - strs from 0268
        #     - Max PTR bites: 10
        #     - начальный адрес строк 0268 001001101000
        #     """

            # # <<<<<<<<<< запакованные ссылки ptr на POI для lin (?)
            # # если есть линии - то дальше их количество +1 значения
            # #  8:  2h - PTR   ptr_linesign? ptr2first TSTR (CALCULATE == tos.li_tstr.ptr) # noqa
            # """
            # bitarray('
            # 01111100110100 0000
            # 011111001101000000
            # 011111001101000000
            # 011111001101000000
            # 011111001101000000
            # 0111110011010000000111110011010000000111110011010000000111110011010000000111110011010000000111110011010000000111110011010001110111110100000010110111110100110010110111110101100000001011111110011001000101011000001011111110110100010111111110100100101111111110110001011111111111100011000000000011000110000000010001001100000000110010011000000010100100110000000110001001100000001110010011000000100001000110000001001011001100000010100000011000000101100000110000001010000001100000011000000011000000110011100110000001101101001100000011101000011000000111110100110000010000100001100000011001110011000001000111100110000010011001001100000010100000011000001010100110000000011000000000001111101011000111110101110011111011000001111101100100111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101000111110110100011111011010001111101101100111110110110011111011011001111101110000111110111010011111011101001111101111000111110111100011111011111001111110000000111111000010011111100010001111110001100111111001000011111100101001111110011000111111001100011111100110001111110011100111111010000011111101001001111110101000111111010110011111101100001111110110100111111011100011111101111001111111000000111111100010011111110010001111111001100010000000000000000000000000010000000010110001001000000000000000000000000000000000000000000000000000000000000000')
            # """
            # if cnt := self.toc.li_lin.cnt:
            #     # 'bytes' object does not support item assignment
            #     mutable = bytearray(self._raw)
            #     INNER_OFFSET_POI = 8
            #     for num in range(cnt + 1):
            #         ptr = ba2int(buffer._unpack(16, buffer.max_PTR_bits, 0, False))
            #         item_offset = self.toc.li_lin.ptr + num * GEO_LINE.size + INNER_OFFSET_POI
            #         mutable[item_offset:item_offset + 2] = ptr.to_bytes(2, byteorder='big')
            #         print(f"ptr2poi: {ptr:02X}")
            #         # если есть POI, то еще 4 бита неясного назначения - 0000,
            #         if self.toc.li_poi.cnt:
            #             buffer._pop(4)      # strange = buffer._pop(4)
            #             pass
            #     self._raw = bytes(mutable)
            #     del INNER_OFFSET_POI, mutable, ptr, item_offset, num

            # <<<<<<<<<< TSTRs  - # далее в архиве запакованы собственно TSTR
            """
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
        # далее в архиве запакованы собственно TSTR
        short_ptr = b'\x00\x00'
        byte_lang = b'\x00'
        byte_type = b'\x00'

        for _ in range(self.li_tstr.cnt):
            # load or reuse ptr
            if ba2int(self._pop(1)):
                # read ptr
                short_ptr = self._unpack_short(self.max_bits_in_ptr)
            # else:       # use prev value tstr_ptr
            # language
            if ba2int(self._pop(1)):
                # read lang
                byte_lang = self._unpack_byte(8)
            # else:   # use prev language
            # type
            if ba2int(self._pop(1)):
                # read type
                byte_type = self._unpack_byte(5)
            # else:   # use prev type
                
            # "собираем" word + byte + byte: ptr + lang + type
            tstr = short_ptr + byte_lang + byte_type
            # a_hex = tstr.hex()
            self.res += tstr

        # И вот теперь пришло время для ТЕКСТОВ texts
        self.res += unpacked_bin_strings

        # bitarray('
        # 101101101010110111001011011110101110000010111000101011100100101110011010111010000000000000000000000000000000000000')

        # если осталось что- либо нераспакованное - его в tail
        self.tail = self.buffer

        # чтобы после распаковки нормально работал блок - добиваем размер нулями
        self.res += b'\x00' * (self.head.sizeofblock - len(self.res))

        return self.res

    # ------------ ФУНКЦИИ РАСПАКОВКИ ОБЪЕКТОВ -----------
    def __unpack_next_category(self) -> bytes:
        """
        BYTE  en_GEO_CATEGORY <--- 7 bits
        BYTE  0poligon_1poliline en_DRAW_TYPE <--- 1 bit
        WORD  ptr_to_category PTR <--- max_PTR_bits-1 bits
        """
        # <<<<<<<<<< GEO_CATEGORY
        res = b''
        # /0/ en_GEO_CATEGORY
        cat = self._unpack_byte(BITS_IN_CATEGORY_TYPE)    # 7 bit на

        # /1/ 0poligon_1poliline
        cat += self._unpack_byte(1)    # 1 бит на полигон0/полилиния1

        # /2/ ptr_to_category
        # left shift 1 - т.к. last = 0 always in this ptr
        # max_bits_in_ptr - 1 максимальное к-во бит для near ссылки на word
        cat += self._unpack_short(self.max_bits_in_ptr - 1, 1)
        res += cat
        # h = cat.hex()  # DEBUG
        return res

    def __unpack_next_shape(self) -> bytes:
        """
        WORD - ptr2string <--- word, ptr 2 zero-ended string
        WORD   ptr2firstVertex  <--- запакованы не offs, а номера вертексов, vertnum, надо расчитывать ptr - offset
        DWORD  id <----- read bit, if 1 - read next32bits is id, if not - so, not
        COORD - qword <--- coord 64bits
        ZeroWord align <--- no in arc
        WORD ptr_to_table_to_strings, unarc by calculate CURR_PTR_PTSTR +4 - next ptstr
        == # в хвостовом vertex = ptrStrTable, последний pstrt = pstrt + 4*pstr.cnt
        """
        # <<<<<<<<<< GEO_SHAPE
        # /0/ WORD - ptr2string <--- word, ptr to zero-ended string
        ptr2string = self._unpack_short(self.max_bits_in_ptr)

        # /1/ word, ptr 2 first vertex
        # запакованы не offs, а номера вертексов vertnum, надо в 4 раза меньше бит,
        # чтобы сохранить т.к. ptr vrtx кратен 4 -> self.max_PTR_bits - 2 (по факту нет, но порядок да)
        # num_vrtx = self._pop(self.max_bits_in_vrtxnum)
        num_vrtx = ba2int(self._pop(self.max_bits_in_vrtxnum))   # номер 0-го vrtx для распаковываемого объекта
        # offset = from li_vrtx.ptr + vrtx_num * size
        vrtx_offset = self.li_vrtx.ptr + VERTEX.size * num_vrtx
        # однако надо 2 bytes, а не int
        ptr2firstVertex = struct_WORD.pack(vrtx_offset)

        # /2/  dword, id
        #id - если следующий бит = 1, ЕСТЬ 32бит ID, иначе bits_to_unpack_then_zero
        qty = BITS_IN_UINT if self._pop(1)[0] else self.max_bits_id_shape_if_0
        # int_id = ba2int(self._pop(qty))
        # id = struct_4BYTES.pack(int_id)
        id = self._unpack_uint(qty)

        # /3/  dword dword - coord, here '08 c0 00 a0 40 01 8d 00'
        # координаты - они есть, всегда. Просто лежат без упаковки  '0010010001110101000001011000010011100010'
        # lon = self._unpack_uint(BITS_IN_UINT)        # _lon
        # lat = self._unpack_uint(BITS_IN_UINT)        # _lat
        coord = self._unpack_uint(BITS_IN_UINT) + self._unpack_uint(BITS_IN_UINT)

        # >>>>>>>>>> - а ВСЁ, более ничего запакованного нет.
        # /5/ word - ptr2table
        # можно рассчитать - если ПРЕДЫДУЩИЙ элемент был с id == 0, то инкремента нет
        # WORD ptr_to_table_to_strings, unarc by calculate CURR_PTR_PTSTR +4 - next ptstr
        # if this_will_increment:
        #     self.offset_tstr += TSTR.size
        # self.result += struct_WORD.pack(self.offset_tstr)

        # >>>>>>>>>> - а ВСЁ, более ничего запакованного нет. Поэтому остальное добиваем нулями
        # /4/  ZeroWord align
        # /5/ WORD ptr_to_table_to_strings

        zeroTail = b'\x00' * 4    # 2 * word bytes

        res = ptr2string + ptr2firstVertex + id + coord + zeroTail
        return res

    def __unpack_next_line(self) -> bytes:
        res = b''

        return res

    def __unpack_half_vertex(self, prev: int) -> int:
        """
        Декодирует одну из координат (short x или y) vertex
        В зависимости от первых 2-х префиксных бит (self.max_bits_in_vertex_delta == 9):
         - '11' - read 16 bit, считать все 16 бит, как значение.
         - '10' - read 9 бит, вычесть значение из предыдущего
         - '01', '00' - read 8 bit, or с 1 или 0 - и сложить с предыдущим
        Args:
            prev: short int - Предыдущее значение.
        Returns:
            int: short значение координаты x или y
        """
        prefix = self._pop(2)
        bits_to_read = self.max_bits_in_vertex_delta
        
        if prefix == CONST_BA_11:                   # CONST_BA_11 = bitarray([1, 1])
            # load full short
            half = ba2int(self._pop(BITS_IN_WORD))
            return half
        
        elif prefix == CONST_BA_10:                 # CONST_BA_10 = bitarray([1, 0])
            # read max_bits_in_vertex_delta бит, вычесть значение из предыдущего
            val = -ba2int(self._pop(bits_to_read))

        elif prefix == CONST_BA_01:                 # CONST_BA_01 = bitarray([0, 1])
            # read 8 бит, и +добавить ~9й~ старший
            val = ba2int(self._pop(bits_to_read - 1))
            val = (1 << bits_to_read) | val         # 0b100000000 | val

        else:
            # CONST_BA_00
            val = ba2int(self._pop(bits_to_read - 1))

        # 0 - сложить, 10-вычесть, 11 - уже вернули
        half = prev + val
        return half

        # 0x70F0E03 in bmv vdo
        #     C:/DIY/VDO/db_src/bmw34-2010/DB/DB_0
        # 070f0e 03  BlockType.MAP__05k200: 0x14
        # cat 0034:0002 cnt:2 	next ptr: 0040
        # shp 0040:0007 cnt:7 	next ptr: 00E0
        # lin 0000:0000 cnt:0
        # poi 0000:0000 cnt:0
        # vrt 00E0:0135 cnt:309 	next ptr: 05B4
        # tst 05B4:0007 cnt:7 	next ptr: 05D0
        # strs from 05D0
        # Map_hex: 396D900017FA5000  3AED9000197A5000   00010009
        # 72.410501N 143.426737E  76.940351N 147.956586E
        # Максимальные Х и У: C000 x C000
        # 2
        # Max PTR bites: 11
        #     Max VERTEX bites: 9
        # begin word :: 05 00 0A 00

    def __unpack_strings(self) -> bytes:
        """
        Оригинальная реализация Хаффмана.
        :LOOKUP_CHAR_BYTES: Базовая константная таблица соответствия на 14 char,
        :preambula: адаптивная по блокам таблица часто встречающихся до 3-х char - хранит 6 сочетаний
        :ascii: Если символ ни там, ни там - win1250, причем, если ascii до ' ' - то = ascii + 0xe0
        Функция распаковывает ВСЕ строки за один вызов
        Returns:
            bin_str: бинарное представление строковой части zero-ended строк
        """
        # ^^^ первыми запакованы 2 ptr - начало и окончание блока строк
        ptr_start = ba2int(self._pop(self.max_bits_in_ptr))
        ptr_end = ba2int(self._pop(self.max_bits_in_ptr))
        strings_length = ptr_end - ptr_start

        #  ^^^  далее - подготовка преамбулы для хаффмановского декодирования
        # преамбула - словарь из 6 элементов с ключами от 110100001 до 110100110.
        # Причём "пустые" элементы = b'A'

        # но 11 это преамбула, поэтому от 0100001 до 0100110
        preambula = {}
        for k in range(0b0100001, 0b0100111):
            # первые 3 бита = 000
            if beg_marker := ba2int(self._pop(3)):             # val.to01() != '000':
                raise ValueError(f"WTF? В начале строк преамбулы ожидалось 000, а не '{beg_marker:3b}'")    # noqa

            # затем 2 бита - количество ascii chars для чтения
            if not (n := ba2int(self._pop(2))):         #  11 и 01 точно да, а остальные варианты - хз.  # noqa
                # Вроде 00 не может быть - иначе зачем 6 шт где не кодируется ничего?
                raise ValueError(f"WTF? В количестве ch преамбулы не ожидалось 00, а тут '{n:2b}'")    # noqa
            #теперь загрузить n chars
            val = b''
            for _ in range(n):
                # и грузятся ascii коды по 7 бит
                ascii = ba2int(self._pop(BITS_IN_ASCII))
                # bch = ascii.to_bytes(1, byteorder='big')
                # val += bch
                val += bytes((ascii,))          # короче и быстрее
            preambula[f"{k:07b}"] = val

        #   ^^^  и вот только теперь пошли буквы, закодированные ....эммм.
        # .. как бы хафманом, но с нюансами
        bin_str = b''
        for _ in range(strings_length):
            prefix = self._pop(2)
            if prefix == CONST_BA_11:           # prefix.to01() == '11':
                ba = self._pop(BITS_IN_ASCII)
                if ba.to01() in preambula:
                    # о, сокращённенькое из преамбулы
                    pre_chars = preambula[ba.to01()]
                    # но если из преамбулы возвращается А
                    if pre_chars == b'A':
                        bin_str += bytes((ba2int(ba),))      # просто добавить байт
                    else:
                        bin_str += pre_chars
                elif ba2int(ba) < 32:       # похоже загрузить ascii до ' '
                    """
                    ISO 8859-2 xor win1250?
                    """
                    # а это 1250
                    code = 0xe0 + ba2int(ba)  # угу, эмпирическое волшебное число 0xE0
                    # ascii = code.to_bytes(1, byteorder='big')
                    bin_str += bytes((code,))   # bin_str += code.to_bytes(1, byteorder='big')
                else:
                    # или ascii код буквы
                    # ascii = ba2int(ba)
                    bin_str += bytes((ba2int(ba),))   # bin_str += ba2int(ba).to_bytes(1, byteorder='big')
                continue        # всё, данные итерации загружены
            elif prefix == CONST_BA_00:         # prefix.to01() == '00':
                prefix += self._pop(1)
            elif prefix == CONST_BA_01:         # prefix.to01() == '01':
                prefix += self._pop(2)
            else:                               # elif prefix.to01() == '10':
                prefix += self._pop(3)
            # вытаскиваем, что получилось, из дерева и добавляем к результату
            bin_str += LOOKUP_CHAR_BYTES[prefix.to01()]
        # всё, упакованные буквы окончились

        # подрезать хвосты - итераций было по числу символов,
        # но по длинне могло подрасти из-за использования преамбулы
        bin_str = bin_str[:strings_length]

        # <<<<<<<<< Убрать незначащие нули в буфере, в архиве они необходимы для обеспечения
        # пространства использования преамбульных сокращений,
        try:
            first_one_idx = self.buffer.index(1)        # Находим индекс первой единицы
            self.buffer = self.buffer[first_one_idx:]   # Отрезаем всё, что было до неё
        except ValueError:
            # Исключение сработает, если в массиве вообще больше нет единиц
            raise "Прикольно, вот не уверен, что такое вообще может быть"

        return bin_str

    # ----------------------------
    # ------------ ФУНКЦИИ РАСПАКОВКИ ПРИМИТИВОВ - byte, short, uint -----------

    def _pop(self, qty_bits: int) -> bitarray:
        '''POP qty_bits from begin (left) buffer qty bites'''
        val = self.buffer[:qty_bits]   # взять первые qty_bits бит
        self.buffer = self.buffer[qty_bits:]      # удалить qty_bits из начала
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
            raise ValueError(bit_compressed, f"Значение больше {BITS_IN_BYTE}, _unpack_byte")
        
        res: bitarray = self._pop(bit_compressed)
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
        if bit_compressed > BITS_IN_WORD:
            raise ValueError(bit_compressed, f"Значение больше {BITS_IN_WORD}, _unpack_short")
        
        res: bitarray = self._pop(bit_compressed)
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
        
        res: bitarray = self._pop(bit_compressed)
        # добавить справа нолей на к-во сдвига
        res.extend(bitarray([0]) * left_shift)  # самый быстрый путь добавить справа
        # оставить только 32 правых бит
        res = res[-BITS_IN_UINT:]
        # выровнять до word
        from_left = BITS_IN_UINT - len(res)
        res = (bitarray([0]) * from_left) + res
        # br = res.tobytes()
        return res.tobytes()

    # ------------ под удаление, похоже.
    def _unpack(self, bit_goal: int, bit_compressed: int, left_shift: int=0, bool_save: bool=True) -> bitarray:  # noqa:
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

    def _touch(self, qty_bits: int, start: int = 0) -> bitarray:
        ''' Return qty bits from start W/o deleting'''
        val = self.buffer[start:start + qty_bits].copy()
        return val


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
        if word_a not in [5, 0xc, 0xd, 0xe, 0xf, 0x10, 0x11, 0x13, 0x14, 0x15]:
            raise ValueError(word_a, f"0x{word_a:X} .word_a")  # 19/0x13 ?
        if word_c not in [8, 9, 0x0a]:
            raise ValueError(word_c, f"0x{word_c:X} .word_c")
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
        self.max_bits_num_vrtx = len(f"{(parent.li_vrtx.cnt - 1):b}")
        self.max_PTR_bits = parent.max_PTR_bits()    # max possible bits in near offset
        self.start_vrtx_ptr = parent.li_vrtx.ptr     # start_vrtx_ptr стартовый offset vertexes
        self.offset_tstr = parent.li_tstr.ptr        # tstr стартует с этого смещения, каждый объект - + 1  # noqa

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
        '''POP qty_bits from begin (left) buffer qty bites'''
        val = self.buffer[:qty_bits]   # взять первые qty_bits бит
        del self.buffer[:qty_bits]      # удалить qty_bits из начала
        return val
    
    def _touch(self, qty_bits: int, start: int = 0) -> bitarray:
        ''' Return qty bits from start W/o deleting'''
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
        self.result += struct_WORD.pack(self.parent.li_tstr.ptr)

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
