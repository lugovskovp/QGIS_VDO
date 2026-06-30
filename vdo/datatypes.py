"""

классы:
VDO_FILE
BYTESTRUCT
BL_ADDR  DWORD, Структура адреса блока
PTR      WORD near - указатель
LIST
FAR_LIST
CH_IDX
BLSTART
"""

import os.path
import struct
import importlib
import heapq

from .enums import BlockType
from .consts import struct_WORD, struct_UINT
from .consts import USHORT_BYTES_CNT, UINT_BYTES_CNT, DOUBLE_BYTES_CNT, ZERO_DWORD

OFFSET_TOC = 0x08

DEFAULT_DB_REVISION = 0x1e
DEFAULT_ONE_SEG_SIZE = 0x800
OFFSET_ONE_SEG_SIZE = 0x2c
OFFSET_DB_REVISION = 0x1a

MAX_STR_LEN = 63    # 255


def setup_known_types():
    """ """
    # 'C:\\Work\\QGIS_VDO\\vdo'
    plugin_dir = os.path.dirname(os.path.realpath(__file__))
    # 'C:\\Work\\QGIS_VDO\\vdo\\blocks'
    dirname = os.path.join(plugin_dir, "blocks")
    # список файлов в директории - только файлы
    files = [f for f in os.listdir(dirname) if os.path.isfile(os.path.join(dirname, f))]
    # оставить только файлы, начинающемися на 'block_', без расширений [0:-3]
    block_files = [f[0:-3] for f in files if f[0:6] == 'block_']
    # 'block_0x0B', 'block_0x12' ...
    # '0x0B' '0x12' '0x13' '0xEE' - block types
    known_types = dict([(int(t[-4:], 16), t) for t in block_files])
    # {(11, 'block_0x0B'), (18, 'block_0x12'), (19, 'block_0x13')...}
    return known_types


# создается список блоков, для которых уже есть классы
KNOWN_BLOCKS = setup_known_types()


