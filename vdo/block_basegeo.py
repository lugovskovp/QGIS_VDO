"""
block_basegeo - Базовый тип для - карт   00 16 15 1c 14 1d 1e # noqa: E116
bitstream - class wrapper for bitarray
"""
from bitarray import bitarray   # https://pypi.org/project/bitarray/
# https://github.com/ilanschnell/bitarray/blob/master/doc/buffer.rst


from vdo.block_base import block_base
from vdo.datatypes import BLADDR, LIST
from vdo.enums import en_GEO_CATEGORY, en_DRAW_TYPE
from vdo.geotypes import MAP_AREA, GEO_CATEGORY, GEO_SHAPE, GEO_LINE, VERTEX
from vdo.datatypes import UINT_struct


OFFSET_LI_GEOCATEGORY = 0x08    # geodata types (categories)
OFFSET_LI_GEOSHAPE = 0x0c       # гео SHAPES - замкнутые полигоны
OFFSET_LI_GEOLINE = 0x10        # линии
OFFSET_LI_VERTEX = 0x14         # точки word, word
OFFSET_LI_POI = 0x18            # poi`s`
OFFSET_LI_TSTR = 0x1c           # ptrs tstr - индексы строк en_GEO_OBJ

OFFSET_ACHIVED_DATA = 0x34  # ТИПЫ БЛОКОВ archived type_1_vdo_pack
                            # bmw ee bnl:  00 16 15 1c 14 1d 1e # noqa: E116
                            # в них незапакованы первые 0х34 # noqa: E116


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

    shapes = []
    lines = []
        
    def __init__(self, addr: BLADDR) -> None:
        class toc:
            li_cat: LIST
            li_shp: LIST
            li_lin: LIST
            li_vrtx: LIST
            li_poi: LIST
            li_str: LIST
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
            self._raw = barray[:OFFSET_ACHIVED_DATA]    # до 0x34 - не запакованы, потом идёт непонятный ?? DWORD # noqa
            # 83888384 = 5000 9000
            self.unk_beg_arch_dword = self.hex(UINT_struct.unpack(barray[OFFSET_PACKED_DATA:OFFSET_ACHIVED_DATA + 4])[0])  # noqa
            # Всё остальное в buffer - поток битов, которые надо распаковать
            buffer = bitstream(barray[OFFSET_ACHIVED_DATA + 4:])  # + unk_beg_arch_dword
            # привести в порядок значения unpacked размера?
            #  or not ?self.size = self._const_segsize * self.unarc_segcnt
            
            # локально константами
            BYTE_BITS = 8
            USHORT_BITS = 16
            UINT_BITS = 32
        # всё содержимое
        self.setup_all_objects()
        
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
        self.toc.li_str = self.list(OFFSET_LI_TSTR)

    def setup_all_objects(self) -> None:
        """
        Заполняет self.obj_lines и self.obj.shapes
        """
        cat: GEO_CATEGORY
        for cat in self.get_all_categories():
            if cat.draw == en_DRAW_TYPE.SHAPE:
                #step_ptr = GEO_SHAPE.size
                func = self.shape
                arr = self.shapes
            else:       # en_DRAW_TYPE.LINE
                #step_ptr = GEO_LINE.size
                func = self.line
                arr = self.lines
            step_ptr = cat.obj_size
            for ptr in range(cat.ptr,
                             cat.ptr + step_ptr * (cat.cnt),  # -1: самый последний элемент - нулевой # noqa
                             step_ptr):
                arr.append(func(ptr, cat))


            # step_ptr = GEO_SHAPE.size if cat.draw == en_DRAW_TYPE.SHAPE else GEO_LINE.size
            # func = self.line

            # ptr_obj = cat.ptr
            # for obj in range(cat.)
            # if cat.draw == en_DRAW_TYPE.SHAPE:
            #     line = self.line(ptr_obj)
            #     self.lines.append(line)
            #     ptr_obj += GEO_LINE.size
            # else:
            #     shape = self.shape(ptr_obj)
            #     self.shapes.append(shape)
            #     ptr_obj += GEO_SHAPE
            print(cat)

    def category(self, offset: int) -> GEO_CATEGORY:
        """

        """
        res = None
        if self.is_unpacked:
            buff = self.read(offset, GEO_CATEGORY.size * 2)
            res = GEO_CATEGORY(buff)
        return res

    def shape(self, offset: int, category: en_GEO_CATEGORY) -> GEO_SHAPE:
        """

        """
        res = None
        if self.is_unpacked:
            buff = self.read(offset, GEO_SHAPE.size * 2)
            res = GEO_SHAPE(buff, category)
            res.name = self.read_str(res.ptr_str)
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

    def line(self, offset: int, category: en_GEO_CATEGORY) -> GEO_LINE:
        """

        """
        res = None
        if self.is_unpacked:
            buff = self.read(offset, GEO_LINE.size * 2)
            res = GEO_LINE(buff, category)
            # TODO
        
            res.name = self.read_str(res.ptr_str)
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

    def __init__(self, barray: bytes) -> None:
        self.buffer = bitarray(buffer=barray, endian='big').copy()    # copy - else read only memory # noqa
        self.result = bytearray()   # empty
        pass

    @property
    def res(self):
        ''' online see result values'''
        return " ".join("{:02x}".format(c) for c in self.result)
    
    def pop(self, qty_bits: int) -> bitarray:
        '''pop from begin (left) buffer qty bites'''
        val = self.buffer[:qty_bits]
        del self.buffer[:qty_bits]
        return val

