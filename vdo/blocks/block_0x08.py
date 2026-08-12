"""
SCALE_ALMANAC = 0x08    # set of map folders 0x9.

Индекс папок с гео-блоками.
Описывает квадрат (в SCALE), количество итемов - папок (block_0x9),
дельта координат между папками, сам список папок

ALARM! количество items - не всегда квадрат стороны!

block_0x08

//header start
    BL_HEADER       block;
// header end, last = 0Ch -1
   DWORD folder_side_size <format=hex, fgcolor=cYellow,bgcolor=cDkGreen>;
   //was side_one_square_almanac
    
   FOLDER_MAPS folder[block.data.Cnt] <optimize=false>;

}BLOCK_TYPE_0x08

"""

from typing import Iterator, Tuple, Optional

from QGIS_VDO.vdo.block_base import block_base
from QGIS_VDO.vdo.blocks import block_0x09
from QGIS_VDO.vdo.datatypes import BLADDR
from QGIS_VDO.vdo.geotypes import COORD         # , MULCOORD
from QGIS_VDO.vdo.consts import struct_UINT     # , struct_2UINT, MOST_SIGNIFICANT_BIT


OFFSET_LIST_FOLDEFS = 0x08
OFFSET_FOLDER_SIZE = 0x0c


class block_0x08(block_base):
    """
    0x08    LIST     li_folders  ptr_cnt на BLADDR | 0
    0x0c    DWORD    side        размер приращения _hlat на следующий folder
    0x10    [BLADDR]             массив на папки-индексы гео-блоков
    """

    __slots__ = (
        'li_items',
        'item_side',
        'origin_hlon',
        'origin_hlat',
        'qty_y',
        'qty_x',
    )

    def __init__(self, bl_addr: BLADDR, origin: COORD, max: COORD) -> None:
        super().__init__(bl_addr)

        self.li_items = self.read_list(OFFSET_LIST_FOLDEFS)
        self.item_side = self.uint(OFFSET_FOLDER_SIZE)

        # Сохраняем сырые signed int32 значения для корректной CarInDB-математики
        self.origin_hlon = origin._hlongitude
        self.origin_hlat = origin._hlatitude
        
        # Вычисляем размеры сетки
        self.qty_y = (max._hlatitude - origin._hlatitude) // self.item_side
        self.qty_x = (max._hlongitude - origin._hlongitude) // self.item_side

        pass

    def items_cnt(self) -> int:
        """Возвращает количество уникальных итемов за O(N) через хеш-сет."""
        finded_early = set()
        raw_buffer = self._raw
        step = BLADDR.size
        start_ptr = self.li_items.ptr
        end_ptr = start_ptr + self.li_items.cnt * step

        for offset in range(start_ptr, end_ptr, step):
            val = struct_UINT.unpack_from(raw_buffer, offset)[0]
            if val:
                finded_early.add(val)
                
        return len(finded_early)

    def get_items(self) -> Iterator[Tuple[int, COORD, COORD]]:
        """Генератор валидных итемов с оригинальными объектами COORD.
        
        Возвращает:
            tuple: (bla_val, coord_lb, coord_rt)
        """
        finded_early = set()
        step = BLADDR.size
        base_ptr = self.li_items.ptr
        q_y = self.qty_y
        q_x = self.qty_x
        side = self.item_side
        raw_buffer = self._raw

        for x in range(q_x):
            # оригинальная индексация по qty_x
            x_offset = x * q_y
            
            # Рассчитываем долготу (X)
            hex_lon = (self.origin_hlon + x * side)
            hex_lon_next = (hex_lon + side)

            for y in range(q_y):
                curr_item = y + x_offset

                offset = base_ptr + step * curr_item
                bla_val = struct_UINT.unpack_from(raw_buffer, offset)[0]
                
                if not bla_val:
                    continue
                    
                if bla_val in finded_early:
                    raise ValueError(f"Дубликат bla_val {bla_val} обнаружен в сетке папок")
                
                finded_early.add(bla_val)

                # Рассчитываем широту (Y)
                hex_lat = (self.origin_hlat + y * side)
                hex_lat_next = (hex_lat + side)

                # Создаем тяжелые COORD только для валидных элементов (после всех continue)
                coord_lb = COORD(hex_lon, hex_lat)
                coord_rt = COORD(hex_lon_next, hex_lat_next)

                yield (bla_val, coord_lb, coord_rt)

    def _find_folder_by_coord(self, srch: COORD) -> Optional[Tuple[BLADDR, COORD, COORD]]:
        """ Поиск BLADDR block_0x08 по координатам srch"""
        # в "координатах" блока 0x08
        item_side = self.item_side
        x = (srch._hlongitude - self.origin_hlon) // item_side
        y = (srch._hlatitude - self.origin_hlat) // item_side

        # ОПТИМИЗАЦИЯ: Делаем проверку границ ОДИН раз прямо здесь
        if not (0 <= y < self.qty_y and 0 <= x < self.qty_x):
            return None
        
        # Теперь мы точно знаем, что x и y валидны, и можем читать данные напрямую
        item_num = y + x * self.qty_y
        offset = self.li_items.ptr + item_num * BLADDR.size
        folder_bladdr_val = struct_UINT.unpack_from(self._raw, offset)[0]
        
        if not folder_bladdr_val:
            return None
            
        # Рассчитываем координаты области без повторных проверок границ
        hex_lon = self.origin_hlon + x * item_side
        hex_lat = self.origin_hlat + y * item_side
        lb = COORD(hex_lon, hex_lat)
        rt = COORD(hex_lon + item_side, hex_lat + item_side)
        
        folder = self.vdo.get_bladdr(folder_bladdr_val)
        return folder, lb, rt

    def _get_xy_area(self, x: int, y: int) -> Optional[Tuple[COORD, COORD]]:
        """Возвращает оригинальные объекты COORD lb, rt для ячейки x, y."""
        # проверка на попадание в локальные координаты
        if y >= self.qty_y:     # вышел вверх за границу
            return None
        if y < 0:     # вышел вниз за границу
            return None
        if x >= self.qty_x:     # вышел вправо за границу
            return None
        if x < 0:     # вышел влево за границу
            return None
        
        side = self.item_side
        hex_lon = (self.origin_hlon + x * side)
        hex_lat = (self.origin_hlat + y * side)

        # В блоке 0х08 все ячейки 1х1
        return COORD(hex_lon, hex_lat), COORD((hex_lon + side), (hex_lat + side))

    def _get_xy_value(self, x: int, y: int) -> Optional[int]:
        """Вернуть int адрес папки по индексам сетки."""
        
        # проверка на попадание в локальные координаты
        if y >= self.qty_y:     # вышел вверх за границу
            return None
        if y < 0:     # вышел вниз за границу
            return None
        if x >= self.qty_x:     # вышел вправо за границу
            return None
        if x < 0:     # вышел влево за границу
            return None

        item_num = y + x * self.qty_y
        offset = self.li_items.ptr + item_num * BLADDR.size
        bladdr_val = struct_UINT.unpack_from(self._raw, offset)[0]
        
        if not bladdr_val:      # if 0 === None bladdr
            return None

        return bladdr_val
    
    def find_by_coord(self, srch: COORD) -> Optional[BLADDR]:
        """Поиск подблока карты, в который попадают координаты."""
        # Ищем в альманахе папку карт
        b_09 = self._find_folder_by_coord(srch)

        if b_09 is None:
            return None

        bl, c1, c2 = b_09
        # загружаем папку карт - индекс maps
        bl_folder: block_0x09 = self.vdo.get_block(bl, c1, c2)

        return bl_folder.find_by_coord(srch)    # тут будет чистый map, только BLADDR

 
