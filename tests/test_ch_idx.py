import pytest   # type: ignore # noqa
from QGIS_VDO.vdo.datatypes import CH_IDX


def test_ch_idx_exact_offsets(custom_vdo):
    """Проверка распаковки по точным смещениям байт (0, 4, 5, 6, 10)."""
    # Формируем 12 байт:
    # [0:4]   b'\x00\x00\x00\x10' -> BLADDR: block 16
    # [4]     b'R' (0x52)         -> Буква 'R'
    # [5]     b'\x01'             -> is_out = True
    # [6:10]  b'\x0A\x0B\x00\x02' -> LIST: ptr=0x0A0B, cnt=2
    # [10:12] b'\x00\x00'         -> Align (WORD)
    buffer = b'\x00\x00\x10\x01R\x01\x0A\x0B\x00\x02\x00\x00'
    
    idx = CH_IDX(buffer, vdo=custom_vdo)
    
    assert idx.ch == "R"
    assert idx.is_out is True
    assert idx.bladdr.blocknumber == 16
    assert idx.list.ptr == 0x0A0B
    assert idx.list.cnt == 2


def test_ch_idx_cp1250_encoding(custom_vdo):
    """Проверка, что символы cp1250 выше диапазона ASCII (>127) не ломаются."""
    # 0xC6 в кодировке cp1250 — это заглавная буква 'Ć'
    buffer = b'\x00\x00\x00\x00\xC6\x00\x00\x00\x00\x00\x00\x00'
    idx = CH_IDX(buffer, vdo=custom_vdo)
    
    assert idx.ch == "Ć"


def test_ch_idx_property_caching(custom_vdo):
    """Проверка, что свойства .bladdr и .list сохраняют один и тот же объект в памяти."""
    buffer = b'\x00' * 12
    idx = CH_IDX(buffer, vdo=custom_vdo)
    
    first_bladdr = idx.bladdr
    first_list = idx.list
    
    assert idx.bladdr is first_bladdr
    assert idx.list is first_list


def test_ch_idx_slots_integrity(custom_vdo):
    """Проверка полной изоляции памяти CH_IDX от динамических __dict__ словарей."""
    idx = CH_IDX(b'\x00' * 12, vdo=custom_vdo)
    
    assert not hasattr(idx, '__dict__')
    assert not hasattr(idx.bladdr, '__dict__')
    assert not hasattr(idx.list, '__dict__')
    
    with pytest.raises(AttributeError):
        idx.new_dynamic_field = "fail"
