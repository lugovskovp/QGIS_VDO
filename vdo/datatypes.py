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
from __future__ import annotations  # Обязательно на самой первой строчке файла

import os.path
import importlib

from typing import TYPE_CHECKING, Union, Any, Optional

if TYPE_CHECKING:       # pragma: no cover
    # Этот блок видит только Pylance, интерпретатор Python его игнорирует
    from _typeshed import ReadableBuffer
else:
    # Запасной вариант для рантайма, чтобы не было NameError
    ReadableBuffer = bytes


from .enums import BlockType
from .consts import struct_WORD, struct_UINT
from .consts import USHORT_BYTES_CNT, UINT_BYTES_CNT, DOUBLE_BYTES_CNT, EMPTY_BUFFER


OFFSET_TOC = 0x08

DEFAULT_DB_REVISION = 0x1e
DEFAULT_ONE_SEG_SIZE = 0x800
OFFSET_ONE_SEG_SIZE = 0x2c
OFFSET_DB_REVISION = 0x1a

MAX_STR_LEN = 63    # 255


def setup_known_types(blocks_dir: str | None = None) -> dict[int, str]:
    """
    Динамически собирает словарь известных типов блоков на основе файлов в папке blocks.
    
    Args:
        blocks_dir: Опциональный путь к папке. Если не передан, вычисляется автоматически.
    Returns:
        dict: {int_type: "block_name"}
    """
    if blocks_dir is None:
        plugin_dir = os.path.dirname(os.path.realpath(__file__))
        blocks_dir = os.path.join(plugin_dir, "blocks")

    # Защита: если папки physical не существует (например, при специфичном запуске тестов)
    if not os.path.exists(blocks_dir):
        return {}

    known_types = {}
    
    try:
        for f in os.listdir(blocks_dir):
            # Проверяем расширение и префикс файла
            if f.startswith("block_") and f.endswith(".py"):
                module_name = f[:-3]  # Отсекаем ".py" -> "block_0x0B"
                
                # Извлекаем HEX-часть: разбиваем по '_' и берем последний элемент
                hex_part = module_name.split("_")[-1]  # "0x0B"
                
                try:
                    block_type = int(hex_part, 16)
                    known_types[block_type] = module_name
                except ValueError:
                    # Игнорируем файлы, которые не заканчиваются на валидный HEX
                    continue
    except OSError:
        return {}

    return known_types


# Инициализация словаря блоков по умолчанию
KNOWN_BLOCKS = setup_known_types()


