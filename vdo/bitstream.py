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
    GEO_SHAPE,
    GEO_LINE,
    VERTEX,
    # TSTR,
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

class bitstream():
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

        # распаковывать ли lin{5} - характеристика дороги, предположительно макс скорость
        self.flag_unpack_lin5 = False

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
        if self.max_bits_id_line_if_0 not in [5, 0xa, 0xb, 0xc, 0xd, 0xe, 0xf, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15]:
            raise ValueError(self.max_bits_id_line_if_0, f"0x{self.max_bits_id_line_if_0:X} .max_bits_id_line_if_0")  # noqa 19/0x13 ?
        if self.max_bits_in_vertex_delta not in [8, 9, 0x0a, 0xb, 0xc]:
            raise ValueError(self.max_bits_in_vertex_delta, f"0x{self.max_bits_in_vertex_delta:X} .max_bits_in_vertex_delta")  # noqa
        if unkn_zero not in [0]:
            raise ValueError(unkn_zero, f"0x{unkn_zero} .unkn_zero")
        pass

    def unpack(self) -> bytearray:      # noqa 'bit_stream.unpack' is too complex (23)Flake8(C901)
        """основная функция, возвращает распакованный _raw"""
        # <<<<<<<<<< 1 GEO_CATEGORY
        if self.li_cat.cnt:     # Для каждой геокатегории
            # +1 - всегда есть завершающий итем, нулевой
            for _ in range(self.li_cat.cnt + 1):      # noqa
                category = self.__unpack_next_category()
                print(category.hex())
                self.res += category
                # category[0] - en_GEO_CATEGORY
                if 0x67 < category[0] < 0x6f:
                    # если хоть раз встретилась дорога, взводим флаг
                    self.flag_unpack_lin5 = True
  
        # <<<<<<<<<< 2 GEO_SHAPE
        if self.li_shp.cnt:     # если есть shapes - замкнутые полигоны - распаковываем
            # Для каждого шейпа (полигона) из toc.list_shape:
            for _ in range(self.li_shp.cnt + 1):      # +1 - всегда есть завершающий итем, нулевой
                shape = self.__unpack_next_shape()
                print(shape.hex())
                self.res += shape

        # <<<<<<<<<< 3 GEO_LINE
        if self.li_lin.cnt:
            # для каждой полилинии
            for _ in range(self.li_lin.cnt + 1):      # +1 - всегда есть завершающий итем, нулевой
                line = self.__unpack_next_line()
                # line = p_str_name + ptr2firstObjVertex + id + ptr_linesign + ptr2poi + ptr2tstr + shrtEnd
                # но запакованы только до id включительно, остальные = 0
                # a_hex = line.hex()
                # print(line.hex())
                self.res += line
            pass

        # <<<<<<<<<< 4 VERTEX
        # дальше запакованы вертексы, delta-coding
        if self.li_vrtx.cnt:
            # первые2 значения - рассматриваем, как xy начальных точек.
            prev_x = ba2int(self.pop(16))
            prev_y = ba2int(self.pop(16))
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

        # <<<<<<<<<< 5 ZERO ENDED STRINGS unpack, but add to self.res only after TSTRrs
        """
            В запакованном блоке сначала уложены строки. И только потом - запакованые tstr.
            .
            ptr_beg - (len Max_PTR_bits) - начальный адрес строк
            ptr_end - (len Max_PTR_bits) - окончание строк, адрес конца всех строк
            6 сокращений - преамбула.
            собственно запакованный текст
            заканчивается множественными 0-ми
            подробно - см. bitstream.unpack_all_str
        """
        if self.li_tstr.cnt:
            # нет tstr - нет и строк для распаковки
            unpacked_bin_strings = self.__unpack_all_strings()
            # debug
            unic = unpacked_bin_strings.replace(b"\x00", b".")
            unic = unic.decode('cp1250')
            print(f"\n{unpacked_bin_strings}\n\n{unic}\n")

            # <<<<<<<<< Убрать незначащие нули в буфере, в архиве они необходимы для обеспечения
            # TODO: причем остается и только если только shp... self.cuted_after_str
            #  WARN! после DB 07156A01 001E 01 02 [1E:MAP__11k_11] остается
            #  0111000010010000001000... - atlantic ocean
            #  WARN! после DB 0715AC01 001E 01 02 [1E:MAP__11k_11] остается
            #  0111000010010000001... 0x38481 - artic ocean
            #  0715AB01 001E 01 02 [1E:MAP__11k_11] - 0111000010010000001000000000
            # 0111000010110000001 01110000101000000001 01110000101100000001(sc5 antalia)
            ten_zero_idx = self.buffer.find(bitarray('0000000000000000'))     # Находим индекс единицы
            self.tail_cutted_after_str = None
            if ten_zero_idx:
                self.tail_cutted_after_str = self.buffer[:ten_zero_idx]
                self.buffer = self.buffer[ten_zero_idx:]   # Отрезаем всё, что было до
            
            # Отрезаем все 0, что было для пространства использования преамбульных сокращений,
            try:
                first_one_idx = self.buffer.index(1)        # Находим индекс первой единицы
                self.buffer = self.buffer[first_one_idx:]   # Отрезаем всё, что было до неё
            except ValueError:
                # Исключение сработает, если в массиве вообще больше нет единиц
                raise "Прикольно, такое вообще не может быть"
        
        # <<<<<<<<<< LIN{45} ссылки на TSTRs из каждого lin (ptr_linesign , ptr2poi)
        if self.li_lin.cnt:
            # line = p_str_name + ptr2firstObjVertex + id + ptr_linesign + ptr2poi + ptr2tstr + shrtEnd
            # см lzw: 0x070A240f(italia), 0x70AC609(azov) in bmw. type = 14h, scale=5
            # ptr для каждого lin, включая последний нулевой, "уложены" подряд
            # :: ptr_linesign <--  self.max_bits_in_ptr - 1
            # :: prt2poi <-- 5 (пять ???) бит
            # для проверки
            #  - ptr_linesign указывают на TSTRS с типом 0 - полигон (похоже принадлежность?)
            #  - sc5, версия - все = li_tstr.ptr

            if self.head.bltype.value == 0x14:     # пока только для sc5 14h типа 5 бит
                bit_in_ptr2poi = 4  # 5
                pass
            else:
                raise NotImplementedError(f"тип блока {self.head.bltype}")

            # подбор значения bit_in_ptr2poi
            watchdog = 1
            if watchdog < 0xFFFF and self.flag_unpack_lin5:
                # нет дорог - нет характеристик
                start_tstr = self.touch(self.max_bits_in_ptr - 1)
                ptr = self.max_bits_in_ptr
                candidate = self.touch(self.max_bits_in_ptr - 1, ptr)
                cand_f = self.touch(1, ptr - 1)
                # ищем, через сколько всплывёт опять тот же start_tstr
                while candidate == start_tstr:
                    ptr += self.max_bits_in_ptr
                    candidate = self.touch(self.max_bits_in_ptr - 1, ptr)
                    cand_f = self.touch(1, ptr - 1)
                # или нашелся, или нет, candidate != start_tstr
                if candidate != start_tstr:
                    # есть ли флаговый бит, который предварял?
                    if use_flag := cand_f == bitarray([1]):
                        bit_in_ptr2poi = BITS_IN_WORD   # версия, реально хз
                    else:
                        # подсчитать дельту до следующего
                        for shift in range(1, BITS_IN_WORD + 1):
                            candidate = self.touch(self.max_bits_in_ptr - 1, ptr + shift)
                            if candidate == start_tstr:
                                # чу, опять он
                                break
                        pass   # вот тут shift == bit_in_ptr2poi
                        bit_in_ptr2poi = shift + 1   # +1 чтобы потом флаговый pop не
                # а если все дороги - без характеристик?
                watchdog += 1

            # DEBUG
            if self.head.bltype.value == 0x14 and bit_in_ptr2poi not in [4, 5, 16]:     # пока только для sc5 14h типа
                raise ValueError("bit_in_ptr2poi not in [4, 5, 16]")
            
            # 8 - offset ptr_linesign in GEO_LINE
            INNER_OFFSET_POI = 8
            offset = self.li_lin.ptr + INNER_OFFSET_POI
            for _ in range(self.li_lin.cnt + 1):       # +1 0-tail
                # ptr_linesign = self._unpack_short(self.max_bits_in_ptr)   # word aligned
                ptr_linesign = self._unpack_short(self.max_bits_in_ptr - 1, 1)   # word aligned
                # записываем в уже распакованные линии
                self.res[offset:offset + 2] = ptr_linesign
                # ::: проблема ptr2poi - два варианта упаковки:
                # - ptr_linesign(max_bits_in_ptr - 1) и бит флаг- ptr2poi(BITS_IN_WORD) (дороги и реки)
                # - вообще нет такого - грузия
                # - ptr_linesign(max_bits_in_ptr) без флага и ptr2poi(bit_in_ptr2poi=4), (дороги, норги)
                # костыли - пробовать читать следующий, если != self.li_tstr.ptr,
                # то в подпрограмму установки сколько читать

                if self.flag_unpack_lin5:
                    # следующий бит - флаг, считывать 4 бита, или 16
                    if use_flag and self.pop(1) == bitarray([1]):
                        ptr2poi = self._unpack_short(BITS_IN_WORD)
                        self.res[offset + 2:offset + 4] = ptr2poi
                    elif not use_flag:
                        ptr2poi = self._unpack_short(bit_in_ptr2poi)  # bit_in_ptr2poi = 4
                        self.res[offset + 2:offset + 4] = ptr2poi
                    else:
                        # вообще тут нет ptr2poi
                        pass
                else:
                    # а вот тут 1 бит всё равно надо снять
                    self.pop(1)

                # # на примере центральной испании 0x705C816 sc5 (валятся норги и грузия)
                # if self.pop(1) == bitarray([1]):
                #     ptr2poi = self._unpack_short(BITS_IN_WORD)
                #     # записываем в уже распакованные линии
                #     self.res[offset + 2:offset + 4] = ptr2poi

                # # на примере норгов 0x709DF0A и грузии, 0x70AE205 (валится испания)
                # if self.flag_unpack_lin5:
                #     ptr2poi = self._unpack_short(bit_in_ptr2poi)  # bit_in_ptr2poi = 5
                #     # записываем в уже распакованные линии
                #     self.res[offset + 2:offset + 4] = ptr2poi

                offset += GEO_LINE.size

        # <<<<<<<<<< TSTRs  - # далее в архиве запакованы собственно TSTR
        if self.li_tstr.cnt:
            self.res += self.__unpack_all_tstrs()

        # После tstrs теперь пришло время для добавления в результат ранее распакованых ТЕКСТОВ texts
        self.res += unpacked_bin_strings

        # <<<<<<<<<<<<<<<<<<<<  основное тело сформировани.
        # Далее запакованы значения, которыми заполняются сформированные 00-е поля

        # <<<<<<<<<< ссылки на TSTRs из каждого shp (последний word)
        if self.li_shp.cnt:
            # ptr для каждого shp, включая последний нулевой, просто "упакованы" подряд
            # однако т.к. их значения выровнены по short - то  self.max_bits_in_ptr - 1
            # для проверки
            #  -tstr первого shp (если нет lin) = ptr на начало li_shp.ptr
            #  -tstr последнего нулевого shp (если нет lin) = ptr на начало строк
            offset = self.li_shp.ptr + GEO_SHAPE.size - 2    # последний word
            for _ in range(self.li_shp.cnt + 1):    # включая последний нулевой shp
                tstr_val = self._unpack_short(self.max_bits_in_ptr - 1, 1)   # значения выровнены по short
                # запись в ранее распакованные shp
                self.res[offset:offset + 2] = tstr_val
                offset += GEO_SHAPE.size

        # <<<<<<<<<< ссылки на TSTRs из каждого lin (ptr2tstr)
        if self.li_lin.cnt:
            # line = p_str_name + ptr2firstObjVertex + id + ptr_linesign + ptr2poi + ptr2tstr + shrtEnd
            # нв примере lzw - 0x070A240f in bmw. type = 14h, scale=5
            # ptr для каждого lin, включая последний нулевой, "уложены" подряд, но предваряются 1 (если есть)
            # :: flag 1/0
            # :: ptr2tstr <--  self.max_bits_in_ptr - 1

            # для проверки - ptr_linesign указывают на TSTRS с типом 10 - полилиния
            if self.head.bltype.value == 0x14:     # пока только для 14 типа 5 бит
                bit_in_ptr2poi = 55555555      # TODO - вообще убрать после проверки на др типах
            else:
                raise NotImplementedError(f"тип блока {self.head.bltype}")
            
            # 8 - offset ptr_linesign in GEO_LINE
            INNER_OFFSET_POI = GEO_LINE.size - 4
            offset = self.li_lin.ptr + INNER_OFFSET_POI
            for _ in range(self.li_lin.cnt + 1):       # +1 0-tail

                ptr2tstr = self._unpack_short(self.max_bits_in_ptr - 1, 1)   # word aligned
                self.res[offset:offset + 2] = ptr2tstr
                offset += GEO_LINE.size
        
        # <<<<<<<<<<<<<<<<<<<< если осталось что- либо нераспакованное - его в tail
        if self.buffer and ba2int(self.buffer) > 0:
            self.tail = self.buffer
            # 14h, lin.cnt = 3; 00100000000101000000010000000000000000000000000000000000000000000
            # 14h, lin_cnt =25; 0010000000010100000000000000000000000000000100000000000000000000000000000000000000000000
            # noqa 14h, lin_cnt =47; 0100111111001100011111100111001111110100000111111010010011111101010000100000000 1011000100000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000
            # noqa 14h, lin_cnt =23; 0010000000000000000010000000010110001000000000000000000001000000000000000000000000000000000000000000000000000
            # 14h, lin_cnt = 3; 00100000000000000000000000000000000000000000000000000000000000000
        else:
            self.tail = None

        # чтобы после распаковки нормально работал блок - добиваем размер нулями 10110001
        self.res += b'\x00' * (self.head.sizeofblock - len(self.res))

        return self.res

    # ------------ ФУНКЦИИ РАСПАКОВКИ СУЩНОСТЕЙ  -----------
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
        WORD   ptr2firstObjVertex  <--- запакованы не offs, а номера вертексов, vertnum,
                    надо расчитывать ptr - offset
        DWORD  id <----- read bit, if 1 - read next32bits is id, if not - so, not
        COORD - qword <--- coord 64bits
        ZeroWord align <--- no in arc
        WORD ptr_to_table_to_strings, unarc by calculate CURR_PTR_PTSTR +4 - next ptstr
        == # в хвостовом vertex = ptrStrTable, последний pstrt = pstrt + 4*pstr.cnt
        """
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

        # >>>>>>>>>> - а ВСЁ, более ничего запакованного нет.
        # /5/ word - ptr2table
        # можно рассчитать - если ПРЕДЫДУЩИЙ элемент был с id == 0, то инкремента нет
        # WORD ptr_to_table_to_strings, unarc by calculate CURR_PTR_PTSTR +4 - next ptstr
        # if this_will_increment:
        #     self.offset_tstr += TSTR.size
        # self.result += struct_WORD.pack(self.offset_tstr)

        # >>>>>>>>>> - а ВСЁ, более ничего запакованного нет. Поэтому остальное добиваем нулями
        # /4/ WORD ZeroWord align
        # /5/ WORD ptr_to_table_to_strings (указатель на ПЕРВЫЙ TSTR, запаковано в другом месте)
        zeroTail = b'\x00' * 4    # 2 * word bytes -> размер GEO_SHAPE полный

        res = ptr2string + ptr2firstObjVertex + id + coord + zeroTail
        return res

    def __unpack_next_line(self) -> bytes:
        """
        Geo segment of line - poligon
        0:  WORD - PTR         p_str_name - ptr на 0-ended str; =max_ptr_bit_len
        2:  WORD - PTR         ptr_vrtx - vrtx num; =max_vrtx_num_bits_len
        4:  DWORD         id; 1 =32; 0 =max_bits_id_line_if_0 (word_a)
        8:  WORD - PTR   ptr_linesign? ptr2первый TSTR? наименование области?
        10: WORD  -  ptr2poi? подозрение, *10=скорость
        12: WORD - PTR ptr2tstr на TSTR на p_str_name, наименование линии (мультиязычность?)
                (Самый первый - 34B4 из последнего shp
        14: WORD -# (CALCULATE == 2 байта страны ,
            при распаковке - константу, пусть FFFF
        """
        # /0/ p_str_name
        p_str_name = self._unpack_short(self.max_bits_in_ptr)

        # /1/ WORD, ptr 2 first vertex (упакованы НОМЕРА vrtx)
        ptr2firstObjVertex = self._unpack_vrtx_ptr()

        # /2/ > DWORD id ?? (полный ли DWORD? если нет, то сколько бит грузить?)
        flag = self.pop(1)
        if flag == bitarray([1]):
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
        # TODO: При "распаковке" - подставлять страну ?
        shrtEnd = b'\x00' * 2

        line = p_str_name + ptr2firstObjVertex + id + ptr_linesign + ptr2poi + ptr2tstr + shrtEnd
        # len(line) == GEO_LINE.size
        return line

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
        prefix = self.pop(2)
        bits_to_read = self.max_bits_in_vertex_delta
        
        if prefix == CONST_BA_11:                   # CONST_BA_11 = bitarray([1, 1])
            # load full short
            half = ba2int(self.pop(BITS_IN_WORD))
            return half
        
        elif prefix == CONST_BA_10:                 # CONST_BA_10 = bitarray([1, 0])
            # read max_bits_in_vertex_delta бит, вычесть значение из предыдущего
            val = -ba2int(self.pop(bits_to_read))

        elif prefix == CONST_BA_01:                 # CONST_BA_01 = bitarray([0, 1])
            # read 8 бит, и +добавить ~9й~ старший
            val = ba2int(self.pop(bits_to_read - 1))
            val = (1 << bits_to_read) | val         # 0b100000000 | val

        else:
            # CONST_BA_00
            val = ba2int(self.pop(bits_to_read - 1))

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

    def __unpack_all_strings(self) -> bytes:
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
        ptr_start = ba2int(self.pop(self.max_bits_in_ptr))
        ptr_end = ba2int(self.pop(self.max_bits_in_ptr))
        strings_length = ptr_end - ptr_start

        #  ^^^  далее - подготовка преамбулы для хаффмановского декодирования
        # преамбула - словарь из 6 элементов с ключами от 110100001 до 110100110.
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
                ascii = ba2int(self.pop(BITS_IN_ASCII))
                # bch = ascii.to_bytes(1, byteorder='big')
                # val += bch
                val += bytes((ascii,))          # короче и быстрее
            preambula[f"{k:07b}"] = val

        #   ^^^  и вот только теперь пошли буквы, закодированные ....эммм.
        # .. как бы хафманом, но с нюансами
        bin_str = b''
        for _ in range(strings_length):
            prefix = self.pop(2)
            if prefix == CONST_BA_11:           # prefix.to01() == '11':
                ba = self.pop(BITS_IN_ASCII)
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
                prefix += self.pop(1)
            elif prefix == CONST_BA_01:         # prefix.to01() == '01':
                prefix += self.pop(2)
            else:                               # elif prefix.to01() == '10':
                prefix += self.pop(3)
            # вытаскиваем, что получилось, из дерева и добавляем к результату
            bin_str += LOOKUP_CHAR_BYTES[prefix.to01()]
        # всё, упакованные буквы окончились

        # подрезать хвосты - итераций было по числу символов,
        # но по длинне могло подрасти из-за использования преамбулы
        bin_str = bin_str[:strings_length]

        return bin_str

    def __unpack_all_tstrs(self) -> bytes:
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
            
        all_tstrs = b''
        short_ptr = b'\x00\x00'
        byte_lang = b'\x00'
        byte_type = b'\x00'
        
        for _ in range(self.li_tstr.cnt):
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
            if ba2int(self.pop(1)):
                # read type
                byte_type = self._unpack_byte(5)
            # else:   # use prev type
                
            # "собираем" word + byte + byte: ptr + lang + type
            tstr = short_ptr + byte_lang + byte_type
            # a_hex = tstr.hex()
            all_tstrs += tstr

        return all_tstrs
    
    # ----------------------------
    # ------------ ФУНКЦИИ РАСПАКОВКИ ПРИМИТИВОВ - byte, short, uint -----------

    def pop(self, qty_bits: int) -> bitarray:
        '''POP qty_bits from begin (left) buffer qty bites'''
        val = self.buffer[:qty_bits]   # взять первые qty_bits бит
        self.buffer = self.buffer[qty_bits:]      # удалить qty_bits из начала
        return val

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
            raise ValueError(bit_compressed, f"Значение больше {BITS_IN_BYTE}, _unpack_byte")
        
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
        if bit_compressed > BITS_IN_WORD:
            raise ValueError(bit_compressed, f"Значение больше {BITS_IN_WORD}, _unpack_short")
        
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
        Запакованы не offs, а номера вертексов, vertnum,
        бонус - надо в 4 раза меньше бит, чтобы сохранить
        ptr vrtx - выравнивается по WORD, кратен 4 -> self.max_PTR_bits - 2 (по факту нет, но порядок да)
        """
        num_vrtx = ba2int(self.pop(self.max_bits_in_vrtxnum))   # номер 0-го vrtx для распаковываемого объекта
        # offset = от первого li_vrtx.ptr + num_vrtx * size вертекса
        vrtx_offset = self.li_vrtx.ptr + VERTEX.size * num_vrtx
        # однако надо 2 bytes, а не int
        ptr2firstObjVertex = struct_WORD.pack(vrtx_offset)
        return ptr2firstObjVertex

    # ------------ под удаление, похоже.
    # def _unpack(self, bit_goal: int, bit_compressed: int, left_shift: int=0, bool_save: bool=True) -> bitarray:  # noqa:
    #     """
    #     Args:
    #         bit_goal: int  bits in result
    #         bit_compressed: int how many bits pop from self
    #         left_shift: int=0 - qty left shift result
    #         bool_save: bool save into self.result
    #     Returns:
    #         str: String with hex value, f.e. '00a8'
    #     """
    #     res = self.pop(bit_compressed)  # pop bits from buffer
    #     val = bitarray((bit_goal - (res.nbytes * 8 - res.padbits)) * '0')  # leading zeroes  # noqa
    #     val += res                      # append lead zero with result
    #     val <<= left_shift              # left shift if lsch > 0
    #     # можно не сохранять - если значение надо интерпретировать перед сохранением
    #     if not bool_save:
    #         return val  # но тогда возвращать bitarray
    #     # в последовательность байтов   bres = val.tobytes() - только значащие байты, увы.  # noqa
    #     bres = val.tobytes()
    #     self.result += bres
    #     str_res = ''
    #     for h in bres:
    #         str_res += "{:02x}".format(h)   # str_res - for debug ))))
    #     return str_res   # bres
