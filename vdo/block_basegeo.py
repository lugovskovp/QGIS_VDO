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
from vdo.datatypes import UINT_struct, USHORT_struct, USHORT_TWICE_struct    # BYTE_struct,


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
            # первые 2 word - назначение неизвестно. 83888384 = 5000 9000
            # ?
            self.beg_arch_word_A = USHORT_struct.unpack(barray[OFFSET_PACKED_DATA:OFFSET_PACKED_DATA + 2])[0]  # noqa 
            # ?
            self.beg_arch_word_B =  USHORT_struct.unpack(barray[OFFSET_PACKED_DATA + 2:OFFSET_PACKED_DATA + 4])[0]  # noqa 
            # остальное в buffer - поток битов, которые будем распаковывать
            buffer = bitstream(barray[OFFSET_PACKED_DATA + 4:],  # + unk_beg_arch_dword # noqa
                               OFFSET_PACKED_DATA,   # вот с этого офсета будем заполнять
                               self.max_PTR_bits(),
                               self.toc.li_vrtx.ptr,  # не ошибка, нужен offset vrtx
                               self.toc.li_tstr)       # и list tstr тоже надо
            # BYTE_BITS = 8
            # USHORT_BITS = 16
            # UINT_BITS = 32

            # суммарная уже известная информация
            print(f"\n{self.vdo.path}\n{self.head.bladdr}  {self.head.bltype}: 0x{self.head.bltype.value:02x}")
            print(f"\nMax PTR bites: {self.max_PTR_bits()}")
            end = f"\tnext ptr: {(self.toc.li_cat.cnt + 1) * 4 + self.toc.li_cat.ptr:04X}" if self.toc.li_cat.cnt else ""  # noqa
            print(f"cat {self.toc.li_cat} {end}")
            end = f"\tnext ptr: {(self.toc.li_shp.cnt + 1) * 0x14 + self.toc.li_shp.ptr:04X}" if self.toc.li_shp.cnt else ""  # noqa
            print(f"shp {self.toc.li_shp} {end}")
            end = f"\tnext ptr: {(self.toc.li_lin.cnt + 1) * 0x10 + self.toc.li_lin.ptr:04X}" if self.toc.li_lin.cnt else ""  # noqa
            print(f"lin {self.toc.li_lin} {end}")
            # size poi???? 12?
            end = f"\tnext ptr: {(self.toc.li_poi.cnt + 1) * 12 + self.toc.li_poi.ptr:04X}" if self.toc.li_poi.cnt else ""  # noqa
            print(f"poi {self.toc.li_poi} {end}")
            end = f"\tnext ptr: {(self.toc.li_vrtx.cnt) * 4 + self.toc.li_vrtx.ptr:04X}" if self.toc.li_vrtx.cnt else ""  # noqa
            print(f"vrt {self.toc.li_vrtx} {end}")
            end = f"\tnext ptr: {(self.toc.li_tstr.cnt) * 4 + self.toc.li_tstr.ptr:04X}" if self.toc.li_tstr.cnt else ""  # noqa
            print(f"tst {self.toc.li_tstr} {end}")
            print(f"strs from {self.toc.START_TXT:04X}")
            print(f"begin word = {self.beg_arch_word_A:04X}:{self.beg_arch_word_B:04X}")
            print(f"Map_hex: {self.map.hex}\n")
            pass

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
                    #----------------
                    bs = buffer.result     # _for_print
                    pp = f"{USHORT_struct.unpack(bs[0:2])[0]:04X} {USHORT_struct.unpack(bs[2:4])[0]:04X}"
                    pp += f" {UINT_struct.unpack(bs[4:8])[0]:08x}"
                    pp += f"  {UINT_struct.unpack(bs[8:12])[0]:08X} {UINT_struct.unpack(bs[12:16])[0]:08X}"
                    pp += f"  {USHORT_struct.unpack(bs[16:18])[0]:04X} {USHORT_struct.unpack(bs[18:20])[0]:04X}"
                    print(pp)
                    #---------------
                    self._raw += buffer.result
                    buffer.clear_result()

            # <<<<<<<<<< GEO_LINE
            if self.toc.li_lin.cnt:
                # для каждой полилинии
                """
                
                """
                for _ in range(self.toc.li_lin.cnt + 1):     # +1 - всегда есть завершающий итем, нулевой # noqa
                    buffer.unpack_lines()

                    self._raw += buffer.result
                    buffer.clear_result()

            self.bit_tail = buffer
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
        print(f"Максимальные Х и У: {self.max_bounds}")
        # записать распакованное
        self.write_raw()
        if not self.is_unpacked:
            print(f"tail_{self.head.bladdr}.bin")
            with open(f"tail_{self.head.bladdr}.bin", "bw") as f:
                f.write(self.bit_tail.buffer.tobytes()) 
        # и, наконец, всё содержимое
        self.arr_shapes = []
        # self.lines = []
        # self.cats = []
        self.setup_objects()
        #self.setup_all_objects()

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
        unpack one byte from qty_bit to self.buffer
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
        unpack word (packed len=max_bits_ptr) to self.buffer
        Args:
            qty_bit:  Количество бит для интерпретации, как байт
            left_shift: сдвиг влево после распаковки
        """
        str_res = self.unpack(BITS_IN_WORD, self.max_PTR_bits, left_shift)
        return str_res

    def ptr_w(self, left_shift: int = 0) -> None:
        """
        ptr, выровненный по word
        unpack word (len=max_bits_ptr - 1) to self.buffer
        Args:
            left_shift: сдвиг влево после распаковки
        """
        str_res = self.unpack(BITS_IN_WORD, self.max_PTR_bits - 1, left_shift)
        return str_res

    def ptr_d(self, left_shift: int = 0) -> None:
        """
        ptr, выровненный по dword
        unpack word (len=max_bits_ptr - 2) to self.buffer
        Args:
            left_shift: сдвиг влево после распаковки
        """
        str_res = self.unpack(BITS_IN_WORD, self.max_PTR_bits - 2, left_shift)
        return str_res

    #---------------------------------------------------
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
        self.ptr_w(1)    # максимальное к-во бит для near ссылки word

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
        """
        # /0/ WORD - ptr2string <--- word, ptr 2 zero-ended string
        # if 0 - zero tail ptr2table str -- вот кстати вопрос - на точно ли так надо ваще????
        # flag_calc_ptr2tstr = self.unpack(BITS_IN_WORD, self.max_PTR_bits, 0) != '0000'
        flag_increment_ptr2tstr = self.ptr() != '0000'
        """
        begin word = 0500:0900   self.ptr()
        WORD - ptr2string
        tst 08B0:0004 cnt:4     next ptr: 8c0  strs from 08c0  100011000000  max_PTR_bits=12
        '100011000000 0000000000 101000000000000011'
        """
        pass

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
        """
        ptr2string, ptr2firstVertex
        begin word = 0500:0900   self.ptr(), calc_vrtx_offs, 
        
        tst 08B0:0004 cnt:4     next ptr: 8c0  strs from 08c0  100011000000  max_PTR_bits=12
        """

        # /2/  dword, id -
        #self.pop(1)
        #id - если следующий бит = 1, ЕСТЬ ID, иначе пропустить
        if self.touch(1) == bitarray('1'):
            self.pop(1)     # флаг наличия id в запаковке - '1' - больше не нужен
            self.unpack(BITS_IN_UINT, BITS_IN_UINT, 0)
        else:
            self.pop(1) 
            # id в архиве нет, ID = 00 00 00 00
            self.result += b'\x00' * 4
        """
        ptr2string, ptr2firstVertex, id
        begin word = 0500:0900   self.ptr(), calc_vrtx_offs, 

        '1 010000000000000110001 101000000000011111'
        """

        # /3/  dword dword - coord, here '08 c0 00 a0 40 01 8d 00'
        # координаты - они есть, всегда. Просто лежат без упаковки
        self.unpack(BITS_IN_UINT, BITS_IN_UINT, 0)        # _lon
        self.unpack(BITS_IN_UINT, BITS_IN_UINT, 0)        # _lat
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
        off_tstr = self.offset_tstr
        self.result += USHORT_struct.pack(off_tstr)
        if flag_increment_ptr2tstr:
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