# ----
class VDO_FILE():
    """ класс работы с файлом формата carindb """
    # Запрещаем создание __dict__, жестко фиксируем свойства экземпляра
    __slots__ = (
        "file_path",
        "is_empty",
        "filename",
        "QGISvdoGroupName",
        "_initialized",
        "dbrev",
        "segsize",
        "file_size",
    )
    
    # Переменная класса для хранения синглтона (не входит в __slots__)
    _singleton_instance = None

    def __new__(cls, file_path: Optional[str] = None):
        """
        Если строка пустая, он должен создать singletone экземпляр этого класса
        """
        # Безопасно преобразуем None в пустую строку
        path_str = file_path or ""

        # Проверяем условия валидности файла
        is_valid_file = (
            path_str
            and os.path.exists(path_str)
            and os.path.getsize(path_str) > OFFSET_ONE_SEG_SIZE
        )

        # Если файл пустой, None, не существует или мал -> возвращаем синглтон
        if not is_valid_file:
            if cls._singleton_instance is None:
                cls._singleton_instance = super().__new__(cls)
                cls._singleton_instance._initialized = False
            return cls._singleton_instance

        # Если файл прошел все проверки -> создаем новый объект
        return super().__new__(cls)

    def __init__(self, file_path: Optional[str] = None):
        # Защита от повторной инициализации синглтона
        if hasattr(self, "_initialized") and self._initialized:
            return

        # Безопасно преобразуем None в пустую строку
        path_str = file_path or ""

        # Повторно проверяем валидность для правильной настройки атрибутов
        is_valid_file = (
            path_str
            and os.path.exists(path_str)
            and os.path.getsize(path_str) > OFFSET_ONE_SEG_SIZE
        )

        if not is_valid_file:
            # Фиксируем синглтон
            self.file_path = ""
            self.is_empty = True
            self.filename = ""
            self._initialized = True  # Фиксируем синглтон
            self.file_size = 0
            self.dbrev = DEFAULT_DB_REVISION
            self.segsize = DEFAULT_ONE_SEG_SIZE
        else:
            # Для обычных файлов
            self.file_path: str = path_str
            self.is_empty = False
            self.filename = os.path.basename(path_str)
            self._initialized = False
            self.file_size = os.path.getsize(self.file_path)
            # Используем unpack_from для безопасности типов ReadableBuffer
            self.dbrev: int = struct_WORD.unpack_from(self.read(OFFSET_DB_REVISION, 2))[0]
            # :dbrev: database revision, 30 (0x1e) or 34 (0x22)
            self.segsize: int = struct_WORD.unpack_from(self.read(OFFSET_ONE_SEG_SIZE, 2))[0]
        # для всех
        self.QGISvdoGroupName = self._create_QGISvdoGroupName()

    def __repr__(self) -> str:
        return f"VDO v.{self.dbrev}[{self.segsize}]:{self.filename}"

    def _create_QGISvdoGroupName(self) -> str | None:
        """Генерация уникального имени для корневой группы слоев QGIS."""
        if self.is_empty:
            return None
        # Замена ручного split("/") на кроссплатформенный os.path.split
        _, folder_name = os.path.split(os.path.dirname(self.file_path))
        return f"{folder_name}_0x{self.file_size:04X}"

    def read(self, offset: int, size: int) -> bytes:
        """Чтение блока байт заданной длины по указанному смещению."""
        if self.is_empty or size <= 0 or (offset + size) > self.file_size:
            return EMPTY_BUFFER
        try:
            with open(self.file_path, "rb") as f:
                f.seek(offset)
                return f.read(size)
        except (OSError, FileNotFoundError):    # pragma: no cover
            return EMPTY_BUFFER

    def get_bladdr(self, bladdr: Union[int, BLADDR]) -> BLADDR:
        """
        Args:
            bladdr :int - uint значение bladdr, BLADDR
        Returns:
            res :BLADDR с vdo self
        """
        if isinstance(bladdr, int):
            buffer = struct_UINT.pack(bladdr)
        else:
            buffer = bladdr._raw
        return BLADDR(buffer, self)

    def get_block(self, addr: Union[int, BLADDR], *args: Any) -> Any | None:
        """
        Возвращает экземпляр блока по смещению offset (int) или из структуры BLADDR.
        
        Args:
            addr: int offset | BLADDR block address
        Returns:
            Block instance или None, если адрес невалиден или это не блок.
        """
        if self.is_empty:
            return None
        if addr is None:
            return None
        
        if isinstance(addr, int):
            offset = addr
        elif isinstance(addr, BLADDR):  # Исправлена проверка типа
            if addr.isZero:  # Используем оптимизированное свойство
                return None
            # какой бы ни пришёл BLADDR, используем его только номер, и размер сегмента vdo
            offset = addr.blocknumber * self.segsize
        else:
            raise ValueError(f"Неверный тип адреса {type(addr)}: ожидается int или BLADDR")

        # Чтение заголовка блока
        head_bytes = self.read(offset, BLSTART.size)
        if len(head_bytes) < BLSTART.size:
            return None
            
        head = BLSTART(head_bytes, self)
        if head.bladdr.offset != offset:
            return None

        block_type = head.bltype.value

        # Динамический импорт класса блока
        if block_type in KNOWN_BLOCKS:
            bl_module_name = KNOWN_BLOCKS[block_type]
            # Безопасный относительный импорт без жесткого префикса QGIS_VDO
            module = importlib.import_module(f"..blocks.{bl_module_name}", package=__name__)
            bl_class = getattr(module, bl_module_name)
        else:
            module = importlib.import_module("..block_base", package=__name__)
            bl_class = getattr(module, "block_base")
            bl_module_name = "block_base"

        bl_instance = bl_class(head.bladdr, *args)
        bl_instance.type = block_type
        bl_instance.type_name = bl_module_name

        return bl_instance
        pass        # def get_block(self, addr: Union[int, BLADDR], *args: Any)

    # def get_huffman_weights(self) -> dict:
    #     """
    #     в первом блоке, 0х12 есть таблица весов для дерева хаффмана
    #     по смещению OFFSET_MAY_BE_HUFFMAN_THREE = 0x28 list(ptr|cnt)\n
    #     Таблица одна на весь файл - и логично не привязывать её к блоку
    #     Returns:
    #         weight: dict {key_id : value_weight}
    #     """
    #     OFFSET_SEEMS_LIKE_HUFFMAN_WEIGHTS = 0x28
    #     # начальный адрес таблицы весов и количество элементов.
    #     HUFFMAN_PAIR_SIZE = 4
    #     struct_WORD_TWICE = struct.Struct(">HH")

    #     weights = {}
    #     bytes_list = self.read(OFFSET_SEEMS_LIKE_HUFFMAN_WEIGHTS, HUFFMAN_PAIR_SIZE)
    #     (ptr, cnt) = struct_WORD_TWICE.unpack(bytes_list)
    #     for _ in range(cnt):
    #         (key_id, value_weight) = struct_WORD_TWICE.unpack(self.read(ptr, HUFFMAN_PAIR_SIZE))   # noqa
    #         #if 0 <= key_id <= 0xFFFF:
    #         # Нам нужны только символы с реальным весом > 0
    #         if value_weight > 0:
    #             weights[key_id] = value_weight
    #         ptr += HUFFMAN_PAIR_SIZE
    #     return weights

    # def generate_canonical_lookup(self, weights_table):
    #     """Строит каноническую lookup-мапу: { бинарная_строка: int_байт }"""
    #     full_weights = {b: 1 for b in range(256)}
    #     #for key_hex, weight in weights_table.items():
    #     for byte_id, weight in weights_table.items():
    #         try:
    #             #byte_id = int(key_hex, 16)
    #             if 0 <= byte_id <= 255:
    #                 full_weights[byte_id] = weight
    #         except ValueError:
    #             continue

    #     heap = []
    #     counter = 0
    #     for byte_id, weight in full_weights.items():
    #         heapq.heappush(heap, (weight, counter, {'id': byte_id, 'left': None, 'right': None}))  # noqa
    #         counter += 1

    #     while len(heap) > 1:
    #         w1, _, n1 = heapq.heappop(heap)
    #         w2, _, n2 = heapq.heappop(heap)
    #         heapq.heappush(heap, (w1 + w2, counter, {'id': None, 'left': n1, 'right': n2}))  # noqa
    #         counter += 1

    #     _, _, root_node = heapq.heappop(heap)
    #     code_lengths = {}
        
    #     def collect_lengths(node, current_depth):
    #         if node['id'] is not None:
    #             code_lengths[node['id']] = current_depth
    #             return
    #         if node['left']: collect_lengths(node['left'], current_depth + 1)  # noqa
    #         if node['right']: collect_lengths(node['right'], current_depth + 1)  # noqa

    #     collect_lengths(root_node, 0)
    #     sorted_elements = sorted(code_lengths.items(), key=lambda x: (x[1], x[0]))

    #     canonical_lookup = {}
    #     current_code_int = 0
    #     last_length = 0

    #     for byte_id, length in sorted_elements:
    #         if length == 0: continue  # noqa
    #         if last_length > 0:
    #             current_code_int <<= (length - last_length)
    #         bit_code = f"{current_code_int:0{length}b}"
    #         canonical_lookup[bit_code] = byte_id
    #         current_code_int += 1
    #         last_length = length

    #     return canonical_lookup

    # def generate_huffman_lookup(self, weights_table: dict) -> dict:
    #     """
    #     Автоматически строит дерево Хаффмана на основе таблицы весов
    #     для ключей в диапазоне от 0x0000 до 0xA000.
    #     Args:
    #         weights_table: dict - таблица весов
    #     Returns:
    #         словарь соответствия: { 'бинарный_код_строкой': декодированное_значение }
    #     """
    #     # Очередь с приоритетами (куча) для сборки дерева
    #     heap = []
    #     counter = 0
        
    #     for key_title, weight in weights_table.items():
    #         node = {'id': key_title, 'left': None, 'right': None}
    #         # Формат элемента: (вес, уникальный_счетчик, узел_дерева)
    #         heapq.heappush(heap, (weight, counter, node))
    #         counter += 1

    #     if not heap:
    #         return {}

    #     # Построение дерева Хаффмана путем слияния минимальных узлов
    #     while len(heap) > 1:
    #         weight1, _, node1 = heapq.heappop(heap)
    #         weight2, _, node2 = heapq.heappop(heap)
            
    #         parent_node = {'id': None, 'left': node1, 'right': node2}
    #         parent_weight = weight1 + weight2
            
    #         heapq.heappush(heap, (parent_weight, counter, parent_node))
    #         counter += 1

    #     # Корень финального дерева
    #     _, _, root_node = heapq.heappop(heap)       # там 1 элемент, heap[0]
    #     # _, _, root_node = heapq.heappop(heap)  #  heap
    #     huffman_lookup = {}
        
    #     # Рекурсивный обход дерева для генерации префиксных битовых кодов
    #     def walk_tree(node, current_code):
    #         if node['id'] is not None:
    #             val_id = node['id']
    #             """
    #             # noqa:
    #             # Логика интерпретации ID в конечный символ или токен
    #             # if val_id == 0x00:
    #             #     char_out = "[EOS]"                      # Маркер конца строки
    #             # elif 0x41 <= val_id <= 0x5A:
    #             #     char_out = chr(val_id).lower()          # Перевод латиницы A-Z в нижний регистр a-z
    #             # elif 32 <= val_id <= 126:
    #             #     char_out = chr(val_id)                  # Остальной печатный ASCII
    #             # elif 0x0400 <= val_id <= 0x04FF:
    #             #     char_out = chr(val_id)                  # Кириллица (Unicode), если присутствует в СНГ-версии
    #             # else:
    #             #     char_out = f"[Token_0x{val_id:04X}]"    # Крупные токены координат или гео-префиксов
    #             """
    #             # huffman_lookup[current_code] = char_out
    #             huffman_lookup[current_code] = val_id
    #             return
            
    #         # Левая ветка кодируется нулем, правая — единицей
    #         if node['left']:
    #             walk_tree(node['left'], current_code + "0")
    #         if node['right']:
    #             walk_tree(node['right'], current_code + "1")

    #     # Запускаем обход от корня
    #     walk_tree(root_node, "")
    #     return huffman_lookup

    
