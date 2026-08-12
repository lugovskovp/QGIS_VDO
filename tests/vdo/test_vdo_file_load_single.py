import pytest   # type: ignore # noqa

# from pathlib import Path
from unittest.mock import patch

from QGIS_VDO.vdo.datatypes import VDO_FILE
from QGIS_VDO.vdo.geotypes import COORD

from QGIS_VDO.tests.fixtures import FIXTURES_DIR


EXPECTED_SINGLE_METRIC = {
    "block_0x13_v30.bin": {
        "init": {"dbrev": 30, "segsize": 0x800},  # Передаем как позиционные аргументы по порядку
        "expected_dbrev": 30,
        "expected_segsize": 0x800,
        "bl_type": 0x13,
    },
    "block_0x13_v34_0x200_zlib.bin": {
        "init": {"dbrev": 34, "segsize": 0x200},
        "expected_dbrev": 34,
        "expected_segsize": 0x200,
        "bl_type": 0x13,
    },
    "block_0xee_v30.bin": {
        "init": {},  # Пустой словарь для дефолтных значений
        "expected_dbrev": 34,
        "expected_segsize": 0x800,
        "bl_type": 0xFF,
    },
    "carindb30_0h_9000h.bin": {
        "init": {"dbrev": 30, "segsize": 0x800},  # Передаем как позиционные аргументы по порядку
        "expected_dbrev": 30,
        "expected_segsize": 0x800,
        "bl_type": 0x12,
    },
}


@pytest.fixture(
    scope="function",
    params=list(EXPECTED_SINGLE_METRIC),
    ids=list(EXPECTED_SINGLE_METRIC)
)
def block_single_fixture(request):
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

# ==================================================================


def test_empty_load_single_block(block_single_fixture):
    """Проверка правильности формирования vdo при загрузке"""
    block, metric = block_single_fixture

    assert block.vdo.is_single
    assert block.vdo.dbrev == metric["expected_dbrev"]
    assert block.vdo.segsize == metric["expected_segsize"]
    assert block.type == metric["bl_type"]
    assert block.offset_next() is None          # вообще строго верно это для когда только один блок


def test_empty_load_single_after_load_single(block_single_fixture):
    """Попытка загрузить еще блок после single load"""
    block, metric = block_single_fixture

    with pytest.raises(RuntimeError):
        block.vdo.load_single_block("empty_path")


def test_empty__single_create_vdo_after_load_single(block_single_fixture):
    """Попытка загрузить еще блок после single load"""
    block, metric = block_single_fixture

    with pytest.raises(RuntimeError):
        block.vdo._single_create_vdo("до проверки пути там не дойдёт")


def test_empty_load_single_wrong_path():
    """загрузка заведомо отсутствующего файла"""
    with pytest.raises(FileNotFoundError):
        VDO_FILE().load_single_block("this_is_wrong_path")


def test_empty_load_single_wrong_only_one_coord():
    """загрузка тольео одной координаты"""
    path = FIXTURES_DIR / '0x08_ru34_sc11_09567101.bin'

    with pytest.raises(RuntimeError, match='должны быть ОБА класса COORD'):
        VDO_FILE().load_single_block(path, 34, 2048, COORD(bytes.fromhex('13F919BE13DA074C')))


def test_load_single_block_os_error_handling():
    """
    Проверяет, что при возникновении OSError внутри _single_create_vdo
    метод корректно перехватывает ошибку и выбрасывает RuntimeError.
    """
    # 1. Берем заведомо существующий файл (можно пустой синглтон или сам файл теста)
    dummy_file = __file__
    
    # Инициализируем пустой синглтон, от которого будем вызывать метод
    empty_vdo = VDO_FILE()
    
    # 2. Перехватываем os.path.getsize с помощью утилиты patch.
    # side_effect указывает, что при вызове функции должно возникнуть исключение OSError
    with patch("os.path.getsize", side_effect=OSError("Permission denied / File locked")):
        
        # 3. Проверяем, что метод load_single_block (или напрямую _single_create_vdo)
        # выбрасывает именно RuntimeError, как заложено в ветке except
        with pytest.raises(RuntimeError) as exc_info:
            empty_vdo.load_single_block(dummy_file)
            
        # 4. Проверяем текст сообщения об ошибке, чтобы убедиться, что сработал именно наш catch
        assert "Ошибка при инициализации файла одиночного блока" in str(exc_info.value)
        assert "Permission denied" in str(exc_info.value)