# ----
class VDO_FILE():
    """ класс работы с файлом формата carindb """
    path: os.path
    # :path: full filepath, os.path or None
    dbrev: int
    """:dbrev: database revision, 30 (0x1e) or 34 (0x22)"""
    segsize: int    # :segsize: size of one segment in chank

    def __init__(self, path: os.path = None) -> None:
        """ """
        if path:
            self.path = path
            self.dbrev = struct_WORD.unpack(self.read(OFFSET_DB_REVISION, 2))[0]
            self.segsize = struct_WORD.unpack(self.read(OFFSET_ONE_SEG_SIZE, 2))[0]
            return
        self.empty()

    def __repr__(self):
        s = f'VDO v.{self.dbrev}[{self.segsize}]:{self.path}'
        return s

    def read(self, offset: int, size: int) -> bytearray | None:
        """ Return bytearray[size] from self.path.offset
        Args:
            offset: offset in file path
            size:    bytes in result bytearray
        Returns:
            bytearray[size]: from self.path.offset
        """
        with open(self.path, 'rb') as f:
            f.seek(offset)
            return f.read(size)
        return None

    def get_block(self, addr: int) -> object:
        """
        Возвращает блок по offset addr или из BLADDR adr
        Args:
            addr: int offset | BLADDR block address
        Returns:
            Block: block base structure needed type (if possible)
        """
        if type(addr) is int:
            offset = addr
        elif type(addr) is BLADDR:
            if not struct_UINT.unpack(addr._raw)[0]:       # == 0
                # raise ValueError(addr, " bladdr 00 00 00 00")
                return None
            offset = addr.offset
        else:
            # только offset начала блока или BLADDR
            raise ValueError(addr, " Тип не int и не bladdr")
        head = BLSTART(self.read(offset, BLSTART.size), self)
        if head.bladdr.offset != offset:
            # а это и не блок вовсе
            return None
        # а описан ли тип этого блока?
        if head.bltype.value in KNOWN_BLOCKS.keys():
            bl = KNOWN_BLOCKS[head.bltype.value]
            # импорт класса bl из модуля
            bl_class = getattr(importlib.import_module('.blocks.' + bl, package="QGIS_VDO.vdo"), bl)  # noqa
            bl_class.type = head.bltype.value
            bl_class.type_name = bl
        else:
            # no this type in known blocks
            bl_class = getattr(importlib.import_module('.vdo.block_base'), 'block_base')
            #return block_base(head.bladdr, self)
            bl_class.type = head.bltype.value
            bl_class.type_name = 'block_base'
            pass
        #
        bl_instance = bl_class(head.bladdr)
        return bl_instance

    def get_huffman_weights(self) -> dict:
        """
        в первом блоке, 0х12 есть таблица весов для дерева хаффмана
        по смещению OFFSET_MAY_BE_HUFFMAN_THREE = 0x28 list(ptr|cnt)\n
        Таблица одна на весь файл - и логично не привязывать её к блоку
        Returns:
            weight: dict {key_id : value_weight}
        """
        OFFSET_SEEMS_LIKE_HUFFMAN_WEIGHTS = 0x28
        # начальный адрес таблицы весов и количество элементов.
        HUFFMAN_PAIR_SIZE = 4
        struct_WORD_TWICE = struct.Struct(">HH")

        weights = {}
        bytes_list = self.read(OFFSET_SEEMS_LIKE_HUFFMAN_WEIGHTS, HUFFMAN_PAIR_SIZE)
        (ptr, cnt) = struct_WORD_TWICE.unpack(bytes_list)
        for _ in range(cnt):
            (key_id, value_weight) = struct_WORD_TWICE.unpack(self.read(ptr, HUFFMAN_PAIR_SIZE))   # noqa
            #if 0 <= key_id <= 0xFFFF:
            # Нам нужны только символы с реальным весом > 0
            if value_weight > 0:
                weights[key_id] = value_weight
            ptr += HUFFMAN_PAIR_SIZE
        return weights

    def generate_canonical_lookup(self, weights_table):
        """Строит каноническую lookup-мапу: { бинарная_строка: int_байт }"""
        full_weights = {b: 1 for b in range(256)}
        #for key_hex, weight in weights_table.items():
        for byte_id, weight in weights_table.items():
            try:
                #byte_id = int(key_hex, 16)
                if 0 <= byte_id <= 255:
                    full_weights[byte_id] = weight
            except ValueError:
                continue

        heap = []
        counter = 0
        for byte_id, weight in full_weights.items():
            heapq.heappush(heap, (weight, counter, {'id': byte_id, 'left': None, 'right': None}))  # noqa
            counter += 1

        while len(heap) > 1:
            w1, _, n1 = heapq.heappop(heap)
            w2, _, n2 = heapq.heappop(heap)
            heapq.heappush(heap, (w1 + w2, counter, {'id': None, 'left': n1, 'right': n2}))  # noqa
            counter += 1

        _, _, root_node = heapq.heappop(heap)
        code_lengths = {}
        
        def collect_lengths(node, current_depth):
            if node['id'] is not None:
                code_lengths[node['id']] = current_depth
                return
            if node['left']: collect_lengths(node['left'], current_depth + 1)  # noqa
            if node['right']: collect_lengths(node['right'], current_depth + 1)  # noqa

        collect_lengths(root_node, 0)
        sorted_elements = sorted(code_lengths.items(), key=lambda x: (x[1], x[0]))

        canonical_lookup = {}
        current_code_int = 0
        last_length = 0

        for byte_id, length in sorted_elements:
            if length == 0: continue  # noqa
            if last_length > 0:
                current_code_int <<= (length - last_length)
            bit_code = f"{current_code_int:0{length}b}"
            canonical_lookup[bit_code] = byte_id
            current_code_int += 1
            last_length = length

        return canonical_lookup

    def generate_huffman_lookup(self, weights_table: dict) -> dict:
        """
        Автоматически строит дерево Хаффмана на основе таблицы весов
        для ключей в диапазоне от 0x0000 до 0xA000.
        Args:
            weights_table: dict - таблица весов
        Returns:
            словарь соответствия: { 'бинарный_код_строкой': декодированное_значение }
        """
        # Очередь с приоритетами (куча) для сборки дерева
        heap = []
        counter = 0
        
        for key_title, weight in weights_table.items():
            node = {'id': key_title, 'left': None, 'right': None}
            # Формат элемента: (вес, уникальный_счетчик, узел_дерева)
            heapq.heappush(heap, (weight, counter, node))
            counter += 1

        if not heap:
            return {}

        # Построение дерева Хаффмана путем слияния минимальных узлов
        while len(heap) > 1:
            weight1, _, node1 = heapq.heappop(heap)
            weight2, _, node2 = heapq.heappop(heap)
            
            parent_node = {'id': None, 'left': node1, 'right': node2}
            parent_weight = weight1 + weight2
            
            heapq.heappush(heap, (parent_weight, counter, parent_node))
            counter += 1

        # Корень финального дерева
        _, _, root_node = heapq.heappop(heap)       # там 1 элемент, heap[0]
        # _, _, root_node = heapq.heappop(heap)  #  heap
        huffman_lookup = {}
        
        # Рекурсивный обход дерева для генерации префиксных битовых кодов
        def walk_tree(node, current_code):
            if node['id'] is not None:
                val_id = node['id']
                """
                # noqa:
                # Логика интерпретации ID в конечный символ или токен
                # if val_id == 0x00:
                #     char_out = "[EOS]"                      # Маркер конца строки
                # elif 0x41 <= val_id <= 0x5A:
                #     char_out = chr(val_id).lower()          # Перевод латиницы A-Z в нижний регистр a-z
                # elif 32 <= val_id <= 126:
                #     char_out = chr(val_id)                  # Остальной печатный ASCII
                # elif 0x0400 <= val_id <= 0x04FF:
                #     char_out = chr(val_id)                  # Кириллица (Unicode), если присутствует в СНГ-версии
                # else:
                #     char_out = f"[Token_0x{val_id:04X}]"    # Крупные токены координат или гео-префиксов
                """
                # huffman_lookup[current_code] = char_out
                huffman_lookup[current_code] = val_id
                return
            
            # Левая ветка кодируется нулем, правая — единицей
            if node['left']:
                walk_tree(node['left'], current_code + "0")
            if node['right']:
                walk_tree(node['right'], current_code + "1")

        # Запускаем обход от корня
        walk_tree(root_node, "")
        return huffman_lookup

    def empty(self):
        """
        Args:
            param1: This is the first param.
            param2: This is a second param.

        Returns:
            This is a description of what is returned.

        Raises:
            KeyError: Raises an exception.
        """
        self.path = None
        self.dbrev = DEFAULT_DB_REVISION
        self.segsize = DEFAULT_ONE_SEG_SIZE