# ================================================

class BYTESTRUCT:
    """Base for other data structures"""

    # Жестко выделяем память только под _raw
    __slots__ = ("_raw",)

    def __init__(self, buffer: ReadableBuffer, size: int | None = None) -> None:
        if not (isinstance(buffer, ReadableBuffer) or isinstance(buffer, memoryview) or isinstance(buffer, bytearray)):
            raise TypeError("buffer must be ReadableBuffer", type(buffer))
        # Создаем memoryview. Если buffer уже memoryview, избегаем двойного оборачивания
        view = buffer if isinstance(buffer, memoryview) else memoryview(buffer)
        self._raw: memoryview = view[:size]

    def __repr__(self) -> str:
        return self.hex

    @property
    def hex(self) -> str:
        raw_hex = self._raw.hex().upper()
        chunks = []
        # Шаг 32 символа = 16 байт
        for i in range(0, len(raw_hex), 32):
            line = raw_hex[i : i + 32]
            length = len(line)
            if length == 32:
                chunks.append(f"{line[:16]}  {line[16:]}")
            elif length > 16:
                # Если хвост больше 8 байт, бьем на 8 байт + остаток
                chunks.append(f"{line[:16]} {line[16:]}")
            else:
                # Если хвост меньше или равен 8 байтам
                chunks.append(line)

        return "   ".join(chunks)

    def len(self) -> int:
        """length raw in bytes"""
        return len(self._raw)

    def read(self, offset: int, cnt: int) -> memoryview:
        """read from inner bytes array (returns zero-copy view)"""
        return self._raw[offset : offset + cnt]

    def read_str(self, ptr: int, max_len: int | None = None) -> str:
        """Чтение 0-ended строки БЕЗ копирования и лишнего выделения памяти

        Args:
            ptr: offset в текущем _raw
        Returns:
            str: декодированная строка до первого \x00
        """
        limit = max_len if max_len is not None else MAX_STR_LEN
        sub_view = self._raw[ptr : ptr + limit]

        # Ищем 0x00 перебором прямо по memoryview БЕЗ вызова .tobytes()
        # Для memoryview итерация возвращает int (коды байт)
        null_idx = next((i for i, b in enumerate(sub_view) if b == 0), None)

        if null_idx is not None:
            sub_view = sub_view[:null_idx]

        # Декодируем напрямую через bytes(sub_view) - копия создается только 1 раз при десериализации
        return bytes(sub_view).decode("cp1250")

    def uchar(self, near_offset: int = 0) -> int:
        """Return uchar, offset from _raw begin"""
        return self._raw[near_offset]

    def ushort(self, near_offset: int = 0) -> int:
        """Return unsigned short (2 bytes, word), offset from _raw begin"""
        return struct_WORD.unpack_from(self._raw, near_offset)[0]

    def uint(self, near_offset: int = 0) -> int:
        """Return unsigned int (4 bytes, dword), offset from _raw begin"""
        return struct_UINT.unpack_from(self._raw, near_offset)[0]


