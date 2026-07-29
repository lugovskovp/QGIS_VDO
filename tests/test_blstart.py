import pytest   # type: ignore # noqa
from QGIS_VDO.vdo.datatypes import BLSTART, BlockType


def test_blstart_uncompressed_block(custom_vdo):
    """Тест парсинга несжатого блока известного типа (ABSTRACT=0x12)."""
    # 8 байт:
    # [0:4] -> BLADDR (block 1, segcnt 5)
    # [4:6] -> Type 0x0012 (ABSTRACT)
    #   -> Is_arch = 0 (Не сжато)
    #   -> Unarch_size = 0
    buffer = b'\x00\x00\x01\x05\x00\x12\x00\x00'
    
    head = BLSTART(buffer, vdo=custom_vdo)
    
    assert head.bltype == BlockType.ABSTRACT
    assert head.arch_type == 0
    assert head.bladdr.blocknumber == 1
    assert head.segcnt == 5  # Берется из bladdr
    assert head.sizeofblock == 5 * custom_vdo.segsize


def test_blstart_compressed_block(custom_vdo):
    """Тест парсинга сжатого блока (COUNTRY=0x0A) со своими сегментами."""
    # [4:6] -> Type 0x000A (COUNTRY)
    #   -> Is_arch = 2 (zlib)
    #   -> Unarch_size = 12 сегментов
    buffer = b'\x00\x00\x01\x05\x00\x0A\x02\x0C'
    
    head = BLSTART(buffer, vdo=custom_vdo)
    
    assert head.bltype == BlockType.COUNTRY
    assert head.arch_type == 2
    assert head.segcnt == 12  # Переопределено по смещению 7
    assert head.sizeofblock == 12 * custom_vdo.segsize


def test_blstart_unknown_type_safety(custom_vdo):
    """Проверка защиты от падения (ValueError) при встрече с неизвестным типом блока."""
    # Передаем несуществующий тип типа 0x9999
    buffer = b'\x00\x00\x01\x05\x99\x99\x00\x00'
    head = BLSTART(buffer, vdo=custom_vdo)
    
    assert head.bltype == BlockType.UNKNOWN


def test_blstart_slots_and_caching(custom_vdo):
    """Проверка сохранения идентичности кэша свойств и изоляции slots."""
    buffer = b'\x00\x00\x01\x05\x00\x12\x00\x00'
    head = BLSTART(buffer, vdo=custom_vdo)
    
    assert head.bladdr is head.bladdr  # Кэш работает
    assert not hasattr(head, '__dict__')