# All block tests in block_0x07
#05154A03 0008 00 00 [08:SCALE_ALMANAC]

# -------------------------------------------------------------------------

if __name__ == '__main__':
    # from vdo.datatypes import VDO_FILE
    from QGIS_VDO.vdo.fixtures_vdo import vdo30, vdo34ee, vdobmv, vdo34bnl, vdoRu  # noqa
    from QGIS_VDO.vdo.consts import struct_UINT        # noqa

    # block(0x55D7201);   // EE scale 7 0x16 arch=0 near SPb
    # block(0x55D6903);   // EE scale 7 0x16 arch=1 near SPb

    vdo = vdo30
    vdo = vdo34ee
    # vdo = vdobmv
    # vdo = vdo34bnl
    # vdo = vdoRu

    # test get_items ---------------------------------------------------------------------
    from QGIS_VDO.vdo.blocks import block_0x12, block_0x07

    bl_toc: block_0x12 = vdo.get_block(0)
    bl_scales: BLADDR = bl_toc.bladdr_scales

    block_07: block_0x07 = vdo.get_block(bl_scales)
    del bl_toc, bl_scales

    scale = block_07.scales[2]        # 5, 10, 11 - 1x1, 2-8x8
    # scale = block_07.scales[11]
    lb, rt = scale.area     # (10.636742S 36.299691W, 86.000050N 60.337100E)

    block_almanac: block_0x08 = vdo.get_block(scale.almanac_idx, lb, rt)  # noqa
    srch_spb = COORD(bytes.fromhex('13F919BE13DA074C'))
    srch_zagreb = COORD(15.9780, 45.8144)      # 45.8144° северной широты, 15.9780° восточной долготы. '0F399A2D0F2BBBD5' # noqa
    srch_bucurest = COORD(26.1063, 44.4323)      #  44.4323° N, 26.1063°E . '1294304B0EB69259' # noqa
    bl_09_spb = block_almanac._find_folder_by_coord(srch_spb)   # sc=5: 0x570e705; sc=2  5,5 (0x05118c01) 0x05119602
    bl_09_zgr = block_almanac._find_folder_by_coord(srch_zagreb)   # sc=5: 0x570e705; sc=2  4,4  0x05118c01
    bl_09_buc = block_almanac._find_folder_by_coord(srch_bucurest)   # sc=5 (0x0570e601): 0x570e705; sc=2 (0x05118c01) 5,4 0x5119402 # noqa

    alm_item_cnt = block_almanac.items_cnt()
    
    # block_08 content
    print(f"block_08: 0x{block_almanac} block_0x09 : x : y")