class BLADDR(BYTESTRUCT):
    """
    b'\x01\x02\x03\x04' -> 0x010203 - number, 04 - len in blocks
    """
    # Фиксируем слоты. Базовый '_raw' уже унаследован, здесь пишем только новые поля
    __slots__ = ('vdo',)
    
    size: int = UINT_BYTES_CNT

    def __init__(self, buffer: ReadableBuffer, vdo: getattr = None) -> None:
        # Передаем буфер строго фиксированной длины в базовый класс
        super().__init__(buffer, size=UINT_BYTES_CNT)
        
        # Экономим память: создаем новый VDO_FILE() - singletone
        if vdo is None:
            self.vdo = VDO_FILE()    # EMPTY_VDO
        elif isinstance(vdo, VDO_FILE):
            self.vdo = vdo
        else:
            raise AttributeError(f"vdo должен быть или VDO_FILE или никаким, но не {type(vdo)}")

    @property
    def isZero(self) -> bool:
        """Быстрая проверка на нулевой dword без сравнения массивов байт"""
        return self.value == 0
    
    @property
    def value(self) -> int:
        """Числовое значение всего dword (Big-Endian)"""
        # Индекс [0] обязателен, если unpack_from возвращает кортеж (val,)
        return struct_UINT.unpack_from(self._raw, 0)[0]

    @property
    def blocknumber(self) -> int:
        """Номер блока (первые 3 байта). Работает моментально через битовый сдвиг."""
        return self.value >> 8
    
    @property
    def segcnt(self) -> int:
        """Размер в сегментах (последний 4-й байт)"""
        return self._raw[3]
    
    @property
    def sizeofblock(self) -> int:
        """Размер описываемого блока в байтах"""
        return self.segcnt * self.vdo.segsize
    
    @property
    def offset(self) -> int:
        """Смещение от начала файла"""
        return self.blocknumber * self.vdo.segsize
    
    def next_block_offset(self) -> int:
        return self.offset + self.sizeofblock

    @property
    def hex(self) -> str:
        # Вывод номера блока в 6 символов hex и размера сегмента в 2 символа hex
        return f'{self.blocknumber:06x} {self._raw[3]:02x}'

    def __repr__(self) -> str:
        v = ' virt' if self.vdo.is_empty else ''
        return self.hex + v
    
    def _check_context(self, other: 'BLADDR') -> None:
        """Внутренняя проверка на совместимость контекстов данных"""
        if self.vdo.segsize != other.vdo.segsize:
            raise ValueError(
                f"Cannot compare BLADDR with different segsize: {self.vdo.segsize} != {other.vdo.segsize}"
            )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BLADDR):
            return NotImplemented
        self._check_context(other)
        return self.blocknumber == other.blocknumber
    
    def __lt__(self, other: object) -> bool:
        if not isinstance(other, BLADDR):
            return NotImplemented
        self._check_context(other)
        return self.blocknumber < other.blocknumber

    def __le__(self, other: object) -> bool:
        if not isinstance(other, BLADDR):
            return NotImplemented
        self._check_context(other)
        return self.blocknumber <= other.blocknumber


