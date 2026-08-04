"""


"""

import zlib             # распаковка архивов типа 2 и 3

from typing import TYPE_CHECKING, Union, Type, TypeVar

if TYPE_CHECKING:
    # Этот блок видит только Pylance, интерпретатор Python его игнорирует
    from _typeshed import ReadableBuffer  # pragma: no cover
else:
    # Запасной вариант для рантайма, чтобы не было NameError
    ReadableBuffer = bytes


# from QGIS_VDO.vdo.consts import struct_UINT

# from vdo.enums import BlockType
from QGIS_VDO.vdo.datatypes import BYTESTRUCT, BLADDR, BLSTART, LIST, FAR_LIST, CH_IDX, PTR
from QGIS_VDO.vdo.datatypes import MAX_STR_LEN
from QGIS_VDO.vdo.geotypes import COORD
# from QGIS_VDO.vdo.enums import BlockType

ZLIB_BEGIN_OFFSET = 8         # for archive type 2
BLOCK_0x12_SIZE = 0x800

# 0x13 - read_str(self)

ZERO_DWORD = "\x00" * 4


# Выносим декомпрессоры на уровень модуля
def _decompress_zlib(buffer: memoryview, head: BLSTART, vdo) -> bytearray:
    max_bufsize = head.segcnt * vdo.segsize
    unarc_raw = bytearray(buffer[:ZLIB_BEGIN_OFFSET])
    unarc_raw += zlib.decompress(buffer[ZLIB_BEGIN_OFFSET:], bufsize=max_bufsize)
    return unarc_raw


# Мапа стратегий: arch_type -> функция обработки
COMPRESSION_REGISTRY = {
    2: _decompress_zlib,
    3: _decompress_zlib,
}


# 1. Жестко перечисляем разрешенные классы для статического анализа (IDE / Mypy)
ALLOWED_STRUCTURES = TypeVar(
    'ALLOWED_STRUCTURES',
    BLADDR, FAR_LIST, LIST, PTR, COORD, CH_IDX
)

# 2. Множество для молниеносной рантайм-проверки (O(1))
_VALID_STRUCTS = {BLADDR, FAR_LIST, LIST, PTR, COORD, CH_IDX}


class block_base(BYTESTRUCT):
    """Родительский класс для любого блока данных карты с оптимизированной структурой."""

    __slots__ = ('vdo', 'is_unpacked', '_head_cached', 'type', 'type_name')

    def __init__(self, addr: BLADDR) -> None:
        # 1. Валидация на входе
        if not isinstance(addr, BLADDR):
            raise TypeError(f"addr must be BLADDR, got {type(addr)}")
        if addr.isZero or addr.vdo.is_empty:
            raise ValueError(f"Cannot initialize block from zero address: {addr.isZero}, or empty VDO: {addr.vdo.is_empty} context")  # noqa

        self.vdo = addr.vdo
        self.is_unpacked = True
        self._head_cached = None

        # 2. Чтение буфера
        if self.vdo.is_single:   # одиночный файл
            offset = 0
            size = addr.sizeofblock
        else:
            offset = addr.offset
            size = BLOCK_0x12_SIZE if addr.blocknumber == 0 else addr.sizeofblock
        buffer = self.vdo.read(offset, size)
        
        if not buffer:
            super().__init__(b"")
            self.is_unpacked = False
            return

        # 3. Парсинг заголовка
        temp_view = memoryview(buffer)
        head_obj = BLSTART(temp_view[:BLSTART.size], self.vdo)
        self._head_cached = head_obj

        #
        self.type = head_obj.bltype.value
        self.type_name = head_obj.bltype.value

        # 4. Диспетчеризация распаковки (Паттерн Стратегия)
        arch_type = head_obj.arch_type
        
        if arch_type == 0:
            super().__init__(buffer)
            return

        decoder = COMPRESSION_REGISTRY.get(arch_type)
        if decoder is None:
            # Сюда попадает arch_type == 1 и любые неизвестные типы
            super().__init__(buffer)
            self.is_unpacked = False
            return

        try:
            unpacked_data = decoder(temp_view, head_obj, self.vdo)
            super().__init__(unpacked_data)
        except (zlib.error, ValueError):
            super().__init__(buffer)
            self.is_unpacked = False

    @property
    def head(self) -> BLSTART:
        return self._head_cached

    @property
    def dbrev(self) -> int:
        return self.vdo.dbrev

    @property
    def segsize(self) -> int:
        return self.vdo.segsize

    def __repr__(self) -> str:
        if not self.head:
            return "NO_HEAD"
        packed = '@ ' if self.head.arch_type else ''
        return f"{packed}{repr(self.head)}"

    def offset_next(self) -> Union[int, None]:
        if not getattr(self.vdo, 'file_path', None):
            return None
        res = self.head.bladdr.offset + (self.vdo.segsize * self.head.bladdr.segcnt)
        # TODO: а что делать с vdo.is_single ?
        if res < self.vdo.file_size:
            return res
        return None  # это был последний блок, следущего нет

    # --- Универсальный интерфейс чтения вместо 6 дубликатов ---

    def read_struct(self, offset: int, struct_cls: Type[ALLOWED_STRUCTURES]) -> ALLOWED_STRUCTURES:
        """Быстрое чтение строго ограниченного списка структур по смещению."""
        
        # Защита в рантайме
        if struct_cls not in _VALID_STRUCTS:
            raise TypeError(f"Класс {struct_cls.__name__} не разрешен для чтения через read_struct")
            
        if type(offset) is not int:
            raise TypeError(f"Смещение должно быть int, получено {type(offset)}")
        
        raw_bytes = self.read(offset, struct_cls.size)
        try:
            return struct_cls(raw_bytes, self.vdo)
        except TypeError:
            return struct_cls(raw_bytes)

    # --- Сахар для обратной совместимости (теперь со 100% точной типизацией) ---
    def read_bladdr(self, offset: int) -> BLADDR: return self.read_struct(offset, BLADDR)       # noqa
    def read_farlist(self, offset: int) -> FAR_LIST: return self.read_struct(offset, FAR_LIST)       # noqa
    def read_list(self, offset: int) -> LIST: return self.read_struct(offset, LIST)       # noqa
    def read_ptr(self, offset: int) -> PTR: return self.read_struct(offset, PTR)       # noqa
    def read_coord(self, offset: int) -> COORD: return self.read_struct(offset, COORD)       # noqa
    def read_ch_idx(self, offset: int) -> CH_IDX: return self.read_struct(offset, CH_IDX)       # noqa

    def read_li_str(self, ptr_list_str: int) -> str:
        li = self.read_list(ptr_list_str)
        return bytes(self.read(li.ptr, li.cnt - 1)).decode('cp1250')

    def read_str(self, offset: int) -> str:
        if not offset:
            return ''
        if type(offset) is not int:
            raise TypeError(f"Смещение должно быть int, получено {type(offset)}")
        return super().read_str(offset, MAX_STR_LEN)

    def write_raw(self, name: str = "_base_block.bin") -> None:
        with open(name, "wb") as f:
            f.write(self._raw)


# --------------------------------------------------------
if __name__ == "__main__":
    from QGIS_VDO.vdo import VDO_FILE

    fpath = 'c:\\DIY\\VDO\\db_src\\NAV_DB\\carindb'
    vdo = VDO_FILE(fpath)

    bla12 = BLADDR(b'\x00\x00\x00\x01', vdo)
    bla13 = BLADDR(b'\x00\x00\x01\x01', vdo)

    bb12 = block_base(bla12)
    bb13 = block_base(bla13)

    pass
