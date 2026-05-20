''' Enumerate values in one place '''
import enum

'''
BlockType
    en_CARINET_LANGUAGE
    en_POI_CATEGORY
    en_GEO_CATEGORY
    en_DRAW_TYPE
    en_GEO_COUNTRY
'''


@enum.unique
class BlockType(enum.Enum):
    ''' Known block types '''
    ABSTRACT = 0x12
    BIBLIOGR = 0x13
    SCALES = 0x07

    CH_country = 0x0b  # fully parsed chars idxs
    COUNTRY = 0x0a  # fully parsed COUNTRY INFO
    CH_city = 0x0d  # fully parsed chars idxs
    CITY = 0x0c  # fully parsed CITY INFO
    CH_road = 0x0f  # fully parsed chars idxs
    ROAD = 0x0e  #
    CH_poi = 0x11  # fully parsed chars idxs
    POI = 0x10  # fully parsed, POI
    
    SCALE_ALMANAC = 0x08    # set of map folders 0x9.
    FOLDER_MAPS = 0x09		# map folders 0x9.
    MAP__POLI_1 = 0x06  # scale 1
    MAP__POLI_2 = 0x01  # scale 2
    MAP__POLI_3 = 0x02  # scale 3
    MAP__POLI_4 = 0x03  # scale 4
    MAP__05k200 = 0x14  # scale 5   14_MAP_POLI_5_k200	//[5] 5(9:200h)-0x14
    MAP__06k80 = 0x15  	# scale 6   15_MAP_POLI_6_k80	//[6] 6(7:80h)-0x15
    MAP__07k40 = 0x16  	# scale 7   16_MAP_POLI_7_k40	//[7] 7(6:40h)-0x16
    #						#								//[8] - всегда всё 0.
    MAP__09k100 = 0x1c  # scale 9   1c_MAP_POLI_9_k100	//[9]  9(8:100h)-0x1c
    MAP__10k400 = 0x1d  # scale 10  1d_MAP_POLI_10_k400 //[10] a(a:400h)-0x1d
    MAP__11k_11 = 0x1e  # scale 11  1e_MAP_POLI_11			//[11] b(b:666h)-0x1e

    UNKN = 0xFF  # если тип блока ещё не описан

    bl_0x0 = 0x0
    bl_0x4 = 0x4
    bl_0x17 = 0x17
    bl_0x18 = 0x18
    
    # EMPTY = BLOCK_TYPE_EMPTY_ENTRY    # value may be '00 00 00 00' - its legal, but
    # empty, must not read
    # UNKN  = BLOCK_TYPE_UNKNOWN
    # ТИПЫ БЛОКОВ archived by zlib in bmw:
    # 17 1E 09 1D 14 1C 15 16 01 02 03 04 00 06 10 11 0E 0F 0C 0D 0A 13
    # 17 *1E *09 *1D *14 *1C *15 *16 *01 *02 *03
    #  04 00 *06 *10 *11 *0E *0F *0C *0D *0A *13