# ----
class PTR(BYTESTRUCT):
    ''' Указатель(near) 01 02 -> near offset 0x102 '''
    # Класс не вводит новых переменных, но чтобы не создавался __dict__,
    # нужно явно объявить пустые __slots__
    __slots__ = ()

    size: int = USHORT_BYTES_CNT

    def __init__(self, buffer: ReadableBuffer) -> None:
        # Передаем буфер фиксированного размера (2 байта) напрямую в базовый класс
        super().__init__(buffer, size=USHORT_BYTES_CNT)
    
    def __repr__(self) -> str:
        """Отображение значения при отладке в правильном 16-битном формате (4 символа)"""
        return f"0x{self.value:04X}"
 
    @property
    def value(self) -> int:
        ''' Near ptr to begin list'''
        #p = struct_WORD.unpack(self._raw)[0]
        return self.ushort()
    
    @property
    def hexptr(self) -> str:
        """Возвращает указатель в виде hex-строки фиксированной длины 4 символа (0x0000)"""
        return f"0x{self.value:04X}"

    @property
    def isZero(self) -> bool:
        """True, если указатель нулевой (пустой)"""
        return self.value == 0
    
    
# ----
class LIST(BYTESTRUCT):
    ''' ptr: указатель(near) на начало массива; cnt: количество элементов
    b'\x01\x02\x03\x04' -> near offset 0x102, counter items 0x304 '''
    # Сохраняем оптимизацию памяти базового класса, запрещая создание __dict__
    __slots__ = ()

    size: int = 4       # UINT_BYTES_CNT

    def __init__(self, buffer: ReadableBuffer) -> None:
        # Жестко ограничиваем буфер размером структуры (4 байта)
        super().__init__(buffer, size=4)         # 4 - self.bytescnt

    def __repr__(self):
        ''' View while debug value'''
        return f"{self.ptr:04X}:{self.cnt:04X} cnt:{self.cnt}"
        
    @property
    def ptr(self) -> int:
        ''' Near ptr to begin list'''
        return self.ushort(0)

    @property
    def cnt(self) -> int:
        ''' List counter '''
        return self.ushort(2)
 