# ================================================
class BYTESTRUCT():
    """ Base for other data structures """

    def __init__(self, buffer: bytearray, size: int = None) -> None:
        if size is not None:
            self._raw = buffer[:size]
            return
        self._raw = buffer
    
    def __repr__(self) -> str:
        # ss = "B " + self.hex
        return self.hex
    
    @property
    def hex(self):
        # he = " ".join("{:02x}".format(c) for c in self._raw)
        hex_list = [f"{c:02X}" for c in self._raw]
        result_lines = []
        for i in range(0, len(hex_list), 16):
            # Номер строки в HEX (0000, 0010, 0020 и т.д.)
            #   line_number = f"{i:04X}: "
            # 8 + " " + 8 HEX-значений текущей строки
            # hex_chunk = " ".join(hex_list[i : i + 16])
            hex_chunk0 = " ".join(hex_list[i : i + 8])
            hex_chunk1 = " ".join(hex_list[i + 8 : i + 16])
            # Собираем строку воедино
            #result_lines.append(f"{line_number}: {hex_chunk0}  {hex_chunk1}")
            result_lines.append(f"{hex_chunk0}  {hex_chunk1}")
        # Объединяем все строки
        # cr = "{}".format("\n")
        result = "   ".join(result_lines)
        return result

    @property
    def len(self):
        """ length raw in bytes """
        return len(self._raw)

    def read(self, offset: int, cnt: int) -> bytearray:
        """ read from inner bytes array """
        ret = self._raw[offset: offset + cnt]
        return ret

    def read_str(self, ptr: int, max_len: int = None) -> str:
        """
        Args:
            ptr: offset в текущем _raw
        Returns:
            str: 0-ended строка
        """
        # ??? struct.unpack("s*")
        if not max_len:
            max_len = MAX_STR_LEN
        return self.read(ptr, max_len).decode('cp1250').split('\x00')[0]
    
    def uchar(self, near_offset: int = 0) -> int:
        ''' Return uchar, offset from _raw begin'''
        #uc = self.read(near_offset, UCHAR_BYTES_CNT)
        uc = self._raw[near_offset]
        return uc

    def ushort(self, near_offset: int = 0) -> int:
        ''' Return unsigned short (2 bytes, word), offset from _raw begin'''
        return struct_WORD.unpack_from(self._raw[near_offset:])[0]
    
    def uint(self, near_offset: int = 0) -> int:
        ''' Return unsigned int (4 bytes, dword), offset from _raw begin'''
        return struct_UINT.unpack_from(self._raw[near_offset:])[0]

    # def list(self, near_offset: int = 0) -> LIST:
    #     return LIST(self._raw[near_offset:LIST.size])

    # def coord(self, near_offset: int = 0) -> COORD:
    #     return COORD(self._raw[near_offset:COORD.size])
    

