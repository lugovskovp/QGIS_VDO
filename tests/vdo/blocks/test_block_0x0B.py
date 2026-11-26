"""
Тесты для block_0x0B — CH_country (страны и их индексы символов).

Покрытие:
- Инициализация и чтение li_toc
- get_chidxs() — словарь str -> CH_IDX
- get_chidxs_iter() — итератор по CH_IDX
- find_chidx() — поиск по символу страны
- Кэширование li_toc
- __slots__ и оптимизация памяти
"""
import pytest

from QGIS_VDO.vdo.datatypes import VDO_FILE, BLADDR, LIST, CH_IDX
from QGIS_VDO.vdo.blocks import block_0x0B, block_0x12

from QGIS_VDO.tests.fixtures import FIXTURES_DIR


# ---------------------------------------------------------------------------
# Фикстуры
# ---------------------------------------------------------------------------

VDO_DICT = {
    "carindb30_0h_9000h.bin": {
        "name": "ru30",
        "dbrev": 30,
        "expected_chars": ["a", "b", "c"],
    },
    "carindb34_0h_6800h.bin": {
        "name": "ce34",
        "dbrev": 34,
        "expected_chars": ["b", "c", "e"],
    },
    "DB34_0h_3A01h.bin": {
        "name": "bmw34",
        "dbrev": 34,
        "expected_chars": ["a", "b", "c"],
    },
}


@pytest.fixture(
    scope="function",
    params=list(VDO_DICT),
    ids=[VDO_DICT[k]["name"] for k in VDO_DICT],
)
def block_0x0b_fixture(request):
    """
    Фикстура возвращает блок 0x0B, полученный из фикстуры через block_0x12.bladdr_ch_country.
    """
    filename = request.param
    metric = VDO_DICT[filename]
    vdo = VDO_FILE(FIXTURES_DIR / filename)
    bl_toc: block_0x12 = vdo.get_block(0)
    bladdr_ch_country: BLADDR = bl_toc.bladdr_ch_country
    block: block_0x0B = vdo.get_block(bladdr_ch_country)
    return block, metric


# ---------------------------------------------------------------------------
# Базовые тесты инициализации
# ---------------------------------------------------------------------------

def test_block_0x0b_init(block_0x0b_fixture):
    """Блок 0x0B инициализируется и привязан к vdo."""
    block, metric = block_0x0b_fixture
    assert block.vdo is not None
    assert block.vdo.dbrev == metric["dbrev"]
    assert block.type == 0x0B


def test_block_0x0b_slots_are_effective(block_0x0b_fixture):
    """Проверяем, что блок 0x0B использует __slots__ и не создаёт __dict__."""
    block, _ = block_0x0b_fixture
    assert not hasattr(block, "__dict__")
    assert hasattr(block, "__slots__")
    assert "vdo" in block.__slots__
    assert "_li_toc_cache" in block.__slots__


# ---------------------------------------------------------------------------
# li_toc — чтение и кэширование
# ---------------------------------------------------------------------------

def test_block_0x0b_li_toc_is_list(block_0x0b_fixture):
    """li_toc возвращает экземпляр LIST."""
    block, _ = block_0x0b_fixture
    li = block.li_toc
    assert isinstance(li, LIST)
    assert isinstance(li.ptr, int)
    assert isinstance(li.cnt, int)


def test_block_0x0b_li_toc_cache(block_0x0b_fixture):
    """li_toc кэшируется — повторный вызов возвращает тот же объект."""
    block, _ = block_0x0b_fixture
    li1 = block.li_toc
    li2 = block.li_toc
    assert li1 is li2
    # Кэш должен быть не None
    assert block._li_toc_cache is li1


# ---------------------------------------------------------------------------
# get_chidxs_iter() — итератор (закомментировано в block_0x0B, см. TODO)
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="get_chidxs_iter закомментирован в block_0x0B")
def test_block_0x0b_get_chidxs_iter_type(block_0x0b_fixture):
    """get_chidxs_iter возвращает итератор, элементы — CH_IDX."""
    block, _ = block_0x0b_fixture
    iterator = block.get_chidxs_iter()
    # Проверяем, что итератор не пустой
    first = next(iterator)
    assert isinstance(first, CH_IDX)