# ----
class FAR_LIST(BYTESTRUCT):
    """
    Композитная структура: BLADDR (4 байта) + LIST (4 байта).
    Общий размер: 8 байт.
    """
    # Жестко фиксируем поля в памяти. __dict__ больше не создается!
    __slots__ = ('vdo', '_bladdr_obj', '_list_obj')
    
    size: int = DOUBLE_BYTES_CNT

    def __init__(self, buffer: ReadableBuffer, vdo: Union[VDO_FILE, None] = None) -> None:
        # Инициализируем базовый буфер размером 8 байт
        super().__init__(buffer, size=DOUBLE_BYTES_CNT)
        
        # Защита от создания лишних тяжелых инстансов VDO
        # Используем встроенное свойство uint базового класса для мгновенной проверки первых 4 байт
        if vdo is None:
            self.vdo = VDO_FILE()    # EMPTY_VDO
        elif isinstance(vdo, VDO_FILE):
            if self.uint(0) == 0:
                self.vdo = VDO_FILE()    # EMPTY_VDO
            else:
                self.vdo = vdo
        else:
            raise AttributeError(f"vdo '{vdo}' is not VDO_FILE: {type(vdo)}")
            
        # ОПТИМИЗАЦИЯ: Создаем дочерние структуры ОДИН раз при инициализации.
        # Передаем zero-copy срезы memoryview, чтобы избежать копирования байт.
        self._bladdr_obj = BLADDR(self._raw[:UINT_BYTES_CNT], self.vdo)
        self._list_obj = LIST(self._raw[UINT_BYTES_CNT:])
    
    def __repr__(self):
        ''' View while debug value'''
        return self.hex
    
    @property
    def bladdr(self) -> BLADDR:
        """Возвращает кэшированный объект адреса блока (без создания нового)"""
        return self._bladdr_obj

    @property
    def list(self) -> LIST:
        """Возвращает кэшированный объект списка (без создания нового)"""
        return self._list_obj

    @property
    def offset(self) -> int:
        """Смещение от начала файла: смещение блока + смещение внутри списка"""
        return self._bladdr_obj.offset + self._list_obj.ptr

    @property
    def hex(self) -> str:
        """Форматированный вывод отладочной информации"""
        return f"{repr(self._bladdr_obj)} : {repr(self._list_obj)}"
    