> p_str_name > 0520
ptr<<2 = 530
> ptr_vrtx ?? == 04ac?  num 260 dec | 104h
> word id ?? (есть ли проверка на существование?)
> tstr_regi > tst 0518  (? < str 0520 ??)
> word or_b_or_c - какое-то число?
> tstr_name     (0520 ????)
> word or_38_or_0_b_country

c:\DIY\VDO\db_src\ru_2013\ru\carindb
08a06b 02  BlockType.MAP__06k80: 0x15

Max PTR bites: 11
cat 0034:0003 cnt:3     next ptr: 0044
shp 0044:0001 cnt:1     next ptr: 006C - only one shape.
lin 006C:0002 cnt:2     next ptr: 009C - two lines
poi 0000:0000 cnt:0 
vrt 009C:011F cnt:287   next ptr: 0518
tst 0518:0002 cnt:2     next ptr: 0520
strs from 0520
begin word = 0E00:0900
Map_hex: 08 B9 30 00 0B 9A 50 00  09 19 30 00 0B FA 50 00   00 01 00 07  
518 -> str520 - 'mar mediterráneo' +\x00
51c -> str531 - river name  ? Уэд-Мудуйа ? море Альборан? Oued Kert ?
01 00 00 44  WATER
65 01 00 6C  RIVER_MAJOR
67 01 00 7C  BORDER
00 00 00 8C   EMPTY
        """
        # /0/  p_str_name >= 0520
        # '10100110001 10000010000111011001101000000'
        # p_str_name = 05 31
        i0_p_str_name = self.ptr()
        # '0531 ' cool! 520 + len 'mar mediterráneo' +\x00

        # /1/  ptr_vrtx ?? shp:009C-04AC,  lines=4ac-0518 
        # bitarray('100000100 00111011001101000000000000100010011
        # vrtx_num = 260 dec | 104h
        # vrtx_off = 04 ac
        # self.pop(1)
        start_vrtx_num = self.unpack(BITS_IN_WORD, self.max_PTR_bits - 2, 0, False)  # не сохранять в result!  # noqa
        start_vrtx_num = ba2int(start_vrtx_num)     # номер from 0-го vrtx объекта
        print(f"start_vrtx_num = {start_vrtx_num}/0x{start_vrtx_num:02x}")
        # 4* num = offset from start vertexes
        vrtx_off = self.start_vrtx_ptr + VERTEX.size * start_vrtx_num
        self.result += USHORT_struct.pack(vrtx_off)     # vertx offs 2word, save
        # '0531 04ac ' cool! 04ac as tail shp, bingo

        # /2/ > word id ?? (есть ли проверка на существование?
        # и есть ли макс ид для линий?)
        # mar mediterráneo id= 40045aa0 = mar mediterráneo
        #k = self.pop(1)
        if True or k != '1':
            #
            i2_id = self.unpack(32, 32)        # map = '08B9 3000 0B9A 5000  0919 3000 0BFA  5000'\
                                               # 35.039236N 3.656246W  36.171698N 2.523783W
        else:
            i2_id = '0'
            self.result += b'\x00' * 4
        # '0531 04ac 3b340022'
        # '05 31 04 ac ec d0 00 89' + pop(2) - 00

        # /3/ > tstr_regi > tst 0518  (? < str 0520 ??)  <<2, т.к. сразу за vortex
        # 518 0 101000110 00 -> 520
        # 51c 0 101000111 00 -> 531
        # 520 0 101001000 00 
        # 531 0 10100110001
        # 538 '1010011100000010000000000001000111110000'
        #   i_z = self.pop(2) 400c 0100000000001100
        # '0111011001101000000000000100010011010011'
        i3_p_tstr_regi = self.unpack(16, 11)
        # '0538' -like ptr 2 string - but early pop 00
        # 00111011001101000000000000100010
        # 01101001110000001000000000000100011111000000000000000110000000000000000010000100000001110010110100101100000000000100 101000110 010110110100010011110001001010101110001010101101011100110011010011010110 101000111 0000110001111010000100100111000001001110000000110011001001111110100101001001110001011001101111100011001111001001110000101010100001100011101100110101001101010110011001100001011110000000011110110011011100010111110001101100100111111010011110011100101110001
        # bitarray('001110110011010000000000001000100110100111000000100000000000010001111100000000000000011000000000000000001000010000000111001011010010110000000000010010100011001011011010001001111000100101010111000101010110101110011001101001101011010100011100001100011110100001001001110000010011100000001100110010011111101001010010011100010110011011111000110011110010011100001010101000011000111011001101010011010101100110011000010111100000000111101100110111000101111100011011001001111110100111100111001011100010001111001001111111001111101101010010101100111111101010000001001000101101001101011000001010011001010111001110001101010101011101111000101011111111111100100110001001010110011001001000100111000100001110110001101001111000110010000000010001000000100011100000100010101000000000001001100001000100110001001110110000110010111001010111100110101101001001000101101101011101111101001000111100010110110101101000100100100100001011001011100101001000001000011110001000100111000000110001000100100011101011001001000000101011110010111011000111001100000010100010110001001110010000100010111001001010100110101000000100010100000001010110000100101101110110001011110100111001101000001100110010110101001110000010010011101010000001010000100100000101111110010101010001101111110001101100001011001100001010100101010001010010101001011000011001110000000111010010010000110000101111001011101101011010111100011100111001111100101100010101001000000100010000111000100111110000001101101000011010001001001100001101100011000001000110110110001000010100101011100110011011100010110010010110110100011100110011110111101010100010000110111100010111110001100110101000100010001110011100001100100000101011000101010110001111001001111110110000111100000100000110100010000010101001010001001001000100101010100011100001101010110001001001000101000010011100101001101011010101110001010100001110100110010010010010010101001101010100010100111101110101101001001000100000110100101000110110100111101011000100111000010011010010000001101011111011001101011000100101101000010000010000010100001100000010011001010100001001001000011001010011000000001010111100011101001001111101110010001000100000011001000100010010001110110100000111110010001101100101110011000000011100000100110001001011001010001101001110001001000111010011111000100110001000000100110000000110100011100011000100101010000110011100100101110011000001000110010100010110101000111000110000000111100000000010010001010001000010100000111110000001010000000101100001001011000001111000010000110001101111100001111101000100011110001101101000001001100000001100001001011000110110110000101111100100001100000111110000101001000011001010001100100000001111100100001111000110001100100111110000101000000011111010001111100100000101000010011000100000111110000100100101010000110000010111100011000010001001110100010011000100010001100110000010001001010101000010000011000001000101110101000100011001100010100010100011001101000001000110011001101101000110100011001100001001010011000011111010011101100010011001000001110111010010000110001111010010100101001010011010000000001100001110001001001100100111101000001001111010101000100111111110011101111100101101100011101110010100100111001111011110111110001111010000010011110010010111001101000110001101101100000001010001111010011001110011011101111001011000111110001000111001001101111111011001000100110111111001000110010000011000100000100101000101111110111101100001010010010011110011101000110111101110000000011000001000000100001101111001011001100000001101000111000110000011000100111101000000100100100111010011000101101110001110010101000110001001110101010001111001100001101110000110001100010010101001011110110011011111010100110110010011111100010010001001011110110101010100000111001000011100111000111011100000001101010110010111011010101010001011001101100011011010000011001100110100011011101111111001100101010100110011111111101010111001000110011110011101110101000111011011001011110011011010101001000011000001001110001110111100111001101001100001010010110000100110001101010111111010101101011100110101001001010111010001100001100001111001010111100010010101110100111110001001001010110100111011100010101011001001100010000011001101110100110011011111100100100010011101110101110001110010000001100010101011000111110100010000111000110110110001100111100011100101001110011010010101111100001001001000111011010110011100110010010101100100101000001001010001101110011100110100110001111000011011110001101101110100111111001001110010000010100010101110001101001001011010011100110100101011111010011010000000001011001001001000101011011001110110010000110111101100010101001110000010100110101000010110011010001001010110010011110101100010101011000011001010110000011100101000001001001111000000000001011100011010000110011101010000011000011001110110001001100011001001010010111110000110010101001101001001001101110010011110100001010001000100111010000110010100101000111001110010110001001000100010100001010011101110010100100101011111011001000100010100111011100001010001011100110000010010011001001100000001011001010011010100001101101011100000000000011011001010001100000111011010011010110000011001101001010010000110000110010011001111001001001010010010011101000000111010100101010001000111110010011110000010011110100110000010101111110110011011100011100111010001110110001010001110001110101110101100011110101100011000100001000101001011101110101100011000001100111001000000110100100101000110011001000101000101010001001000110001000111110111000100111110110010101000100111010100010001100000100101011001010100001100011100001011100100000010100011100011110010000101001101100111110011100111100011110010000100100101100010000010101100100101110010100001101100111010110010100001100111111100000110100101100111110100011110101000100000001011011100110000000010010111101001000010010100101100010001010000100001000000000011110000000000000011110000000000000000000000001101110100100011011100101011110000000011010110100100100010000111011000111000100101001100000001001001000110110010010000010010001110000101101001011000110010111100010100010110001001010101001110010000111111100110101110011010011101000011010000011100100100000010010000111100101001101000000110110001000110100011001011001100100100011001111101111011001101111100100111011011111011001010110010111111101111111111000101001110010011101010011101111011101001001110001100100100000100100001011001000011110010000101101100000100010000111000100110111000000001010000111001011001011001001001101010001101100101110111001100101000000001011110110100100000101001110110000110000010000110000010000110000010000110000010000110000010000110000011111011010000110100001111011010011000110100010100101100110110000001101100011011101110110110001100101111000010001001100001011101101011101110000101100000000000000000000000000000000000000000000000000000000000000000000000000001010001100010100011000101000110001101001000001000001101000001101001100010010100011001010001110101000111010100100001010010000001000000000000000000000000000000000000000000000000000000')

        # /4/ > word or_b_or_c - какое-то число?
        # '0001000000000000 100011111000000000000000'
        i4_or_b_or_c = self.unpack(16, 16)        # '05 31  04 ac  3b 34 00 22  05 38   10 00'  # noqa

        # /5/ > tstr_name     (0520 ????)
        #  '1000111110000000000000001100000000000000'
        self.pop(1)
        i5_p_tstr_name = self.unpack(16, 11)       # '05 31 04 ac 3b 34 00 22 05 38 10 00 f880'  # noqa

        # /6/ > word or_38_or_0_b_country
        # у границ = 0? 67
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

        #print(self.v_byte8)
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
