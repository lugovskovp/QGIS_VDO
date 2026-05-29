"""
block_basegeo - Базовый тип для - карт   00 16 15 1c 14 1d 1e # noqa: E116
bitstream - class wrapper for bitarray
"""

# flake8: noqa F841  на время отладки отключить предупреждения о неиспользуемых


from bitarray import bitarray   # https://pypi.org/project/bitarray/
# https://github.com/ilanschnell/bitarray/blob/master/doc/buffer.rst
from bitarray.util import ba2int


from vdo.block_base import block_base   
from vdo.datatypes import BLADDR, LIST, BYTESTRUCT
from vdo.enums import en_GEO_CATEGORY, en_DRAW_TYPE
from vdo.geotypes import MAP_AREA, GEO_CATEGORY, GEO_SHAPE, GEO_LINE, VERTEX, TSTR
from vdo.datatypes import UINT_struct, USHORT_struct    # BYTE_struct,


OFFSET_LI_GEOCATEGORY = 0x08    # geodata types (categories)
OFFSET_LI_GEOSHAPE = 0x0c       # гео SHAPES - замкнутые полигоны
OFFSET_LI_GEOLINE = 0x10        # линии
OFFSET_LI_VERTEX = 0x14         # точки word, word
OFFSET_LI_POI = 0x18            # poi`s`
OFFSET_LI_TSTR = 0x1c           # ptrs tstr - индексы строк en_GEO_OBJ

OFFSET_PACKED_DATA = 0x34  # ТИПЫ БЛОКОВ archived type_1_vdo_pack
                            # bmw ee bnl:  00 16 15 1c 14 1d 1e # noqa: E116
                            # в них незапакованы первые 0х34 # noqa: E116