# сложные составные типы
# ==========
class CH_IDX(BYTESTRUCT):
    '''
    CH_IDX   3*DWORD, указатель на список букв или (страны, города, улицы, poi)
        0  DWORD bl_postaddr адрес блока
        4  byte  ch    собственно буква
        5  byte  is_ptr_out = 0 на индекс (CH_idx 0b,0d,0f,11), 1 - на описание (0a,0c,0e,10)
        6 LIST  pointer-counter в bl_postaddr
        10 WORD  align
    '''
    # Запрещаем создание __dict__ для CH_IDX и фиксируем внутренний кэш объектов
    __slots__ = ('vdo', '_bladdr_obj', '_list_obj')
    
    size: int = 12

    def __init__(self, buffer: ReadableBuffer, vdo: Union[VDO_FILE, None] = None) -> None:
        # Быстрая проверка длины за O(1) без оборачивания в memoryview
        if len(buffer) < self.size:
            raise TypeError(f"Размер массива байтов {len(buffer)} меньше требуемого {self.size}")
            
        super().__init__(buffer, size=self.size)
        
        # Используем глобальный EMPTY_VDO, если контекст не задан или адрес пустой
        if vdo is None:
            self.vdo = VDO_FILE()    # EMPTY_VDO
        elif isinstance(vdo, VDO_FILE):
            if self.uint(0) == 0:
                self.vdo = VDO_FILE()    # EMPTY_VDO
            else:
                self.vdo = vdo
        else:
            raise AttributeError(f"У vdo неверный тип: {type(vdo)}")

        # ОПТИМИЗАЦИЯ: Создаем и кэшируем вложенные типы строго один раз при инициализации
        self._bladdr_obj = BLADDR(self._raw[:4], self.vdo)
        # LIST занимает строго 4 байта с 6-го по 10-й индекс
        self._list_obj = LIST(self._raw[6:10])

    def __repr__(self) -> str:
        return f"'{self.ch}' out:{int(self.is_out)} {repr(self._bladdr_obj)} : {repr(self._list_obj)}"
    
    @property
    def bladdr(self) -> BLADDR:
        """Возвращает кэшированный объект адреса блока (zero-allocation)"""
        return self._bladdr_obj
    
    @property
    def ch(self) -> str:
        """Декодированная буква (байт 4) с поддержкой расширенной таблицы cp1250"""
        raw_byte = self._raw[4]
        if raw_byte < 128:
            return chr(raw_byte)
        return bytes([raw_byte]).decode('cp1250')

    @property
    def is_out(self) -> bool:
        """ offset 6 :is_ptr_out - flag
        0 - на индекс (CH_idx 0b,0d,0f,11)
        1 - на описание (0a,0c,0e,10) """
        return self._raw[5] != 0

    @property
    def list(self) -> LIST:
        """Возвращает кэшированный объект списка LIST (zero-allocation)"""
        return self._list_obj


