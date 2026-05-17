import struct

'''
BYTESTRUCT
BL_ADDR  DWORD, Структура адреса блока
PTR      WORD near - указатель



'''

ZERO_DWORD = b'\x00\x00\x00\x00'

UCHAR_BYTES_CNT = 1
USHORT_BYTES_CNT = 2
UINT_BYTES_CNT = 4
DOUBLE_BYTES_CNT = 8

USHORT_struct = struct.Struct(">H")
UINT_struct = struct.Struct(">L")

activeCarindb = {'path': 'c:\\DIY\\VDO\\db_src\\NAV_DB\\carindb',
                 'ver': 30,
                 'segsize': 0x100
                 }


# ----
class BYTESTRUCT():
    """ Base for other data structures """

    def __new__(cls, *args, **kwargs):
        """ Добавление атрибуты класса, которые затем наследуются """
        instance = super().__new__(cls)
        instance.filepath = activeCarindb['path']
        instance.segsize = activeCarindb['segsize']
        instance.version = activeCarindb['ver']
        return instance

    def __init__(self, bytesarr: bytes) -> None:
        self._raw = bytesarr
    
    @classmethod
    def from_file(cls, offset: int, bytes: int) -> None:
        """ Создание - чтение массива из файла и инициализация прочитанным """
        tmp = BYTESTRUCT(b'\x00')
        with open(tmp.filepath, 'rb') as f:
            #offset = int(hex_offset, base=16)
            f.seek(offset)
            buffer = f.read(bytes)
            return cls(buffer)

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
    
    def uchar(self, near_offset: int = 0) -> int:
        ''' Return uchar, offset from block begin'''
        uc = self.read(near_offset, UCHAR_BYTES_CNT)
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

    def __init__(self, bytes_arr) -> None:
        super().__init__(bytes_arr[:UINT_BYTES_CNT])  # 4 - self.bytescnt
        #self.segsize = SEGSIZE

    def __repr__(self):
        ''' View while debug value'''
        return self.hex

    @property
    def isZero(self) -> True | False:
        ''' 00 00 00 00 - "заглушка" - встречается, но ptr не на реальный блок '''
        return self._raw == ZERO_DWORD
    
    @property
    def blocknumber(self) -> int:
        ''' Номер блока, первые 3 байта'''
        bb = UINT_struct.unpack(b'\x00' + self._raw[:3])[0]
        return bb
    
    @property
    def segcnt(self) -> int:
        ''' Размер в сегментах, последний байт'''
        bn = self.uchar(3)
        return bn
    
    @property
    def sizeofblock(self) -> int:
        ''' Размер описываемого блока в байтах'''
        sz = self.segcnt * self.segsize
        return sz
    
    @property
    def hex(self):
        he = f'{self.blocknumber:06x} {self._raw[3]:02x}'
        return he

    @property
    def offset(self):
        ''' Смещение от начала файла'''
        bo = int(self.blocknumber * self.segsize)
        return bo
    
    def next_block_offset(self):
        return self.offset + self.sizeofblock
    
    def __eq__(self, value: object) -> bool:
        '''TODO: segsize == segsize'''
        if not isinstance(value, BLADDR):
            return NotImplemented
        if self.segsize != value.segsize:
            return False    # segsize обязаны быть равными
        if self.blocknumber == value.blocknumber:
            return True
        return False
    
    def __lt__(self, value: object) -> bool:
        if not isinstance(value, BLADDR):
            #raise TypeError("Операнд справа должен иметь тип BLADDR")
            return NotImplemented
        if self.segsize != value.segsize:
            return False    # segsize обязаны быть равными
        if self.blocknumber < value.blocknumber:
            return True
        return False
    
    def __le__(self, value: object) -> bool:
        if not isinstance(value, BLADDR):
            return NotImplemented
        if self.segsize != value.segsize:
            return False    # segsize обязаны быть равными
        if self.blocknumber <= value.blocknumber:
            return True
        return False


# ----
class PTR(BYTESTRUCT):
    ''' Указатель(near) 01 02 -> near offset 0x102 '''
    
    def __init__(self, bytes_arr) -> None:
        super().__init__(bytes_arr[:USHORT_BYTES_CNT])     # 2 - self.bytescnt
    
    def __repr__(self):
        ''' View while debug value'''
        return "0x{:04X}".format(self.value)
 
    @property
    def value(self) -> int:
        ''' Near ptr to begin list'''
        #p = USHORT_struct.unpack(self._raw)[0]
        p = self.ushort()
        return p
    
    @property
    def hexptr(self) -> str:
        ''' ptr in hex string '''
        return "{:02X}".format(self.value)
    
    
# ----
class LIST(BYTESTRUCT):
    ''' ptr: указатель(near) на начало массива; cnt: количество элементов
    b'\x01\x02\x03\x04' -> near offset 0x102, counter items 0x304 '''
    
    def __init__(self, bytes_arr) -> None:
        super().__init__(bytes_arr[:UINT_BYTES_CNT])   # 4 - self.bytescnt

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
    
    def __init__(self, bytes_arr: bytes) -> None:
        super().__init__(bytes_arr[:DOUBLE_BYTES_CNT])  # 8 - self.bytescnt
    
    def __repr__(self):
        ''' View while debug value'''
        val = self.hex
        return val
    
    @property
    def bladdr(self) -> BLADDR:
        return BLADDR(self._raw)

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
# --------
class CH_IDX(BYTESTRUCT):
    '''
    CH_IDX   3*DWORD, указатель на список букв или (страны, города, улицы, poi)
      DWORD bl_postaddr адрес блока
      byte  ch    собственно буква
      byte  is_ptr_out = 0 на индекс (CH_idx 0b,0d,0f,11), 1 - на описание (0a,0c,0e,10)
      LIST  pointer-counter в bl_postaddr
      WORD  align
    '''
    
    def __init__(self, bytes_arr) -> None:
        CH_IDX_SIZE = 12      # CH_IDX size = 3 * DWORD
        if (len(bytes_arr) < CH_IDX_SIZE):
            err = f"Размер массива байтов {len(bytes_arr)} \
меньше требуемого {CH_IDX_SIZE}"
            raise TypeError(err)
        super().__init__(bytes_arr[:CH_IDX_SIZE])  # 4 - CH_IDX_SIZE

    def __repr__(self):
        ''' View while debug value'''
        val = self.hex
        return val
    
    @property
    def bladdr(self) -> BLADDR:
        return BLADDR(self._raw)
    
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


# =========================================================================
if __name__ == '__main__':
    #
    raw = b'\x00\x02\x01\x01\x00\x12\x00\x00\x004\x00\x01\x00\x00\x03\x01\x00\x0c\x00\
\x14\x00\x00\x01\x01\x00\x01\x00\x1e\x00\x00\x00\x0c'

    bs = BYTESTRUCT(raw[:16])
    bs2 = BYTESTRUCT.from_file(3, 10)
    ba = BLADDR(raw)
    bp = PTR(raw[5:])
    bl = LIST(raw[8:])
    bfl = FAR_LIST(raw)
    bl_ch_idx = CH_IDX(b'\x00\x00\x02\x02\x47\x01\x01\x00\x00\x10\x00\x00')

    ssbs = bs.segsize
    sstt = ba.segsize
    
    ssbs = bs.segsize
    sstt = ba.segsize

    bb = bs.read(2, 2)
    pass

    pass