# ----
class BLADDR(BYTESTRUCT):
    ''' b'\x01\x02\x03\x04' -> 0x010203 - number, 04 - len in blocks '''
    size: int = UINT_BYTES_CNT

    def __new__(cls, buffer, parent: VDO_FILE = None):
        instance = super().__new__(cls)
        return instance

    def __init__(self, buffer: bytearray, vdo: VDO_FILE = None) -> None:
        super().__init__(buffer[:UINT_BYTES_CNT])  # 4 - self.bytescnt
        #self.vdo = vdo if vdo else VDO_FILE()
        if not vdo or self._raw == ZERO_DWORD:
            self.vdo = VDO_FILE()
        else:
            self.vdo = vdo
        pass

    def __repr__(self) -> str:
        ''' View while debug value'''
        v = '' if self.vdo.path else ' virt'
        return self.hex + v

    @property
    def isZero(self) -> True | False:
        ''' 00 00 00 00 - "заглушка" - встречается, но ptr не на реальный блок '''
        return self._raw == ZERO_DWORD
    
    @property
    def blocknumber(self) -> int:
        ''' Номер блока, первые 3 байта'''
        return struct_UINT.unpack(b'\x00' + self._raw[:3])[0]
    
    @property
    def segcnt(self) -> int:
        ''' Размер в сегментах, последний байт'''
        bn = self.uchar(3)
        return bn
    
    @property
    def sizeofblock(self) -> int:
        ''' Размер описываемого блока в байтах'''
        sz = self.segcnt * self.vdo.segsize
        return sz
    
    @property
    def hex(self):
        he = f'{self.blocknumber:06x} {self._raw[3]:02x}'
        return he

    @property
    def offset(self):
        ''' Смещение от начала файла'''
        bo = int(self.blocknumber * self.vdo.segsize)
        return bo
    
    def next_block_offset(self):
        return self.offset + self.sizeofblock
    
    def __eq__(self, value: object) -> bool:
        '''TODO: segsize == segsize'''
        if not isinstance(value, BLADDR):
            return NotImplemented
        if self.vdo.segsize != value.vdo.segsize:
            return False    # segsize обязаны быть равными
        if self.blocknumber == value.blocknumber:
            return True
        return False
    
    def __lt__(self, value: object) -> bool:
        if not isinstance(value, BLADDR):
            #raise TypeError("Операнд справа должен иметь тип BLADDR")
            return NotImplemented
        if self.vdo.segsize != value.vdo.segsize:
            return False    # segsize обязаны быть равными
        if self.blocknumber < value.blocknumber:
            return True
        return False
    
    def __le__(self, value: object) -> bool:
        if not isinstance(value, BLADDR):
            return NotImplemented
        if self.vdo.segsize != value.vdo.segsize:
            return False    # segsize обязаны быть равными
        if self.blocknumber <= value.blocknumber:
            return True
        return False


# ----
class PTR(BYTESTRUCT):
    ''' Указатель(near) 01 02 -> near offset 0x102 '''
    size: int = USHORT_BYTES_CNT

    def __init__(self, buffer: bytearray) -> None:
        super().__init__(buffer[:USHORT_BYTES_CNT])     # 2 - self.bytescnt
    
    def __repr__(self):
        ''' View while debug value'''
        return "0x{:04X}".format(self.value)
 
    @property
    def value(self) -> int:
        ''' Near ptr to begin list'''
        #p = struct_WORD.unpack(self._raw)[0]
        return self.ushort()
    
    @property
    def hexptr(self) -> str:
        ''' ptr in hex string '''
        return "0x{:02X}".format(self.value)
    
    
