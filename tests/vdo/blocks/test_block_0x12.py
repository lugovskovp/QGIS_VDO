import pytest   # type: ignore # noqa

# from pathlib import Path

# from QGIS_VDO.vdo.blocks import block_0x12
from QGIS_VDO.vdo.datatypes import VDO_FILE, BLADDR

from fixtures import FIXTURES_DIR


# Словарь ожидаемых значений прямо внутри файла с тестами
EXPECTED_SINGLE_METRIC = {
    "carindb30_0h_9000h.bin": {
        "init": {"dbrev": 30, "segsize": 0x800},  # Передаем как позиционные аргументы по порядку
        "expected_dbrev": 30,
        "expected_segsize": 0x800,
        "bl_type": 0x12,
    },
    "block_0x13_v34_0x200_zlib.bin": {
        "init": {"dbrev": 34, "segsize": 0x200},
        "expected_dbrev": 34,
        "expected_segsize": 0x200,
        "bl_type": 0x13,
    },
    "carindb34_0h_6800h.bin": {
        "init": {},  # Пустой словарь для дефолтных значений
        "expected_dbrev": 34,
        "expected_segsize": 0x800,
        "bl_type": 0x12,
    },
    "DB34_0h_3A01h.bin": {
        "init": {"dbrev": 30, "segsize": 0x800},  # Передаем как позиционные аргументы по порядку
        "expected_dbrev": 30,
        "expected_segsize": 0x800,
        "bl_type": 0x12,
    },
}


@pytest.fixture(
    scope="function",
    params=list(EXPECTED_SINGLE_METRIC),
    ids=list(EXPECTED_SINGLE_METRIC)  # Красивые имена тестов в консоли
)       # scope="function")  scope="session",
def block_0x12_fixture(request):
    filename = request.param
    metric = EXPECTED_SINGLE_METRIC[filename]
    
    # Динамически вычисляем путь
    file_path = FIXTURES_DIR / filename
    
    if not file_path.exists():  # pragma: no cover
        pytest.skip(f"Тестовый файл {filename} не найден по пути {file_path}, пропускаем.")

    # Безопасно инициализируем через синглтон пустого VDO_FILE.
    # Используем **kwargs распаковку словаря init (передаст dbrev=30, segsize=0x800 автоматически)
    init_params = metric.get("init", {})
    block = VDO_FILE().load_single_block(str(file_path), **init_params)
    return block, metric

# ==============================================================================
# НАБОР ТЕСТОВ ДЛЯ ПОЛНОГО ПОКРЫТИЯ (QA EXPERT METHODOLOGY)
# ==============================================================================


def test_empty_load_single_block(block_0x12_fixture):
    """QA-01: Базовая проверка правильности формирования блока и контекста."""
    block, metric = block_0x12_fixture

    # Проверка метаданных через привязанный адрес (так как контекст файла изолирован)
    assert block.dbrev == metric["expected_dbrev"]
    assert block.segsize == metric["expected_segsize"]
    assert block.type == metric["bl_type"]


def test_block_slots_and_memory_optimization(block_0x12_fixture):
    """QA-02: Проверка отсутствия динамического словаря __dict__ (Контракт памяти)."""
    block, _ = block_0x12_fixture
    
    # Защита от утечек памяти: у объектов не должно быть __dict__
    assert not hasattr(block, "__dict__"), f"Обнаружен __dict__ у {type(block).__name__}!"
    
    # Попытка записать свойство вне разрешенных __slots__ должна падать
    with pytest.raises(AttributeError):
        block.accidental_typo_property = "leak"


def test_block_0x12_specific_logic(block_0x12_fixture):
    """QA-03: Тестирование специфичной структуры уникального блока 0x12 (carindb30)."""
    block, metric = block_0x12_fixture
    
    # Выполняем проверки только для файлов, которые распознались как блок 0x12
    if metric["bl_type"] == 0x12:
        # Для ревизии v30 (наш файл carindb30_0h_9000h.bin) гео-зоны и карта обязаны быть None
        if metric["expected_dbrev"] == 30:
            assert block.cd_map is None
            assert block.area_A is None
            assert block.area_B is None
        else:
            assert str(block.area_A)
            
        # Общие свойства, доступные на блоке 0x12
        assert isinstance(block.likely_const_ALLWAYS_12, int)
        assert isinstance(block.likely_MAX_SEGS_UNPACKED, int)
        assert isinstance(block.bladdr_bibliogr, BLADDR)
        assert isinstance(block.bladdr_scales, BLADDR)
        assert isinstance(block.bladdr_ch_country, BLADDR)


def test_block_0x12_fails_on_wrong_type_map_fixture():
    """
    QA-06: Проверяет жесткое падение парсера на бинарном файле
    block_0x12_v34_wrong_type_map.bin с поврежденной картой типов блоков.
    """
    filename = "block_0x12_v34_wrong_type_map.bin"
    
    # 1. Динамически вычисляем путь к файлу фикстуры
    file_path = FIXTURES_DIR / filename
    
    if not file_path.exists():  # pragma: no cover
        pytest.skip(f"Тестовый файл {filename} не найден на диске, пропускаем.")

    # 2. Нативно инициализируем одиночный блок как ревизию 34 и сегмент 0x800
    with pytest.raises(ValueError) as exc_info:
        VDO_FILE().load_single_block(str(file_path), dbrev=34, segsize=0x800)
    assert "неизвестный тип: 0xEE" in str(exc_info.value)