@pytest.mark.skip(reason="get_chidxs_iter закомментирован в block_0x0B")
def test_block_0x0b_get_chidxs_iter_count(block_0x0b_fixture):
    """get_chidxs_iter возвращает корректное количество элементов."""
    block, _ = block_0x0b_fixture
    items = list(block.get_chidxs_iter())
    assert len(items) == block.li_toc.cnt
    for item in items:
        assert isinstance(item, CH_IDX)


# ---------------------------------------------------------------------------
# get_chidxs() — словарь (закомментировано в block_0x0B, см. TODO)
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="get_chidxs закомментирован в block_0x0B")
def test_block_0x0b_get_chidxs_returns_dict(block_0x0b_fixture):
    """get_chidxs возвращает словарь str -> CH_IDX."""
    block, _ = block_0x0b_fixture
    result = block.get_chidxs()
    assert isinstance(result, dict)
    for key, value in result.items():
        assert isinstance(key, str)
        assert isinstance(value, CH_IDX)


@pytest.mark.skip(reason="get_chidxs/get_chidxs_iter закомментированы в block_0x0B")
def test_block_0x0b_get_chidxs_keys_match_iter(block_0x0b_fixture):
    """Ключи словаря get_chidxs() совпадают с буквами из итератора."""
    block, _ = block_0x0b_fixture
    d = block.get_chidxs()
    it_chars = {chi.ch for chi in block.get_chidxs_iter()}
    assert set(d.keys()) == it_chars


@pytest.mark.skip(reason="get_chidxs/get_chidxs_iter закомментированы в block_0x0B")
def test_block_0x0b_get_chidxs_values_match_iter(block_0x0b_fixture):
    """Значения словаря get_chidxs() — те же объекты CH_IDX, что и в итераторе."""
    block, _ = block_0x0b_fixture
    d = block.get_chidxs()
    # get_chidxs() создаёт новый словарь из итератора,
    # поэтому объекты CH_IDX — одни и те же (итератор не копирует)
    iter_list = list(block.get_chidxs_iter())
    for chi in iter_list:
        assert chi.ch in d
        assert d[chi.ch].ch == chi.ch
        assert d[chi.ch].bladdr.value == chi.bladdr.value


# ---------------------------------------------------------------------------
# find_chidx() — поиск по символу (закомментировано в block_0x0B, см. TODO)
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="find_chidx закомментирован в block_0x0B")
def test_block_0x0b_find_chidx_found(block_0x0b_fixture):
    """find_chidx находит существующий символ и возвращает CH_IDX."""
    block, metric = block_0x0b_fixture
    for ch in metric["expected_chars"]:
        result = block.find_chidx(ch)
        assert result is not None
        assert isinstance(result, CH_IDX)
        assert result.ch == ch


@pytest.mark.skip(reason="find_chidx закомментирован в block_0x0B")
def test_block_0x0b_find_chidx_not_found(block_0x0b_fixture):
    """find_chidx для несуществующего символа возвращает None."""
    block, _ = block_0x0b_fixture
    result = block.find_chidx("Z")
    assert result is None


@pytest.mark.skip(reason="find_chidx закомментирован в block_0x0B")
def test_block_0x0b_find_chidx_empty_string(block_0x0b_fixture):
    """find_chidx для пустой строки возвращает None."""
    block, _ = block_0x0b_fixture
    result = block.find_chidx("")
    assert result is None


# ---------------------------------------------------------------------------
# Интеграционные проверки (закомментировано в block_0x0B, см. TODO)
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="get_chidxs/get_chidxs_iter/find_chidx закомментированы в block_0x0B")
def test_block_0x0b_full_roundtrip(block_0x0b_fixture):
    """Полный цикл: iter -> dict -> find — согласованность."""
    block, metric = block_0x0b_fixture
    # Из итератора строим ожидаемый набор букв
    expected_chars = {chi.ch for chi in block.get_chidxs_iter()}
    # Словарь должен содержать те же ключи
    d = block.get_chidxs()
    assert set(d.keys()) == expected_chars
    # find_chidx должен находить каждый
    for ch in expected_chars:
        assert block.find_chidx(ch) is not None
        assert block.find_chidx(ch).ch == ch


@pytest.mark.skip(reason="get_chidxs_iter закомментирован в block_0x0B")
def test_block_0x0b_chidx_bladdr_context(block_0x0b_fixture):
    """CH_IDX.bladdr привязан к тому же vdo, что и блок."""
    block, _ = block_0x0b_fixture
    for chi in block.get_chidxs_iter():
        assert chi.vdo is block.vdo
        assert chi.bladdr.vdo is block.vdo
