"""
bitstream - class wrapper for bitarray
"""

from __future__ import annotations

from QGIS_VDO import bitarray, ba2int

from QGIS_VDO.vdo.geotypes import (VERTEX,
                                   TSTR)

from QGIS_VDO.vdo.consts import (struct_WORD,
                                 struct_4BYTES,
                                 BITS_IN_ASCII,
                                 BITS_IN_BYTE,
                                 BITS_IN_WORD,
                                 BITS_IN_UINT,
                                 LOOKUP_CHAR_BYTES)


BITS_IN_CATEGORY_TYPE = BITS_IN_BYTE - 1   # packed cat type len = 7 bit


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
