"""
Базовый тип для геоданных - карты

"""

from vdo.block_base import block_base
from vdo.datatypes import BLADDR, LIST
from vdo.enums import en_GEO_CATEGORY       # , en_DRAW_TYPE
from vdo.geotypes import MAP_AREA, GEO_CATEGORY, GEO_SHAPE, GEO_LINE


OFFSET_LI_GEOCATEGORY = 0x08    # geodata types (categories)
OFFSET_LI_GEOSHAPE = 0x0c       # гео SHAPES - замкнутые полигоны
OFFSET_LI_GEOLINE = 0x10        # линии
OFFSET_LI_VERTEX = 0x14         # точки word, word
OFFSET_LI_POI = 0x18            # poi`s`
OFFSET_LI_TSTR = 0x1c           # ptrs tstr - индексы строк en_GEO_OBJ


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

    def __init__(self, addr: BLADDR) -> None:
        class toc:
            li_cat: LIST
            li_shp: LIST
            li_lin: LIST
            li_vrtx: LIST
            li_poi: LIST
            li_str: LIST
        super().__init__(addr)
        OFFSET_MAP_AREA = 0x20
        self.map = MAP_AREA(self.read(OFFSET_MAP_AREA, MAP_AREA.size))
        self.toc = toc()
        self.setup_toc()        # toc - table of contents
        
    def setup_toc(self):
        """
        Returns:

        """
        self.toc.li_cat = self.list(OFFSET_LI_GEOCATEGORY)
        self.toc.li_shp = self.list(OFFSET_LI_GEOSHAPE)
        self.toc.li_lin = self.list(OFFSET_LI_GEOLINE)
        self.toc.li_vrtx = self.list(OFFSET_LI_VERTEX)
        self.toc.li_poi = self.list(OFFSET_LI_POI)
        self.toc.li_str = self.list(OFFSET_LI_TSTR)

        # self.toc['li_cat'] = self.list(OFFSET_LI_GEOCATEGORY)
        # self.toc['li_shp'] = self.list(OFFSET_LI_GEOSHAPE)
        # self.toc['li_lin'] = self.list(OFFSET_LI_GEOLINE)
        # self.toc['li_ver'] = self.list(OFFSET_LI_VERTEX)
        # self.toc['li_poi'] = self.list(OFFSET_LI_POI)
        # self.toc['li_str'] = self.list(OFFSET_LI_TSTR)

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

    def category(self, offset: int) -> GEO_CATEGORY:
        """

        """
        buff = self.read(offset, GEO_CATEGORY.size * 2)
        res = GEO_CATEGORY(buff)
        return res

    def shape(self, offset: int, category: en_GEO_CATEGORY) -> GEO_SHAPE:
        """

        """
        buff = self.read(offset, GEO_SHAPE.size * 2)
        res = GEO_SHAPE(buff, category)
        # TODO
        if self.is_unpacked:
            res.name = self.read_str(res.ptr_str)
            # TODO read vertexes
        return res

    def line(self, offset: int, category: en_GEO_CATEGORY) -> GEO_LINE:
        """

        """
        buff = self.read(offset, GEO_LINE.size * 2)
        res = GEO_LINE(buff, category)
        # TODO
        if self.is_unpacked:
            res.name = self.read_str(res.ptr_str)
            # TODO read vertexes
        return res

    # -------------------------------------------
    def get_all_categories(self):
        """

        """
        res = []
        offset = self.toc.li_cat.ptr
        for i in range(self.toc.li_cat.cnt):
            res.append(self.category(offset))
            offset += GEO_CATEGORY.size

        return res
