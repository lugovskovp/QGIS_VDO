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
from vdo.consts import struct_UINT, struct_WORD, struct_WORD_TWICE    # BYTE_struct,
from vdo.consts import BITS_IN_ASCII, LOOKUP_CHARS


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
            self.beg_arch_word_A = struct_WORD.unpack(barray[OFFSET_PACKED_DATA:OFFSET_PACKED_DATA + 2])[0]  # noqa 
            # ?
            self.beg_arch_word_B =  struct_WORD.unpack(barray[OFFSET_PACKED_DATA + 2:OFFSET_PACKED_DATA + 4])[0]  # noqa 
            # остальное в buffer - поток битов, которые будем распаковывать
            buffer = bitstream(barray[OFFSET_PACKED_DATA + 4:],  # + unk_beg_arch_dword # noqa
                               OFFSET_PACKED_DATA,   # вот с этого офсета будем заполнять
                               self.max_PTR_bits(),
                               self.toc.li_vrtx.ptr,  # не ошибка, нужен offset vrtx
                               self.toc.li_tstr)       # и list tstr тоже надо

            # суммарная уже известная на данный момент информация
            self.show_main_info()

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
                # Для каждого шейпа (полигона) из toc.list_shape:
                for _ in range(self.toc.li_shp.cnt + 1):     # +1 - всегда есть завершающий итем, нулевой # noqa
                    buffer.unpack_shape()
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
                
                """
                # а пока что не реализовано
                raise ValueError("toc.li_lin: ", self.toc.li_lin, " но GEO_LINE еще не реализован")
                pass

                for _ in range(self.toc.li_lin.cnt + 1):     # +1 - всегда есть завершающий итем, нулевой # noqa
                    buffer.unpack_line()
                    # ------------------------------ <debug

                    # ------------------------------ debug>
                    self._raw += buffer.result
                    buffer.clear_result()

            # <<<<<<<<<< POI
            if self.toc.li_poi.cnt:
                # а пока что не реализовано
                raise ValueError("toc.li_poi: ", self.toc.li_poi, " но POI еще не реализован")

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
                            hex_val += f"{struct_WORD.unpack(last_vals[i:i+2])[0]:04x} "
                        # print(f"{head_offs:04x}: {hex_val}")
                    # ==================== debug print last 10h values

                # ==================== debug print last 10h values
                las_vrtxes = self.data_size - head_offs - 0x10
                head_offs = head_offs + 0x10
                last_vals = self._raw[head_offs:]
                hex_val = ''
                for i in range(0, las_vrtxes, 2):
                    hex_val += f"{struct_WORD.unpack(last_vals[i:i+2])[0]:04x} "
                # debug
                # print(f"{head_offs:04x}: {hex_val}")
                # ==================== debug print last 10h values
                pass
            
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
                print(f"\n{unpacked_bin_strings}\n")

                # <<<<<<<<<< TSTRs
                """
                    # noqa
                    071515 04  BlockType.MAP__10k400: 0x1d
                    Max PTR bits: 12
                самый хвост
                    0000000000000000000000000000000000000000001100011000000100010101100000110001101001100110001110010100110001111011000100010110001000101101010001011100100010111101000110000000000000000000000000000000000000000000000000000000

                    8c0 15 00   delta 13/19
                    1 100011000000 1 00010101 1 00000    1100011000000100010101100000 
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
                # убрать незначащие лидирующие 0
                marker_TSTR = '0000000000000001'
                find = buffer.buffer.find(bitarray(marker_TSTR)) + len(marker_TSTR) - 1
                del marker_TSTR
                buffer._pop(find)   
                del find
                
                # распаковка
                s_ptr = '0'
                s_lang = '0'
                s_type = '0'
                for _ in range(self.toc.li_tstr.cnt):
                    # ptr_2_str
                    if ba2int(buffer._pop(1)):
                        s_ptr = buffer._unpack_ptr()
                    # language
                    if ba2int(buffer._pop(1)):
                        s_lang = buffer._unpack_byte(8)
                    # type
                    if ba2int(buffer._pop(1)):
                        s_type = buffer._unpack_byte(5)
                    # ------------------------- debug
                    print(f"{buffer.av_offs}: {s_ptr} {s_lang} {s_type}")
                    # ------------------------- debug
                    

            self._raw += buffer.result
            buffer.clear_result()

            # texts
            self._raw += unpacked_bin_strings

            # собственно оставшееся в буфере можно и не распаковывать
            # там окончание куда tstr раскидывать
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
        print(f"   strs from {self.toc.START_TXT:04X}")
        print(f"begin word = {self.beg_arch_word_A:04X}:{self.beg_arch_word_B:04X}")
        print(f"Map_hex: {self.map.hex}")
        print(f"{self.map}")
        print(f"Максимальные Х и У: {self.max_bounds} \n")
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
        self.offset_tstr = li_tstr.ptr    # tstr стартует с этого смещения, каждый объект - + 1  # noqa
        self.counter_tstr_table_str = 0
        # для распаковки vertexes по префиксам
        self.BITS_TO_READ = {'00' : 8,       # 8
                            '01' : 8,        # 8
                            '10': 9,         # прочитать 9 бит, вычесть значение из предыдущего
                            '11': 16         # 16 считать все 16 бит, как значение. []
                            }
        pass
    
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
    def v_byte07(self):
        res = self._touch(7)
        #res = self.unpack(8, 7, 0, False)
        return ba2int(res)

    @property
    def v_byte08(self):
        res = self._touch(8)
        #res = self.unpack(8, 8, 0, False)
        return ba2int(res)

    @property
    def v_word15(self):
        res = self._touch(15)
        return ba2int(res)

    @property
    def v_word16(self):
        res = self._touch(16)
        return ba2int(res)

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
    
    def _unpack_word(self, bit_compressed: int=BITS_IN_WORD) -> str:
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

    def _unpack_uint(self, bit_compressed: int=BITS_IN_UINT) -> str:
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
        """
        str_res = self._unpack(BITS_IN_WORD, self.max_PTR_bits, left_shift)
        return str_res

    def _unpack_vertex_offset(self) -> int:
        """
        Упакованы не смещения, а номера вертексов в общем списке.
        """
        # номер самого первого, 0-го vrtx объекта не сохранять в result!  # noqa
        # -2: надо в 4 раза меньше бит, т.к. ptr vrtx кратен 4 -> self.max_PTR_bits - 2
        start_vrtx_num = ba2int(self._unpack(BITS_IN_WORD, self.max_PTR_bits - 2, 0, False)) 
        # offset from start vertexes = размер вертекса * на номер 
        # и прибавить к offset самого первого вектора
        vrtx_off = self.start_vrtx_ptr + VERTEX.size * start_vrtx_num
        # ========================== debug
        print(f"start_vrtx num: {start_vrtx_num} offset: {vrtx_off:04x}")
        # ========================== debug
        # vertx offs word, save
        self.result += struct_WORD.pack(vrtx_off)  
        return vrtx_off

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
        bits_to_read = 9   # wtf? why?
        prefix = self._pop(2).to01()
        # bits_to_read = self.BITS_TO_READ[prefix]
        
        if prefix == '11':
            # load full short
            res = self._unpack_word()
            return res

        if prefix == '10':
            # read 9 бит, вычесть значение из предыдущего
            val = -ba2int(self._unpack(BITS_IN_WORD, bits_to_read, 0, False))

        elif prefix == '01':
            # read 8 бит, и +добавить 9й
            val = ba2int(self._unpack(BITS_IN_WORD, bits_to_read - 1, 0, False))
            val = 0b100000000 | val

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
        self._unpack_byte(BITS_IN_CATEGORY_TYPE)    # 7 bit на 
        
        # en_GEO_CATEGORY
        # /1/
        self._unpack_byte(1)    # 1 бит на полигон0/полилиния1  
        
        # en_DRAW_TYPE
        # /2/
        # left shift 1 - т.к. last = 0 always in this ptr
        self._unpack_ptr_word(1)    # максимальное к-во бит для near ссылки word

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
        # /0/ WORD - ptr2string <--- word, ptr to zero-ended string
        # if 0 - zero tail ptr2table str -- вот кстати вопрос - на точно ли так надо ваще????
        # flag_calc_ptr2tstr = self.unpack(BITS_IN_WORD, self.max_PTR_bits, 0) != '0000'
        flag_increment_ptr2tstr = self._unpack_ptr() != '0000'
        """
        begin word = 0500:0900   self.ptr()
        WORD - ptr2string
        tst 08B0:0004 cnt:4     next ptr: 8c0  strs from 08c0  100011000000  max_PTR_bits=12
        '100011000000 0000000000 101000000000000011'
        """

        # /1/ word, ptr 2 first vertex
        # запакованы не offs, а номера вертексов vertnum,
        #       v_off = self._unpack_vertex_offset()

        # -2: надо в 4 раза меньше бит, т.к. ptr vrtx кратен 4 -> self.max_PTR_bits - 2
        start_vrtx_num = self._unpack(BITS_IN_WORD, self.max_PTR_bits - 2, 0, False)  # не сохранять в result!  # noqa
        start_vrtx_num = ba2int(start_vrtx_num)     # номер 0-го vrtx объекта
        # 4* num = offset from start vertexes
        vrtx_off = self.start_vrtx_ptr + VERTEX.size * start_vrtx_num
        print(f"start_vrtx num: {start_vrtx_num} offset: {vrtx_off:04x}")
        self.result += struct_WORD.pack(vrtx_off)     # vertx offs 2word, save


        # ========================== debug
        # print(f"start_vrtx num: {start_vrtx_num} offset: {vrtx_off:04x}")
        # ========================== debugt

        # /2/  dword, id
        #self._pop(1)
        #id - если следующий бит = 1, ЕСТЬ ID, иначе пропустить
        if self._pop(1) == bitarray('1'):
            self._unpack_uint()
        else:
            # id в архиве нет, ID = 00 00 00 00
            self.result += b'\x00' * 4
        """
        ptr2string, ptr2firstVertex, id
        begin word = 0500:0900   self.ptr(), calc_vrtx_offs, 

        '1 010000000000000110001 101000000000011111'
        """

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
        off_tstr = self.offset_tstr
        self.result += struct_WORD.pack(off_tstr)
        if flag_increment_ptr2tstr:
            self.offset_tstr += TSTR.size

    def unpack_line(self) -> None:
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

                c:/DIY/VDO/db_src/ru_2013/ru/carindb
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
        # '10100110001 10000010000111011001101000000' '1010011000110000010000111011001101000000'
        # p_str_name = 05 31
        i0_p_str_name = self._unpack_ptr()
        # '0531 ' cool! 520 + len 'mar mediterráneo' +\x00

        # /1/  ptr_vrtx ?? shp:009C-04AC,  lines=4ac-0518 010010101100 100101011 - 010100011000 101000110
        # 104 000100000100
        # vrtx_num = 260 dec | 104h
        # vrtx_off = 04 ac
        # self._pop(1)
        start_vrtx_num = self._unpack(BITS_IN_WORD, self.max_PTR_bits - 2, 0, False)  # не сохранять в result!  # noqa
        start_vrtx_num = ba2int(start_vrtx_num)     # номер from 0-го vrtx объекта
        print(f"line: start_vrtx_num = {start_vrtx_num}/0x{start_vrtx_num:02x}")
        # 4* num = offset from start vertexes
        vrtx_off = self.start_vrtx_ptr + VERTEX.size * start_vrtx_num
        self.result += struct_WORD.pack(vrtx_off)     # vertx offs 2word, save
        # '0531 04ac ' cool! 04ac as tail shp, bingo
       

        # /2/ > word id ?? (есть ли проверка на существование?
        # и есть ли макс ид для линий?)
        # mar mediterráneo id= 40045aa0 = mar mediterráneo
        #k = self._pop(1)
        if True or k != '1':
            #
            i2_id = self._unpack_uint()        # map = '08B9 3000 0B9A 5000  0919 3000 0BFA  5000'\
                                               # 35.039236N 3.656246W  36.171698N 2.523783W
        else:
            i2_id = '0'
            self.result += b'\x00' * 4
        # '0531 04ac 3b340022'
        # '05 31 04 ac ec d0 00 89' + _pop(2) - 00
        pass

        # /3/ > tstr_regi > tst 0518  (? < str 0520 ??)  <<2, т.к. сразу за vortex
        # 518 0 101000110 00 -> 520
        # 51c 0 101000111 00 -> 531
        # 520 0 101001000 00 
        # 531 0 10100110001
        # 538 '1010011100000010000000000001000111110000'
        #   i_z = self._pop(2) 400c 0100000000001100
        # '0111011001101000000000000100010011010011'
        # i3_p_tstr_regi = self._unpack_ptr_word()         # unpack(16, 11)
        self._pop(2)  # 01
        i3_p_tstr_regi = self._unpack_ptr()         # unpack(16, 11)
        pass
        # '0538' -like ptr 2 string - but early _pop 00
        # 00111011001101000000000000100010
        # 01101001110000001000000000000100011111000000000000000110000000000000000010000100000001110010110100101100000000000100 101000110 010110110100010011110001001010101110001010101101011100110011010011010110 101000111 0000110001111010000100100111000001001110000000110011001001111110100101001001110001011001101111100011001111001001110000101010100001100011101100110101001101010110011001100001011110000000011110110011011100010111110001101100100111111010011110011100101110001

        # /4/ > word or_b_or_c - какое-то число?
        # '0001000000000000 100011111000000000000000'
        i4_or_b_or_c = self._unpack_word()        # '05 31  04 ac  3b 34 00 22  05 38   10 00'  # noqa

        # /5/ > tstr_name     (0520 ????)
        #  '1000111110000000000000001100000000000000'
        self._pop(1)
        i5_p_tstr_name = self.unpack(16, 11)       # '05 31 04 ac 3b 34 00 22 05 38 10 00 f880'  # noqa

        # /6/ > word or_38_or_0_b_country
        # у границ = 0? 67
        i6_or_38_or_0_b_country = self.unpack(16, 16)

        #==============================
        print(BYTESTRUCT(self.result))
        self.clear_result()
        self._unpack(16, 12)     # 12? max_PTR_bits = 11  или << а след бит - флаг?

        # /1/  ptr_vrtx ?? == 04ac?  num 260 dec | 104h
        start_vrtx_num = self._unpack(BITS_IN_WORD, self.max_PTR_bits - 2, 0, False)  # не сохранять в result!  # noqa
        start_vrtx_num = ba2int(start_vrtx_num)     # номер from 0-го vrtx объекта
        print(f"start_vrtx_num = {start_vrtx_num}")
        # 4* num = offset from start vertexes
        vrtx_off = self.start_vrtx_ptr + VERTEX.size * start_vrtx_num
        self.result += struct_WORD.pack(vrtx_off)     # vertx offs 2word, save

        # /2/ > word id ?? (есть ли проверка на существование?)
        # bitarray('00111011001101000000000000100010')
        id = self._unpack(32, 32)        # = '05 31  04 ac  3b 34 00 22'

        # /3/ > tstr_regi > tst 0518  (? < str 0520 ??)
        # bitarray('01 10100111000 00010
        i_z = self._pop(2)
        i_tstr_regi = self._unpack(16, 11)

        # /4/ > word or_b_or_c - какое-то число?
        # bitarray('0001000000000000 1000111110000000000000001100000000
        ior_b_or_c = self._unpack(16, 16)

        # /5/ > tstr_name     (0520 ????)
        #  bitarray('100011111000000000000000110000000000000000010000100000001110010
        i_tstr_name = self._unpack(16, 16)

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

    def unpack_str(self) -> bytes:
        """
        Распаковывает строку
        Returns:
            bin_str: бинарное представление строковой части zero-ended строк 
        """
        # первыми 2 ptr - начало и окончание строки
        ptr_start = int(self._unpack_ptr(), 16)
        ptr_end = int(self._unpack_ptr(), 16)
        strings_length = ptr_end - ptr_start
        del ptr_end
        del ptr_start
        
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
            val = ''
            for _ in range(n):
                # и грузятся ascii коды по 7 бит
                ch = chr(ba2int(self._pop(BITS_IN_ASCII)))
                val += ch
                # ba = self._pop(BITS_IN_ASCII)
                # bi = ba2int(ba)
                # bb = ba.tobytes()
                # bch = struct_BYTE.unpack(bb)[0]
                # print(bch)
                # #ch_code = ba2int()
                # ch = chr(bi)
                # # bch = struct_BYTE.pack(ch_code)
                # val += ch
                pass
            preambula[f"{k:07b}"] = val

        # и вот только теперь пошли буквы, закодированные ....эммм.
        # .. хафманом, но с нюансами
        res = ''
        for _ in range(strings_length):
            prefix = self._pop(2)
            if prefix.to01() == '11':
                ba = self._pop(BITS_IN_ASCII)
                if ba.to01() in preambula:
                    # о, сокращённенькое из преамбулы
                    pre_chars = preambula[ba.to01()]
                    # но если из преамбулы возвращается А
                    if pre_chars == 'A':
                        res += chr(ba2int(ba))
                    else:
                        res += pre_chars
                else:
                    # или ascii код буквы
                    res += chr(ba2int(ba))
                continue        # всё, данные итерации загружены
            elif prefix.to01() == '00':
                prefix += self._pop(1)
            elif prefix.to01() == '01':
                prefix += self._pop(2)
            else:       # elif prefix.to01() == '10':
                prefix += self._pop(3)
            # вытаскиваем, что получилось, из дерева и добавляем к результату
            res += LOOKUP_CHARS[prefix.to01()]
        # всё, упакованные буквы окончились

        # подрезать хвосты - по длинне могло подрасти из-за использования преамбулы
        bin_str = res.encode('cp1251')
        bin_str = bin_str[:strings_length]
        # res = bin_str.decode('cp1251')
        return bin_str

    pass   # class unpack_type_one():