# ----
class LIST(BYTESTRUCT):
    ''' ptr: указатель(near) на начало массива; cnt: количество элементов
    b'\x01\x02\x03\x04' -> near offset 0x102, counter items 0x304 '''
    size: int = UINT_BYTES_CNT

    def __init__(self, buffer: bytearray) -> None:
        super().__init__(buffer[:UINT_BYTES_CNT])   # 4 - self.bytescnt

    def __repr__(self):
        ''' View while debug value'''
        val = "{0:04X}:{1:04X} cnt:{1:d}".format(self.ptr, self.cnt)
        return val
        
    @property
    def ptr(self) -> int:
        ''' Near ptr to begin list'''
        return self.ushort()

    @property
    def cnt(self) -> int:
        ''' List counter '''
        return self.ushort(2)
 

# ----
class FAR_LIST(BYTESTRUCT):
    ''' BLADDR : LIST '''
    size: int = DOUBLE_BYTES_CNT

    def __new__(cls, buffer, parent: VDO_FILE = None):
        instance = super().__new__(cls)
        return instance
    
    def __init__(self, buffer: bytearray, vdo: VDO_FILE = None) -> None:
        super().__init__(buffer[:DOUBLE_BYTES_CNT])  # 8 - self.bytescnt
        #self.vdo = vdo if vdo else VDO_FILE()
        if not vdo or self._raw[:4] == ZERO_DWORD:
            self.vdo = VDO_FILE()
        else:
            self.vdo = vdo
    
    def __repr__(self):
        ''' View while debug value'''
        val = self.hex
        return val
    
    @property
    def bladdr(self) -> BLADDR:
        return BLADDR(self._raw, self.vdo)

    @property
    def list(self) -> LIST:
        return LIST(self._raw[UINT_BYTES_CNT:])

    @property
    def offset(self) -> int:
        return self.bladdr.offset + self.list.ptr

    @property
    def hex(self) -> str:
        #sh = f"{self.bladdr}: {self.list.hexptr} {self.list.hexcnt}"
        sh = self.bladdr.__repr__() + ' : ' + self.list.__repr__()
        return sh
    

# сложные составные типы
# ==========
class CH_IDX(BYTESTRUCT):
    '''
    CH_IDX   3*DWORD, указатель на список букв или (страны, города, улицы, poi)
      DWORD bl_postaddr адрес блока
      byte  ch    собственно буква
      byte  is_ptr_out = 0 на индекс (CH_idx 0b,0d,0f,11), 1 - на описание (0a,0c,0e,10)
      LIST  pointer-counter в bl_postaddr
      WORD  align
    '''
    size: int = 12        # CH_IDX size = 3 * DWORD

    def __new__(cls, buffer, parent: VDO_FILE = None):
        instance = super().__new__(cls)
        return instance
    
    def __init__(self, buffer: bytearray, vdo: VDO_FILE = None) -> None:
        if (len(buffer) < self.size):
            err = f"Размер массива байтов {len(buffer)}\
 меньше требуемого {self.size}"
            raise TypeError(err)
        super().__init__(buffer[:self.size])  # 4 - CH_IDX_SIZE
        self.vdo = vdo if vdo else VDO_FILE()

    def __repr__(self):
        ''' View while debug value'''
        # val = self.hex
        val = f"{self.ch} {self.is_out} {self.bladdr} {self.list}"
        return val
    
    @property
    def bladdr(self) -> BLADDR:
        return BLADDR(self._raw, self.vdo)
    
    @property
    def ch(self) -> str:
        """ char from offset 5 """
        return chr(self._raw[4])  # 4 - offset of char

    @property
    def is_out(self) -> bool:
        """ offset 6 :is_ptr_out - flag
        0 - на индекс (CH_idx 0b,0d,0f,11)
        1 - на описание (0a,0c,0e,10) """
        return False if self._raw[5] == 0 else True

    @property
    def list(self) -> LIST:
        return LIST(self._raw[UINT_BYTES_CNT + 2:])