BITS_IN_CATEGORY_TYPE = 7   # packed cat type len = 7 bit
BITS_IN_BYTE = 8
BITS_IN_WORD = 16
BITS_IN_UINT = 32

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
        
    def __init__(self, addr: BLADDR) -> None:
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
            # 83888384 = 5000 9000
            self.unk_beg_arch_dword = UINT_struct.unpack(barray[OFFSET_PACKED_DATA:OFFSET_PACKED_DATA + 4])[0]  # noqa
            # Всё остальное в buffer - поток битов, которые надо распаковать
            buffer = bitstream(barray[OFFSET_PACKED_DATA + 4:],  # + unk_beg_arch_dword # noqa
                               OFFSET_PACKED_DATA,   # вот с этого офсета будем заполнять
                               self.max_PTR_bits(),
                               self.toc.li_vrtx.ptr,  # не ошибка, нужен offset vrtx
                               self.toc.li_tstr)       # и list tstr тоже надо
            # BYTE_BITS = 8
            # USHORT_BITS = 16
            # UINT_BITS = 32

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
                # Для каждой геокатегории
                for _ in range(self.toc.li_shp.cnt + 1):     # +1 - всегда есть завершающий итем, нулевой # noqa
                    buffer.unpack_shape()
                    print(BYTESTRUCT(buffer.result))
                    self._raw += buffer.result
                    buffer.clear_result()

            print(f"cat {self.toc.li_cat}")
            print(f"shp {self.toc.li_shp}")
            print(f"lin {self.toc.li_lin}")
            print(f"poi {self.toc.li_poi}")
            print(f"vrt {self.toc.li_vrtx}")
            print(f"tst {self.toc.li_tstr}")
            print(f"str {self.toc.START_TXT:04x}")
            print(f"prev dword = {self.unk_beg_arch_dword:04x}")

            self.bit_tail = buffer
            # <<<<<<<<<< GEO_LINE

            # bi2b = buffer.buffer.tobytes()
            if self.toc.li_lin.cnt and False:
                # для каждой полилинии
                """
                
                """
                for _ in range(self.toc.li_lin.cnt + 1):     # +1 - всегда есть завершающий итем, нулевой # noqa
                    buffer.unpack_lines()

                    self._raw += buffer.result
                    buffer.clear_result()

            # <<<<<<<<<< POI
            # <<<<<<<<<< VERTEX
            # а вот дальше запакованы вертексы, и, вероятно, хаффманом
            if self.toc.li_vrtx.cnt:
                # huffman_lookup = self.vdo.get_block(0).lookup
                # decoded_output = b''
                # current_bits = ""
                # cnt_vrtx * 4 - побайтово
                for num in range(self.toc.li_vrtx.cnt * 4):
                    #
                    # # Шаг 3: Побитовое чтение и сопоставление со сгенерированным словарем # noqa
                    # for bit in buffer.buffer:
                    #     current_bits += str(bit)
                    #     if current_bits in huffman_lookup:
                    #         char = huffman_lookup[current_bits]
                    #         # if char == "[EOS]":
                    #         #     break
                    #         #decoded_output.append(char)
                    #         decoded_output += struct.pack(">B", char)
                    #         current_bits = ""  # Очистка буфера под следующий символ
                            
                    # bs = BYTESTRUCT(decoded_output)
                    # print(bs.hex)
                    pass
            # G
            # локально константами

            # чтобы при чвстичной распаковке нормально работал сетап - добиваем нулями
            self._raw += b'\x00' * (self.head.sizeofblock - len(self._raw))
        # =====================================================
        # записать распакованное
        self.write_raw()
        print(f"tail_{self.head.bladdr}.bin")
        with open(f"tail_{self.head.bladdr}.bin", "bw") as f:
            f.write(self.bit_tail.buffer.tobytes()) 
        # и, наконец, всё содержимое
        self.arr_shapes = []
        # self.lines = []
        # self.cats = []
        self.setup_objects()
        #self.setup_all_objects()
        
    def max_PTR_bits(self):
        '''
         # noqa
        Max число значащих бит в near offs в блоке из 
        seg_cnt сегментов размером по seg_size
        Максимальная длинна указателя в битах 
        (по размеру блока, на 1 меньше - word wrap)
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
        # hlat = UINT_struct.unpack(buff[8:12])[0]
        # if hlat:
        #     res = GEO_SHAPE(buff, category)
        res = GEO_SHAPE(buff, category)
        if self.is_unpacked:
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
                    // LON_LAT     THIS_NOT_coord; // THIS_NOT_coord    bl_offset( 0x293B9000 );
            2h - PTR   ptr_linesign, p_line_sign; // Or start pstr
            2h - WORD  or_b_or_c;
            2h - PTR   p_p_str_name; // ptr to GEO_OBJ_STR
            4h - WORD   or_38_or_0_b_country;
        """
        res = None
        if self.is_unpacked:
            buff = self.read(offset, GEO_LINE.size * 2)
            res = GEO_LINE(buff, category)
            # TODO
        
            res.name = self.read_str(res.p_str_name)
            res.tstr_regi = self.tstr(res.tstr_regi)
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
        if self.is_unpacked:
            buff = self.read(offset, VERTEX.size)
            res = VERTEX(buff)
            # TODO - а может при создании вертекса сюда же еще и реальные координаты?
        return res

    def tstr(self, offset: int) -> TSTR:
        """

        """
        res = None
        if self.is_unpacked:
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
    def get_all_categories(self) -> GEO_CATEGORY:
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
    result: bytearray       # распакованные данные

    def __init__(self, barray: bytes,
                 offset: int,
                 max_PTR_bits: int,
                 start_vrtx_ptr: int,
                 li_tstr: LIST) -> None:
        """
        Args:
            barray: bytes
            offset: int         offset от начала блока, который сейчас будет распаковываться
            max_PTR_bits: int   макс число бит в near offset
            vrtx_ptr: int       стартовый offset vertexes
            li_tstr: LIST       ptr-cnt на TSTR - объекты подписей на карте
        """
        self.buffer = bitarray(buffer=barray, endian='big').copy()    # copy - else read only memory # noqa
        self.result = bytearray()   # empty
        self.offset_start = offset
        self.max_PTR_bits = max_PTR_bits    # max possible bits in near offset
        self.start_vrtx_ptr = start_vrtx_ptr
        # self.li_tstr = li_tstr
        self.offset_tstr = li_tstr.ptr    # tstr стартует с этого смещения, каждый объект - + 1  # noqa
        self.counter_tstr_table_str = 0
        pass
    
    @property
    def av_head(self):
        """ Начало битов - 40 штук """
        res = self.touch(40).to01()
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
    def v_byte07(self):
        res = self.touch(7)
        #res = self.unpack(8, 7, 0, False)
        return ba2int(res)

    @property
    def v_byte08(self):
        res = self.touch(8)
        #res = self.unpack(8, 8, 0, False)
        return ba2int(res)

    @property
    def v_word15(self):
        res = self.touch(15)
        return ba2int(res)

    @property
    def v_word16(self):
        res = self.touch(16)
        return ba2int(res)

    @property
    def res(self):
        ''' online see result values'''
        return " ".join("{:02x}".format(c) for c in self.result)
    
    def pop(self, qty_bits: int) -> bitarray:
        '''pop qty_bits from begin (left) buffer qty bites'''
        val = self.buffer[:qty_bits]
        del self.buffer[:qty_bits]
        return val
    
    def touch(self, qty_bits: int, start: int = 0) -> bitarray:
        ''' Return qty bits from start Without deleting'''
        val = self.buffer[start:start + qty_bits].copy()
        return val

    def unpack(self, bit_goal: int, bit_compressed: int, left_shift: int=0, bool_save: bool=True) -> bytes:  # noqa:
        """
        Args:
            bit_goal: int  bits in result
            bit_compressed: int how many bits pop from self
            left_shift: int=0 - qty left shift result
            bool_save: bool save into self.result
        """
        res = self.pop(bit_compressed)  # pop bits from buffer
        val = bitarray((bit_goal - (res.nbytes * 8 - res.padbits)) * '0')  # leading zeroes  # noqa
        val += res                      # append lead zero with result
        val <<= left_shift              # left shift if lsch > 0
        # можно не сохранять - если значение надо интерпретировать перед сохранением
        if not bool_save:
            return val  # но тогда возвращать bitearray
        # в последовательность байтов   bres = val.tobytes() - только значащие байты, увы.  # noqa
        bres = val.tobytes()
        self.result += bres
        str_res = ''
        for h in bres:
            str_res += "{:02x}".format(h)   # str_res - for debug ))))
        return str_res   # bres

    def byte(self, qty_bit: int, left_shift: int = 0) -> None:
        """
        unpack byte from qty_bit to self.buffer
        Args:
            qty_bit:  Количество бит для интерпретации, как байт
            left_shift: сдвиг влево после распаковки
        """
        if qty_bit > BITS_IN_BYTE:
            raise ValueError(qty_bit, f"Значение больше {BITS_IN_BYTE}")
        str_res = self.unpack(BITS_IN_BYTE, qty_bit, left_shift)  
        pass

    def ptr(self, left_shift: int = 0) -> None:
        """
        unpack word (len=max_bits_ptr) to self.buffer
        Args:
            qty_bit:  Количество бит для интерпретации, как байт
            left_shift: сдвиг влево после распаковки
        """
        str_res = self.unpack(BITS_IN_WORD, self.max_PTR_bits - 1, left_shift)
        return str_res

    #
    def unpack_category(self) -> None:
        """
        BYTE  en_GEO_CATEGORY <--- 7 bits
        BYTE  0poligon_1poliline en_DRAW_TYPE <--- 1 bit
        WORD  ptr_to_category PTR <--- max_PTR_bits-1 bits
        """
        # /0/
        self.byte(BITS_IN_CATEGORY_TYPE)    # 7 bit на # en_GEO_CATEGORY
        # /1/
        self.byte(1)    # 1 бит на полигон0/полилиния1  # en_DRAW_TYPE
        # /2/
        # left shift 1 - т.к. last = 0 always in this ptr
        self.ptr(1)    # максимальное к-во бит для near ссылки word

    def unpack_shape(self) -> None:
        """
        # noqa
        WORD - ptr2string <--- word, ptr 2 zero-ended string
        WORD ptr2firstVertex  <--- запакованы не offs, а номера вертексов, vertnum, надо расчитывать ptr - offset
        DWORD id <----- read bit, if 1 - read next32bits as id, if not - so, not
        COORD - qword <--- coord 64bits
        ZeroWord align <--- no in arc
        WORD ptr_to_table_to_strings, unarc by calculate CURR_PTR_PTSTR +4 - next ptstr
        == # в хвостовом vertex = ptrStrTable, последний pstrt = pstrt + 4*pstr.cnt
        # ('011010101000 0000000010100000000000100010100101100011000001001000100111110011111010100000100000111001111100000101001000111010111000000010110100000000000110101010100000110000001101111010111101101101111111000011010011110101010011100010110111111101110001000010100000000000111101001100000011100001011100011110100011011111010000011011011100001101010111000101000100110100010011110100000000001000111101110100100100001010100010111011000100101011000011001011000001011111001101111000010101110011001110100000000001010010001101101010000001110011010111110100001111011000010111001000101100110010100001000101011010011110000000000110010111000000000001011111101101011111100011000000100000110110101100101100011101000110110010011111100011000001100100101001000001101000101100010011111000111000011111001101111101001000101011000110111110100001000011000011101110101111100001100011001001000010101010011000011100111101101110111011100001000111101000100010101000101111110110000110000001010011100010000010110001001000011100001001111111100110101001001000001000100100001001000010100110111001100001100011001011111110110100101000011111000110000000011000001001001000101010100101110000001000111110001110011111101100001010101101110000011101110000000100000010110111100110111000000000000000000100111010100000000000000100111101000010000001010111010001001001101010111000011010001100011100100011010010000000000000101001110100000000000001010001111011110000001100111011101000010111110010000011011111100011110011111010000000000000000101100010100000000000010010011011100101000001100111011011101100011010100000011010110001110011010010010010000000000000110011000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000110011000000001011001110010010000000000000110100000000010001111111111000000000000000110101000000010010010110100110000000000000110110100000010100000111001000000000000000111000000001000111000010010110000000000000111011100010011010110111101100000000000001000011100011001101001010011110000000000001001000100101010110011001110110000000000001011011001000001100011100010010000000000001100110000000000000000000000000000011111100111100000000000000010101010110001000101100100100011000101110011111010111000100000100000000010011000000000000010100111100110110000111110001110010010101100100000000101000000111101101001110011110011100011100100010101101101111111100111011100000010001000011000000011100000000000000011001011010000110000000000000011000001011001110111011001011100100011000011101111101100011110110011000110010011011110001001000010001101110100010010000100010100101011100001011110011010101111111001100100001111000111100101100110100001000100010110010101010010001000011101011111101000110010101110100110001111101011110100001101000110101010110001111010100001010000101111101011001011011111000010111111001110011000101011010000011011011010010001110110000000000010111111111100110111111001101101100100010111001000110000000110101101101010010101001011111000100100001011001010010000101001001000010110001101110011000000101000100011110110111010101101111110010101001011000011100111011010011011001100010011111011000100000111110111001001001011111101001100111010011100000010010001010001011010101010100111111110111000010111100110111001000111000001011000000000000000011000010011010000000101000111100010110010110010100011110011000011000000000000001100010110011000011100001011110011011100100011100000101100011010100101001100010011011101100110010101001001001011110001111010111010000110011110101100101011011101001100111000101001100110011111000000000011111011100000000000000001100000000000000000000000000001101011011111101001100001100100111010010011000001000000011100001000001000000101100111100000111001100011001110100100111110000001100000100110110001110001010010111110000000000000001100000101100111010000000000001010110011101110101110001110001000000000000110100000110010100110111111001100000000000000101000000001010000000000101100000000101011011001010111001111011001000011001100000010000100000010100000000000010010000010100001101001111001010001101000000000001100000010001010000010100001000000001110100000011011011000100001011010111001100110001100100000010100000000101011000000011010010000010010101101001111010000011101100010001100100000011001000000001101011000000000010100000101010011000110001101000111011101100110110100010011100100000111101110000000000111000011011010000010001101110001001101110110011010101010001111111101001110000001100100010100010011110101111010000110011101100101010000100101111011010110110101001011001100011010100011011001000101110001001011111000010101101110111111110011001110011110101110001110010100100001010001101110011000110100000110000110010011101100101001100100111110000000010011111011000110110101111110011100111010100110110011101100001111100010101001011000110111001001011111011110100100100001010010100101010001001000011000110111010100011110110011000011101111101110011011000110001010010111001001111100100001100000100000111001110001100111011001000001000100010110011110010011000000000000111001100111110000101101110000000000000000000010000011001000101111010101110011100010010101000011010000100110101100111011001100000000111011001011101001010001000000111001001100100000110011001000000001000110001001011111011110011001100001000100101111001010000100111111000000100111000110101001110110111110001100110110000100110011100000011110100010110000110011010011001000110101100101010110110000101000111010000100101100010010111000001001011010000111000111000100110101000101010111110000000000000000110011010100100010000000010000100000000101001111010001100000000001100000000011100011110110001001000101010000111100000000101101001000011001101001000001110000000011100000011011100100010101010000010000101100001001111100100010010110000011010101000000010111100010011111100100100010010000100000000000101011011000100000110001010111011000011100011001101000000100001110001101001110011000001010000011010100010001111011011010001111100011010110111110111100000110110110010001010010000101000110001110010000001011000011101100110000110101001101001001010001010011000000110110001010001011100101010011100101010101100101111100011011110001000100110001100101110111011101110010100001101101001011010000101101010111010110110000101101111000010111000010010110111000101011000001101110010100001011010000000011101000001101000000001111100100000000000000000110000000010010000000010101100100000111100010000100100000001010100000011101101010010000100001000000001001100100101000000011011100110001010001000010100111111000010010000100001100000010000110110000001001000001000001100000000001011111100010100000000010010101010000001010000000010100110000110010011000011010010000011010000001100100101001110010000100000010011100100000000000100000011000000001000000000001001110001101000000001011011011000010100000010000001011000010110000000010101100100010111000000010101101000000100000000000000000000011100000010001011011010000010100000000100110100001110000000011111110001000010101000000000111001000011100000100010000110000000100000000001101001100100100000001011110101010001000000000001001100110001111100001110000000000000000001001001101100110101101001001110000000000000001100111110001000111001011011100000000000000000000000000010110100111100000111110100000000000000000000000011010110000101010110101011001001010100100011100111110101110010000011101101101000100100100000000000000000000000001011000101001100001111101110110101011101010111100001101001001111110111110101101101001000011010010010011100110010100100101010011100110000000000000000000000000000110001010101011110000110100100111111001101101101001110011000100110110111010001100010101001001110011010000011100100111110101101001001111100000000000010010000011101001111101011011010101000100100011010000111100001110111011000010001111011011100101110010000011111010011110011110010000111100101111001011100100001111000011110010010000000011110100011001011101110001101101001010101101000100100111000011110001110011000101101011000110101011111110001111010000110101100001000100010000111101101000101101111000111001100001111111000111101000011010110000100010011000010101000100001111011010001011011110001110011000011111110001111010000110101100001000100110000101010001000011110110111000000010110001100100000111100010011011010000001101101001000110101010011110101100110000111101011110100001101010111100010010110100001111010111101000011010101110011011010010001101010100111101011000100001111010111101000011010100110110011100110110100100011010101001111010110011000011110101111010000110101011100110110100101010100010110101101010010110100001111010111101000010001010110100011110011001010110000111101011110100001000101010111101010001000011110110100010110111100011100110010111101010001000011110110100010110101001111000110000111110100011011011010011010100000101101000001000010000111100010010101100001101000110110110100110010011110101100110000100110001111101100010101011111110110111010010101011010001100110001101100000111111101101110100101010110100011001100011011010111011111110110100101101000011010001101101101001101010000110110101100010111110100011011000100110110010000110000111111010001001011111010001101100011011001001111010110001000010011000111110110001010101111101000110110110100110000101101111011010010110101000111110100011011011010011010100010011110001110011001010010000111101101001001011001111101000110110110100110010011110101100110000100110001111101100111111101101001011010000110100010101000101110100100000101100010010111111101101110100101110100010101000101110100100000101100011011101111111011011101001011101000101010001011101001001100000011011000110111011111110110111010010111010001010100010111010010011000001010110001101110111111101101110100101110100010101000101110100100110000000101101010000001111101000100011010110011000111110110001010101111101000101010001011101001000001011000100010110100000100001000011111110110110100100011000100110101100110001111101100010101011111110110110100100011000100110101101010001011010001010000110000111111010001001011111110110110100010101010011010111110110100100101100111111110110110000100101011010011110110100101101010001111101000101010001011101001000001011000100010110100000100001000101110111101011111101011111110000011111011011111000101011111111010101101001001111010111111010101000100001111101101111100010111110101011010010101110111101011111101011111110000011111011011111000101111101010110100100111101011111101011111110000011111011011111000101111101010110100101011101111111101100001000111111010111111101001111111011011011110110000111100011101110111111101101110010001101100001111000111011101111111011011100100001011000011110001110111011100010110100011011101100110000011100010110100011011101100110001011111110001000101101011001111111000100010110101100000111111100010001011010110001011111111000000001101010001000111000010110000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001010100010001010100010001010100010001010100010001010100010001010100010001010100010001010100010001010100010001010100010010110101010001000000101000001011010111000100001111100010101101100100010000011001011011011011100001011010110111011101000011100101110000000110000010001011100001011100000111010111000111001000010100101110010101110000110001011100111101100000001010111010010001000000110101110101001010000010101011101011100100000010100000101110110101110000111010001010111100000001000010110101111000110010000010100100000110001000011110101111001100010000001101011110101001100000001010111101101111000001110101111100011110000110001011111010101100000100010111111010001000010100101111111011110000001110000011000000010001000001011000101100000011001100000110011000001010101000011110110000011101110000101101100001001100100000111011000010101111000000100110000110100110000101000100001110011000011101011000000010110001000011010000010001100010010001100001100011000100110101000000101000001100000001000100000101100010110000001100110000011001100000101010100001111011000001110111000010110110000100110010000011101011111110111100000011011000011010011000010100010000111001100001110101100000001011000100001101000001000110001001000110000110001100001010111100000010100000110000000100010000010110001011000000110011000001100110000010101010000111101100000111011100001011011000010011001000001110101111111011110000001101100001101001100001010001000011100110000111010110000000101100010000110100000100011000100100011000011000110001010110110000001110000011000101110001000001011000101100011000100100000001001000001000010000011100100001011001000011000110001100111010000011000100001111011000110110011000001001000001100011011111100000011011000111001101000001101000101100011101101100001011011000111001101000011110110001111010010000101110000011000111111001000000111000101100100000100100000100100000110010000100110000010110001001000001100010000111100001100100001111100000010001000000110110010001010101000001100100011011100000101100010110010010001010000110001100100101010100000001011001001100011000001100010000101100101010001001010111010010110100100101110101001100000010011000110100110010110001100101110011001101100110011101001101001000011010101000110101010001101010100011010101000000000001000000000010000000000100000000001000000000010000000000100000000001000000000010000000000100000000001001100100011011100100110110000111110000110000111100100000110000010000110000010000110000010000110000010000110000011101000011010010010101000111110100001101001010001001010001111101000011010011110101001000111110100001110001100010001111000000000000000000000000000000000000000000000000000000')
            06a8          0214
        011010101000    001000010100
        """
        # /0/ WORD - ptr2string <--- word, ptr 2 zero-ended string
        # if 0 - zero tail ptr2table str
        flag_calc_ptr2tstr = self.unpack(BITS_IN_WORD, self.max_PTR_bits - 2, 0) != '0000'
        
        # /1/ word, ptr 2 first vertex
        # запакованы не offs, а номера вертексов vertnum,
        # т.е. off2vertex0 + 4*vertnum = offset распакованный
        # макс. число для архивированного значения - в vertex.cnt
        # -2: надо в 4 раза меньше бит, т.к. ptr vrtx кратен 4 -> self.max_PTR_bits - 2
        start_vrtx_num = self.unpack(BITS_IN_WORD, self.max_PTR_bits - 2, 0, False)  # не сохранять в result!  # noqa
        start_vrtx_num = ba2int(start_vrtx_num)     # номер 0-го vrtx объекта
        print(f"start_vrtx_num = {start_vrtx_num}")
        # 4* num = offset from start vertexes
        vrtx_off = self.start_vrtx_ptr + VERTEX.size * start_vrtx_num
        self.result += USHORT_struct.pack(vrtx_off)     # vertx offs 2word, save

        # /2/  dword, id -
        #self.pop(1)
        #id - если следующий бит = 1, ЕСТЬ ID, иначе пропустить
        if self.touch(1) == bitarray('1'):
            self.pop(1)     # флаг наличия id в запаковке - '1' - больше не нужен
            self.unpack(BITS_IN_UINT, BITS_IN_UINT, 0)
        else:
            # id в архиве нет, ID = 00 00 00 00
            self.result += b'\x00' * 4

        # /3/  dword dword - coord
        # координаты - они есть, всегда. Просто лежат без упаковки
        self.unpack(BITS_IN_UINT, BITS_IN_UINT, 0)        # _lon
        self.unpack(BITS_IN_UINT, BITS_IN_UINT, 0)        # _lat

        # /4/  word align
        self.result += b'\x00' * 2
        
        # /5/ word - ptr2table
        # WORD ptr_to_table_to_strings, unarc by calculate CURR_PTR_PTSTR +4 - next ptstr  # noqa
        off_tstr = self.offset_tstr
        self.result += USHORT_struct.pack(off_tstr)
        self.offset_tstr += TSTR.size
        # ---- old
        # WORD ptr_to_table_to_strings, unarc by calculate CURR_PTR_PTSTR +4 - next ptstr  # noqa
        # if flag_calc_ptr2tstr or self.counter_tstr_table_str == self.li_tstr.cnt:
        #     # num_shape - рассчитать номер в table tstr, из него - offset
            
        #     off_tstr = self.li_tstr.ptr + TSTR.size * self.counter_tstr_table_str
        #     self.result += USHORT_struct.pack(off_tstr)
        #     self.counter_tstr_table_str += 1
        # else:
        #     # в хвостовом vertex = ptrStrTable, последний pstrt = pstrt + 4*pstr.cnt
        #     self.result += b'\x00' * 2
        #SAVE RES
        # todo - tail?????

        '''
        # noqa
        Geo shape - closed, filled poligon
        2h - ptr2str/0;
        2h - ptr2vertexes (first=first vert)
        4h - id [0000 7685]
        8h - LON_LAT
        2h = 00 00 - aligment (??? or POI?)
        2h - ptr2 list strPtr

        bmw_a_1d = vf.block(0xE2A2A00)
        map:                       '3c 6d 90 00  13 7a 50 00 --   
                                    3f 6d 90 00  16 7a 50 00    '3c 6d 90 00 13 7a 50 00 3f 6d 90 00 16 7a 50 00 00 01 00 0a'00 01 00 0a'

        08c0 00a0 40 01 8d 00 3e 8b 4f f4 14 62 9e 01 00 00 08b0 < to first tstr
        08d3 0298 40 02 3f f0 3f d4 0f e0 14 3e b2 69 00 00 08b4
        08e5 0344 40 04 2b 13 3e 75 79 94 13 e8 ef 5a 00 00 08b8
        08f6 0770 40 12 e8 aa 3b 0e bb 42 12 26 61 83 00 00 08bc
        0000 08b0 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08c0 < to txt from
        cat 0034:0001 cnt:1
        shp 003c:0004 cnt:4
        lin 0000:0000 cnt:0
        poi 0000:0000 cnt:0
        vrt 00a0:0204 cnt:516
        tst 08b0:0004 cnt:4
        str 08c0
        SHAPE WATER[4] :0x3c
        '''

    def unpack_lines(self) -> None:
        """

        """
        """
         # noqa
        Geo segment of line - poligon
        0:    2h - PTR         p_str_name - ptr2str/0;
        2:    2h - PTR         ptr_vrtx       p_vertexes_obj; ptr2vertexes
        4:    4h - DWORD       id
                    // LON_LAT     THIS_NOT_coord; // THIS_NOT_coord    bl_offset( 0x293B9000 );
        6:    2h - PTR   ptr_linesign, p_line_sign; // Or start pstr
        8:    2h - WORD  or_b_or_c;
        10:   2h - PTR   ptr_tstr     p_p_str_name; // ptr to GEO_OBJ_STR
        12:   4h - WORD   or_38_or_0_b_country;
        GEO_LINE_struct = struct.Struct(">HHLHHHHxxH12x")
        """

        """
        ru34: 0x08a06b02
            shp 0044:0001 cnt:1
            lin 006C:0002 cnt:2
            poi 0000:0000 cnt:0
            vrt 009C:011F cnt:287
            tst 0518:0002 cnt:2     518=0101 0001 1000, 51c = 0101 0001 1100
            str 0520  = 0101 0010 0000
        05 20 00 9c 40 04 5a a0 09 3c ac fb 0b e5 61 6f 00 00 05 18
        00 00 04 ac 00 00 00 00 00 00 00 00 00 00 00 00 00 00 05 1c
      > xx xx 04 ac
> p_str_name > 0520
ptr<<2 = 530
> ptr_vrtx ?? == 04ac?  num 260 dec | 104h
> word id ?? (есть ли проверка на существование?)
> tstr_regi > tst 0518  (? < str 0520 ??)
> word or_b_or_c - какое-то число?
> tstr_name     (0520 ????)
> word or_38_or_0_b_country

        """
        # /0/  p_str_name > 0520
        # bitarray('0 10100110001 100000100001110110011010000000
        # p_str_name = 05 31
        self.pop(1)
        i0_p_str_name = self.unpack(16, 11)     # 12? max_PTR_bits = 11  или << а след бит - флаг?

        # /1/  ptr_vrtx ?? == 04ac?  num 260 dec | 104h
        # bitarray('10000010000111011001101000000000000100010011
        # vrtx_num = 260 dec | 104h
        # vrtx_off = 04 ac
        # self.pop(1)
        start_vrtx_num = self.unpack(BITS_IN_WORD, self.max_PTR_bits - 2, 0, False)  # не сохранять в result!  # noqa
        start_vrtx_num = ba2int(start_vrtx_num)     # номер from 0-го vrtx объекта
        print(f"start_vrtx_num = {start_vrtx_num}")
        # 4* num = offset from start vertexes
        vrtx_off = self.start_vrtx_ptr + VERTEX.size * start_vrtx_num
        self.result += USHORT_struct.pack(vrtx_off)     # vertx offs 2word, save

        # /2/ > word id ?? (есть ли проверка на существование?)
        # bitarray('00111011001101000000000000100010')
        i2_id = self.unpack(32, 32)        # = '05 31  04 ac  3b 34 00 22'

        # /3/ > tstr_regi > tst 0518  (? < str 0520 ??)
        # bitarray('01 10100111000 00010
        i_z = self.pop(2)
        # = 05 38
        i3_p_tstr_regi = self.unpack(16, 11)

        # /4/ > word or_b_or_c - какое-то число?
        # bitarray('0001000000000000 1000111110000000000000001100000000
        i4_or_b_or_c = self.unpack(16, 16)        # '05 31  04 ac  3b 34 00 22  05 38   10 00'  # noqa

        # /5/ > tstr_name     (0520 ????)
        #  bitarray('100011111000000000000000110000000000000000010000100000001110010
        self.pop(1)
        i5_p_tstr_name = self.unpack(16, 11)       # '05 31 04 ac 3b 34 00 22 05 38 10 00 f880'  # noqa

        # /6/ > word or_38_or_0_b_country
        #
        i6_or_38_or_0_b_country = self.unpack(16, 16)

        #==============================
        print(BYTESTRUCT(self.result))
        self.clear_result()
        self.unpack(16, 12)     # 12? max_PTR_bits = 11  или << а след бит - флаг?

        # /1/  ptr_vrtx ?? == 04ac?  num 260 dec | 104h
        start_vrtx_num = self.unpack(BITS_IN_WORD, self.max_PTR_bits - 2, 0, False)  # не сохранять в result!  # noqa
        start_vrtx_num = ba2int(start_vrtx_num)     # номер from 0-го vrtx объекта
        print(f"start_vrtx_num = {start_vrtx_num}")
        # 4* num = offset from start vertexes
        vrtx_off = self.start_vrtx_ptr + VERTEX.size * start_vrtx_num
        self.result += USHORT_struct.pack(vrtx_off)     # vertx offs 2word, save

        # /2/ > word id ?? (есть ли проверка на существование?)
        # bitarray('00111011001101000000000000100010')
        id = self.unpack(32, 32)        # = '05 31  04 ac  3b 34 00 22'

        # /3/ > tstr_regi > tst 0518  (? < str 0520 ??)
        # bitarray('01 10100111000 00010
        i_z = self.pop(2)
        i_tstr_regi = self.unpack(16, 11)

        # /4/ > word or_b_or_c - какое-то число?
        # bitarray('0001000000000000 1000111110000000000000001100000000
        ior_b_or_c = self.unpack(16, 16)

        # /5/ > tstr_name     (0520 ????)
        #  bitarray('100011111000000000000000110000000000000000010000100000001110010
        i_tstr_name = self.unpack(16, 16)

        print(BYTESTRUCT(self.result))
        self.clear_result()

        print(self.v_byte8)
        print(BYTESTRUCT(self.result))
        """
         # noqa
        bitarray('
        4ac 010010101100
        p_start_vrtx_num = 260 = 104h =  000100000100
        531
        010100110001
        p_start_vrtx_num = 260 = 104h =  000100000100
        1000001       41h<<2=104    -> 04ac
        id '0ecd0008'
        0000111011001101 0000000000001000
        

100110100111000000100000000000010001111100000000000000011000000000000000001000010000000111001011010010110000



        tst 0518:0002 cnt:2     518=0101 0001 1000   010100011000 , 51c = 0101 0001 1100  010100011100
                    str 0520  = 0101 0010 0000   010100100000
        """
        pass

    pass   # class unpack_type_one():
