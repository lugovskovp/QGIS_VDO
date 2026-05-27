"""
block_basegeo - Базовый тип для - карт   00 16 15 1c 14 1d 1e # noqa: E116
bitstream - class wrapper for bitarray
"""
import struct
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
        self.shift_scale = self.uint(OFFSET_SCALE)
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
                    buffer.result.clear()

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
                    buffer.result.clear()

            print(f"cat {self.toc.li_cat}")
            print(f"shp {self.toc.li_shp}")
            print(f"lin {self.toc.li_lin}")
            print(f"poi {self.toc.li_poi}")
            print(f"vrt {self.toc.li_vrtx}")
            print(f"tst {self.toc.li_tstr}")
            print(f"str {self.toc.START_TXT:04x}")
            # <<<<<<<<<< GEO_LINE

            bi2b = buffer.buffer.tobytes()
            if self.toc.li_lin.cnt:
                # для каждой полилинии
                """
                
                """
                for _ in range(self.toc.li_lin.cnt + 1):     # +1 - всегда есть завершающий итем, нулевой # noqa
                    buffer.unpack_lines()

                    self._raw += buffer.result
                    buffer.result.clear()

            # <<<<<<<<<< POI
            # <<<<<<<<<< VERTEX
            # G
            # локально константами

            # чтобы при чвстичной распаковке нормально работал сетап - добиваем нулями
            self._raw += b'\x00' * (self.head.sizeofblock - len(self._raw))
        # =====================================================
        # записать распакованное
        self.write_raw()
        # и, наконец, всё содержимое
        self.arr_shapes = []
        # self.lines = []
        # self.cats = []
        self.setup_objects()
        #self.setup_all_objects()
        
    def max_PTR_bits(self):
        '''
        Max число значащих бит в near offs в блоке из 
        seg_cnt сегментов размером по seg_size
        Максимальная длинна указателя в битах 
        (по размеру блока, на 1 меньше - word wrap)
        '''
        #max_addr = self._const_segsize  * seg_cnt - 1   
        # # Максимально возможное значение адреса; 2 -> 0x800*2=0xfff 
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
                 max_PTR_bits: int, 
                 start_vrtx_ptr: int,
                 li_tstr: LIST) -> None:
        """
        Args:
            barray: bytes
            max_PTR_bits: int   макс число бит в near offset
            vrtx_ptr: int       стартовый offset vertexes
            li_tstr: LIST       ptr-cnt на TSTR - объекты подписей на карте
        """
        self.buffer = bitarray(buffer=barray, endian='big').copy()    # copy - else read only memory # noqa
        self.result = bytearray()   # empty
        self.max_PTR_bits = max_PTR_bits    # max possible bits in near offset
        self.start_vrtx_ptr = start_vrtx_ptr
        # self.li_tstr = li_tstr
        self.offset_tstr = li_tstr.ptr    # tstr стартует с этого смещения, каждый объект - + 1
        self.counter_tstr_table_str = 0
        pass
    
    @property
    def v_byte8(self):
        res = self.touch(8)
        #res = self.unpack(8, 8, 0, False)
        return ba2int(res)

    @property
    def v_byte7(self):
        res = self.touch(7)
        #res = self.unpack(8, 7, 0, False)
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
        val = bitarray((bit_goal - (res.nbytes * 8 - res.padbits)) * '0')  # leading zeroes
        val += res                      # append lead zero with result
        val <<= left_shift              # left shift if lsch > 0
        # можно не сохранять - если значение надо интерпретировать перед сохранением
        if not bool_save:
            return val  # но тогда возвращать bitearray
        # в последовательность байтов   bres = val.tobytes() - только значащие байты, увы.
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
        self.byte(1)    # 1 бит на полигон/полилиния  # en_DRAW_TYPE
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
        """

        # /0/ WORD - ptr2string <--- word, ptr 2 zero-ended string
        # if 0 - zero tail ptr2table str
        flag_calc_ptr2tstr = self.unpack(BITS_IN_WORD, self.max_PTR_bits, 0) != '0000'
        
        # /1/ word, ptr 2 first vertex
        # запакованы не offs, а номера вертексов vertnum, 
        # т.е. off2vertex0 + 4*vertnum = offset распакованный
        # макс. число бит для архивированного значения - в vertex.cnt
        # -2: надо в 4 раза меньше бит, т.к. ptr vrtx кратен 4
        p_start_vrtx_num = self.unpack(BITS_IN_WORD, self.max_PTR_bits - 2, 0, False)  # не сохранять в result!  # noqa
        p_start_vrtx_num = ba2int(p_start_vrtx_num)     # номер 0-го vrtx объекта
        print(f"p_start_vrtx_num = {p_start_vrtx_num}")
        # 4* num = offset from start vertexes
        vrtx_off = self.start_vrtx_ptr + VERTEX.size * p_start_vrtx_num
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
        # WORD ptr_to_table_to_strings, unarc by calculate CURR_PTR_PTSTR +4 - next ptstr
        off_tstr = self.offset_tstr
        self.result += USHORT_struct.pack(off_tstr)
        self.offset_tstr += TSTR.size
        # ---- old
        # WORD ptr_to_table_to_strings, unarc by calculate CURR_PTR_PTSTR +4 - next ptstr
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
        i4_or_b_or_c = self.unpack(16, 16)        # '05 31  04 ac  3b 34 00 22  05 38   10 00'

        # /5/ > tstr_name     (0520 ????)
        #  bitarray('100011111000000000000000110000000000000000010000100000001110010
        self.pop(1)
        i5_p_tstr_name = self.unpack(16, 11)       # '05 31 04 ac 3b 34 00 22 05 38 10 00 f880'

        # /6/ > word or_38_or_0_b_country
        # 
        i6_or_38_or_0_b_country = self.unpack(16, 16)

        #==============================
        print(BYTESTRUCT(self.result))
        self.result.clear()
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
        id = self.unpack(32, 32)        #  = '05 31  04 ac  3b 34 00 22'

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
        self.result.clear()


        print(self.v_byte8)
        print(BYTESTRUCT(self.result))
        """
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



    def unpack_old(self, bit_goal:int, bit_compressed:int, left_shift:int=0, bool_save: bool=True) -> bytes:
        ''' Pop bit_compressed from buffer, left shift, extend to bit_goal. If bool_save self.result += bres'''
        if bit_goal not in (8, 16, 32):
            raise Exception(f"vdo_pack:unpack: Goal must be byte, word or dword, err qti bits:'{bit_goal}'\'")
        res = self.pop(bit_compressed) # pop bits from buffer 
        val = bitarray((bit_goal - (res.nbytes*8 - res.padbits)) * '0')  # leading zeroes
        #val = val.extend(res)
        val += res                      # append lead zero with result
        val <<= left_shift              # left shift if lsch > 0
        # можно не сохранять - если значение надо интерпретировать перед сохранением
        if not bool_save:
            return val  # но тогда возвращать bitearray
        
        # в последовательность байтов   bres = val.tobytes() - только значащие байты, увы.
        bres = val.tobytes()
        self.result += bres
        str_res = ''
        for h in bres:
            str_res += "{:02x}".format(h)   # str_res - for debug ))))
        return str_res #bres
    
    pass # class unpack_type_one():