# ==========
class BLSTART(BYTESTRUCT):
    """ Первый DWORD любого блока
        offset  type  sense         value
        00   dword   BLADDR          00000001 always
        04   word    bl_type         0012
        06   char    is_arch         00-not arch, 01- ???, 02-lzw
        07   char    unarch_size """
    
    size: int = DOUBLE_BYTES_CNT

    def __new__(cls, buffer, parent: VDO_FILE = None):
        instance = super().__new__(cls)
        return instance

    def __init__(self, buffer: bytearray, vdo: VDO_FILE = None):
        """ """
        super().__init__(buffer[:self.size])
        self.vdo = vdo if vdo else VDO_FILE()

    def __repr__(self):
        ''' View while debug value'''
        v = '' if self.vdo.path else ' virt'
        v = f'{v} [{self.bltype.value:02X}:{self.bltype.name}]'
        return self.headhex() + v
    
    @property
    def bladdr(self) -> BLADDR:
        return BLADDR(self._raw, self.vdo)

    @property
    def bltype(self) -> BlockType:
        """ Enums type of block """
        OFFSET_TYPE = 4
        bltype = self.ushort(OFFSET_TYPE)
        if bltype in BlockType:
            return BlockType(bltype)
        return BlockType(0xFF)     # unknown

    def headhex(self) -> str:
        ''' Строковое представление'''
        OFFSET_TYPE = 4
        s = "{:08x} {:02x} {:04x}".format(self.uint(),
                                          self.ushort(OFFSET_TYPE),
                                          self.ushort(OFFSET_TYPE + 2))
        return s

    @property
    def segcnt(self):
        ''' Количество сегментов после распаковки, was unarc_segcnt'''
        if self.arch_type:
            OFFSET_UNARC_SEGS = 7
            return self._raw[OFFSET_UNARC_SEGS]
        return self.bladdr.segcnt
    
    @property
    def arch_type(self):
        ''' 2 - zlib, 1 - bytype, 0 - not archived'''
        if self._raw == b'\x00\x00\x00\x00':
            return None  # if bl 0xEE
        OFFSET_ARC_TYPE = 6
        return self._raw[OFFSET_ARC_TYPE]
    
    @property
    def sizeofblock(self) -> int:
        ''' Размер распакованного блока в байтах'''
        if self.arch_type:
            return self.segcnt * self.vdo.segsize
        return self.bladdr.sizeofblock

# class PSTR(PTR):
#     ''' PSTR    WORD, nearPTR на zero-ended строку '''
#     strval:str
#     bytescnt: int = 2  # CH_IDX size = 3 * DWORD
#     def __init__(self, bytes_arr) -> None:
#         super().__init__(bytes_arr[:self.bytescnt]) # 4 - self.bytescnt


# =========================================================================
if __name__ == '__main__':
    
    vdo2 = VDO_FILE()

    fpath = 'c:\\DIY\\VDO\\db_src\\NAV_DB\\carindb'
    vdo = VDO_FILE(fpath)

    fpath34 = 'c:\\DIY\\VDO\\db_src\\1. BNL_13_14\\carindb'
    vdo34 = VDO_FILE(fpath34)

    ba0 = BLADDR(b'\x00\x01\x02\x01')
    ba1 = BLADDR(b'\x03\x04\x01\x05', vdo)

    raw_bs = b'\x00\x01\x02\x01\x00\x12\x01\x02'
    bstart1 = BLSTART(raw_bs)
    bstart2 = BLSTART(raw_bs, vdo)

    raw = b'\x00\x02\x01\x01\x00\x12\x00\x00\x004\x00\x01\x00\x00\x03\x01\x00\x0c\x00\
\x14\x00\x00\x01\x01\x00\x01\x00\x1e\x00\x00\x00\x0c'
    bp = PTR(raw[5:])
    bl = LIST(raw[8:])
    bfl1 = FAR_LIST(raw_bs)
    bfl2 = FAR_LIST(raw_bs, vdo)

    chi = b'\x00\x00\x02\x02\x47\x01\x01\x00\x00\x10\x00\x00'
    bl_ch_idx1 = CH_IDX(chi)
    chi = b'\x00\x01\x02\x01\x50\x00\x01\x00\x00\x10\x00\x00'
    bl_ch_idx2 = CH_IDX(chi, vdo)

    pass