# ==========
class BLSTART(BYTESTRUCT):
    """ Первый DWORD любого блока
        offset  type  sense         value
        00   dword   BLADDR          00000001 always
        04   word    bl_type         0012
        06   char    is_arch         00-not arch, 01- ???, 02-lzw
        07   char    unarch_size
    """
    # Фиксируем слоты, предотвращая появление __dict__ и кэшируя композиты
    __slots__ = ('vdo', '_bladdr_obj')
    
    size: int = 8  # DOUBLE_BYTES_CNT

    def __init__(self, buffer: ReadableBuffer, vdo: Union[VDO_FILE, None] = None) -> None:
        if len(buffer) < self.size:
            raise TypeError(f"Размер массива байтов {len(buffer)} меньше требуемого {self.size}")
        if vdo is not None and not isinstance(vdo, VDO_FILE):
            raise TypeError(f"Тип vdo {len(buffer)} не VDO_FILE и не None")
            
        super().__init__(buffer, size=self.size)
        
        # Используем оптимизированный синглтон-заглушку
        if not vdo or self.uint(0) == 0:
            self.vdo = VDO_FILE()    # EMPTY_VDO
        else:
            self.vdo = vdo

        # Кэшируем BLADDR один раз при инициализации
        self._bladdr_obj = BLADDR(self._raw[:4], self.vdo)

    def __repr__(self) -> str:
        v = '' if self.vdo.path else ' virt'
        try:
            type_name = self.bltype.name
        except ValueError:
            type_name = "UNKNOWN"
        return f"{self.headhex()}{v} [{self.bltype.value:02X}:{type_name}]"
    
    @property
    def bladdr(self) -> BLADDR:
        """Возвращает кэшированный объект адреса блока (zero-allocation)"""
        return self._bladdr_obj

    @property
    def bltype(self) -> BlockType:
        """Возвращает валидный элемент BlockType"""
        bltype_val = self.ushort(4)     # OFFSET_TYPE = 4
        # Безопасный поиск по значению enum
        try:
            return BlockType(bltype_val)
        except ValueError:
            return BlockType.UNKNOWN

    def headhex(self) -> str:
        """Строковое представление заголовка в соответствии с разметкой байт"""
        # Читаем байты 6 и 7 раздельно, как заложено в структуре
        return f"{self.uint(0):08X} {self.ushort(4):04X} {self._raw[6]:02X} {self._raw[7]:02X}"

    @property
    def segcnt(self) -> int:
        """Количество сегментов после распаковки"""
        if self.arch_type:
            return self._raw[7]  # OFFSET_UNARC_SEGS = 7
        return self._bladdr_obj.segcnt
    
    @property
    def arch_type(self) -> int:
        """2 - zlib, 1 - bytype, 0 - не сжато"""
        return self._raw[6]  # OFFSET_ARC_TYPE = 6
    
    @property
    def sizeofblock(self) -> int:
        """Размер распакованного блока в байтах"""
        if self.arch_type:
            return self.segcnt * self.vdo.segsize
        return self._bladdr_obj.sizeofblock

# class PSTR(PTR):
#     ''' PSTR    WORD, nearPTR на zero-ended строку '''
#     strval:str
#     bytescnt: int = 2  # CH_IDX size = 3 * DWORD
#     def __init__(self, bytes_arr) -> None:
#         super().__init__(bytes_arr[:self.bytescnt]) # 4 - self.bytescnt


# =========================================================================
if __name__ == '__main__':      # pragma: no cover
    # Весь этот блок теперь официально игнорируется тестами
    
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
