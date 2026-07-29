import pytest   # type: ignore
from QGIS_VDO.vdo.datatypes import BLADDR, VDO_FILE  # Настройте импорт BYTESTRUCT

# Константы для тестирования
ZERO_DWORD = b'\x00\x00\x00\x00'


def test_bladdr_parsing_big_endian(custom_vdo):
    """Тест разбора полей адреса блока из сырых байт (Big-Endian)."""
    # b'\x00\x02\x03\x04'
    # В Big-Endian первые 3 байта: 0x000203 -> 515 (номер блока)
    # Последний байт: 0x04 -> 4 (количество сегментов)
    raw_bytes = b'\x00\x02\x03\x04'
    
    addr = BLADDR(raw_bytes, vdo=custom_vdo)
    
    assert addr.isZero is False
    assert addr.blocknumber == 515
    assert addr.segcnt == 4
    assert addr.value == 0x00020304  # Проверка полной uint-структуры
    
    # Проверка математики смещений (515 * 2048)
    assert addr.offset == 515 * 2048
    assert addr.sizeofblock == 4 * 2048
    assert addr.next_block_offset() == (515 * 2048) + (4 * 2048)


def test_bladdr_zero_stub():
    """Тест обработки пустой (нулевой) заглушки."""
    addr = BLADDR(ZERO_DWORD)
    
    assert addr.isZero is True
    assert addr.blocknumber == 0
    assert addr.segcnt == 0
    assert addr.offset == 0
    assert addr.sizeofblock == 0


@pytest.mark.parametrize(
    "raw_bytes, expected_hex, expected_repr_virt",
    [
        (b'\x00\x00\x01\x08', "000001 08", "000001 08 virt"),
        (b'\x0A\x0B\x0C\x02', "0a0b0c 02", "0a0b0c 02 virt"),
        (b'\xFF\xFF\xFF\xFF', "ffffff ff", "ffffff ff virt"),
    ]
)
def test_bladdr_formatting_and_repr_virtual(raw_bytes, expected_hex, expected_repr_virt):
    """Параметризованный тест hex-форматирования и виртуального repr (без vdo.path)."""
    addr = BLADDR(raw_bytes)  # Инициализация без vdo создаст виртуальный VDO_FILE()
    
    assert addr.hex == expected_hex
    assert repr(addr) == expected_repr_virt


def test_bladdr_repr_with_path(custom_vdo):
    """Тест repr, когда у файла VDO задан путь (слово 'virt' должно отсутствовать)."""
    addr = BLADDR(b'\x00\x00\x05\x01', vdo=custom_vdo)
    assert repr(addr) == "000005 01"


def test_bladdr_comparisons(custom_vdo):
    """Тест всех операторов сравнения (__eq__, __lt__, __le__) между блоками."""
    # Блоки с одинаковым размером сегмента (custom_vdo.segsize = 2048)
    addr1 = BLADDR(b'\x00\x00\x10\x01', vdo=custom_vdo)  # Блок 16, размер 1
    addr2 = BLADDR(b'\x00\x00\x10\x05', vdo=custom_vdo)  # Блок 16, размер 5 (номера равны!)
    addr3 = BLADDR(b'\x00\x00\x20\x01', vdo=custom_vdo)  # Блок 32, размер 1
    
    # Блок с другим размером сегмента
    different_vdo = VDO_FILE()
    different_vdo.segsize = 4096
    addr_diff_vdo = BLADDR(b'\x00\x00\x10\x01', vdo=different_vdo)

    # 1. Проверка равенства в рамках одного контекста
    assert addr1 == addr2
    assert addr1 != addr3

    # 2. Проверка оператора "меньше" (<)
    assert addr1 < addr3
    assert not (addr3 < addr1)
    assert not (addr1 < addr2)  # Номера блоков равны

    # 3. Проверка оператора "меньше или равно" (<=)
    assert addr1 <= addr2  # Равны
    assert addr1 <= addr3  # Меньше
    assert not (addr3 <= addr1)

    # 4. ПРОВЕРКА ЗАЩИТЫ: Разные segsize должны вызывать ValueError, а не молча возвращать False
    with pytest.raises(ValueError, match="Cannot compare BLADDR with different segsize"):
        _ = addr1 == addr_diff_vdo

    with pytest.raises(ValueError, match="Cannot compare BLADDR with different segsize"):
        _ = addr1 < addr_diff_vdo

    with pytest.raises(ValueError, match="Cannot compare BLADDR with different segsize"):
        _ = addr1 <= addr_diff_vdo


def test_bladdr_comparison_with_invalid_type(custom_vdo):
    """Проверка, что сравнение с другими типами возвращает NotImplemented (или False)."""
    addr = BLADDR(b'\x00\x00\x10\x01', vdo=custom_vdo)
    
    # В Python сравнение с левым типом через ассерты падает или возвращает False
    assert (addr == "не BLADDR объект") is False
    
    with pytest.raises(TypeError):
        # Операторы сравнения величин (<, <=) при NotImplemented вызывают TypeError
        _ = addr < 42


def test_bladdr_slots_memory_efficiency():
    """Убеждаемся, что дочерний класс зафиксирован в памяти и не имеет __dict__."""
    addr = BLADDR(b'\x00\x00\x00\x01')
    
    # Наличие __slots__ гарантирует отсутствие словаря динамических атрибутов
    assert not hasattr(addr, "__dict__")
    
    # Попытка динамически добавить не зарегистрированное свойство должна упасть
    with pytest.raises(AttributeError):
        addr.custom_dynamic_variable = "test"  # type: ignore
