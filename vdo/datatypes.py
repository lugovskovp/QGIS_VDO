import struct
import os.path
from vdo.enums import BlockType


'''
VDO_FILE
BYTESTRUCT
BL_ADDR  DWORD, Структура адреса блока
PTR      WORD near - указатель
LIST
FAR_LIST
CH_IDX
BLSTART

'''

OFFSET_TOC = 0x08

OFFSET_DB_REVISION = 0x1a
DEFAULT_DB_REVISION = 0x1e
OFFSET_ONE_SEG_SIZE = 0x2c
DEFAULT_ONE_SEG_SIZE = 0x800

#UCHAR_BYTES_CNT = 1
USHORT_BYTES_CNT = 2
UINT_BYTES_CNT = 4
DOUBLE_BYTES_CNT = 8

USHORT_struct = struct.Struct(">H")
UINT_struct = struct.Struct(">L")

ZERO_DWORD = b'\x00\x00\x00\x00'
MAX_STR_LEN = 63    # 255


# ----
class VDO_FILE():
    """ --- """
    path: os.path
    # :path: full filepath, os.path or None
    dbrev: int
    """:dbrev: database revision, 30 (0x1e) or 34 (0x22)"""
    segsize: int    # :segsize: size of one segment in chank

    def __init__(self, path: os.path = None) -> None:
        """ """
        if path:
            self.path = path
            self.dbrev = USHORT_struct.unpack(self.read(OFFSET_DB_REVISION, 2))[0]
            self.segsize = USHORT_struct.unpack(self.read(OFFSET_ONE_SEG_SIZE, 2))[0]
            return
        self.empty()

    def __repr__(self):
        s = f'VDOv{self.dbrev}[{self.segsize}]:{self.path}'
        return s

    def read(self, offset: int, size: int) -> bytearray:
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


# ----
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
        he = " ".join("{:02x}".format(c) for c in self._raw)
        return he

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
        ''' Return uchar, offset from block begin'''
        #uc = self.read(near_offset, UCHAR_BYTES_CNT)
        uc = self._raw[near_offset]
        return uc

    def ushort(self, near_offset: int = 0) -> int:
        ''' Return unsigned short (2 bytes, word), offset from block begin'''
        return USHORT_struct.unpack_from(self._raw[near_offset:])[0]
    
    def uint(self, near_offset: int = 0) -> int:
        ''' Return unsigned int (4 bytes, dword), offset from block begin'''
        return UINT_struct.unpack_from(self._raw[near_offset:])[0]
    

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
        return UINT_struct.unpack(b'\x00' + self._raw[:3])[0]
    
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
        #p = USHORT_struct.unpack(self._raw)[0]
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
