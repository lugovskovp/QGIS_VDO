"""


"""

import zlib             # распаковка архивов типа 2 и 3

# from vdo.enums import BlockType
from vdo.datatypes import BYTESTRUCT, BLADDR, BLSTART, LIST, FAR_LIST
from vdo.datatypes import ZERO_DWORD
from vdo.geotypes import COORD

ZLIB_BEGIN_OFFSET = 8         # for archive type 2
BLOCK_0x12_SIZE = 0x800

# 0x13 - read_str(self)


class block_base(BYTESTRUCT):
    """ Родительский класс для любого блока """

    def __init__(self, addr: BLADDR) -> None:
        """ """
        if addr._raw == ZERO_DWORD:
            #nothing
            zero = ZERO_DWORD + ZERO_DWORD
            self._raw = zero
            return
        if not addr.vdo.path:
            # virtual BLADDR
            zero = ZERO_DWORD + ZERO_DWORD
            self._raw = zero
            return
        #
        self.vdo = addr.vdo
        # и тут инициировать BYTESTRUCT
        size = addr.sizeofblock if addr.offset else BLOCK_0x12_SIZE
        # что бы ни было в файле, но размер блока 0х12 всегда 1*0х800
        buffer = self.vdo.read(addr.offset, size)
        # property self.head = - информация о блоке: тип, архивирован ли, размер(ы)
        self._raw = buffer[:BLSTART.size]
        # при необходимости, распаковать
        if self.head.arch_type == 0:
            super().__init__(buffer)
            return
        elif self.head.arch_type in [2, 3]:
            #zlib  третий тип вообще-то не ясно - почему отдельно от 2, то же самое
            # ТИПЫ БЛОКОВ archived by zlib in bmw:
            # 17 1E 09 1D 14 1C 15 16 01 02 03 04 00 06 10 11 0E 0F 0C 0D 0A 13
            unarc_raw = buffer[:ZLIB_BEGIN_OFFSET]    # - начало не запаковано
            # распаковать запакованное
            unarc_raw += zlib.decompress(buffer[ZLIB_BEGIN_OFFSET:],
                                         bufsize=self.head.segcnt * self.vdo.segsize)
            #self._raw = unarc_raw
            super().__init__(unarc_raw)
            return
        elif self.head.arch_type == 1:
            # ВОТ ТУТ САМОЕ ПЕЧАЛЬНОЕ
            pass
        super().__init__(buffer)
        
        pass

    def __repr__(self) -> str:
        return self.head.__repr__()

    @property
    def head(self) -> BLSTART:
        """ Заголовок, первые 8 байт блока
        Args:
            self: from _raw
        Returns:
            BLSTART: structure
        """
        return BLSTART(self.read(0, BLSTART.size), self.vdo)

    def bladdr(self, value: bytearray | int) -> BLADDR:
        """
        Args:
            value: или массив байтов, или offset, откуда их взять в _raw
        Returns:
            BLADDR: - block adress
        """
        if type(value) is int:
            # offset
            value = self.read(value, BLADDR.size)
        return BLADDR(value, self.vdo)
    
    def farlist(self, value: bytearray | int) -> FAR_LIST:
        """
        Args:
            value: или массив байтов, или offset, откуда их взять в _raw
        Returns:
            FAR_LIST: - block adress, ptr and counter
        """
        if type(value) is int:
            # offset
            value = self.read(value, FAR_LIST.size)
        return FAR_LIST(value, self.vdo)

    def list(self, value: bytearray | int) -> LIST:
        """
        Args:
            value: или массив байтов, или offset, откуда их взять в _raw
        Returns:
            LIST: - ptr-cnt
        """
        if type(value) is int:
            # offset
            return LIST(self.read(value, LIST.size))
        #bytearray
        return LIST(value)

    def coord(self, offset: int) -> COORD:
        """ Координаты - 8 байт блока
        Args:
            self: from _raw
            offset: offset from block start
        Returns:
            COORD: structure
        """
        return COORD(self.read(offset, COORD.size))

    def read_str(self, ptr_list_str: int):
        """
        Строка, адрес и размер которой в LIST по offset
        Args:
            ptr_list_str: int offset ptr-cnt
        Returns:
            str: строка
        """
        li = self.list(ptr_list_str)
        # -1: 'no label\x00'
        return self.read(li.ptr, li.cnt - 1).decode('cp1250')


# --------------------------------------------------------
if __name__ == "__main__":
    from vdo.datatypes import VDO_FILE

    fpath = 'c:\\DIY\\VDO\\db_src\\NAV_DB\\carindb'
    vdo = VDO_FILE(fpath)

    bla12 = BLADDR(b'\x00\x00\x00\x01', vdo)
    bla13 = BLADDR(b'\x00\x00\x01\x01', vdo)

    bb12 = block_base(bla12)
    bb13 = block_base(bla13)

    pass
