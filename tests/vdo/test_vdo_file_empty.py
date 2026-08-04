import pytest   # type: ignore # noqa
import os
from pathlib import Path

from unittest.mock import patch

from QGIS_VDO.vdo.datatypes import BLADDR, VDO_FILE
# from QGIS_VDO.vdo.blocks import block_0x12


@pytest.mark.parametrize("any_addr", [
    None,
    0,
    0x10,
    "strings not good choice here",
    BLADDR(b'\x00\x00\x02\x01')
])
def test_get_block_always_returns_none_when_vdo_is_empty(empty_vdo_fixture, any_addr):
    """Если VDO пустой/невалидный, get_block всегда возвращает None для любых аргументов"""
    empty_vdo, expected = empty_vdo_fixture

    assert empty_vdo.is_empty is expected["is_empty"]
    assert empty_vdo.get_block(any_addr) is None
    # QGISvdoGroupName
    assert empty_vdo.QGISvdoGroupName is None


EXPECTED_SINGLE_METRIC = {
    "block_0x13_v30.bin": {
        "init": [30, 0x800],  # Передаем как позиционные аргументы по порядку
        "expected_dbrev": 30,
        "expected_segsize": 0x800,
        "bl_type": 0x13,
    },
    "block_0x13_v34_0x200.bin": {
        "init": [34, 0x200],
        "expected_dbrev": 34,
        "expected_segsize": 0x200,
        "bl_type": 0x13,
    },
    "block_0xee_v30.bin": {
        "init": [],  # Пустой список для дефолтных значений
        "expected_dbrev": 34,
        "expected_segsize": 0x800,
        "bl_type": 0xFF,
    },
}


@pytest.fixture(
    scope="function",
    params=list(EXPECTED_SINGLE_METRIC),
    ids=list(EXPECTED_SINGLE_METRIC)
)
def single_block_fixture(request):
    filename = request.param
    metric = EXPECTED_SINGLE_METRIC[filename]
    
    # Динамически вычисляем путь относительно файла с тестами
    test_dir = Path(request.fspath).parent.parent
    file_path = test_dir / "fixtures" / filename
    
    if not file_path.exists():  # pragma: no cover
        pytest.skip(f"Тестовый файл {filename} не найден по пути {file_path}, пропускаем.")

    # Безопасно инициализируем через синглтон пустого VDO_FILE.
    # Используем **kwargs распаковку словаря init (передаст dbrev=30, segsize=0x800 автоматически)
    init_params = metric.get("init", [])
    block = VDO_FILE().load_single_block(str(file_path), *init_params)
    
    return block, metric


def test_empty_load_single_block(single_block_fixture):
    """Проверка правильности формирования vdo при загрузке"""
    block, metric = single_block_fixture

    assert block.vdo.is_single
    assert block.vdo.dbrev == metric["expected_dbrev"]
    assert block.vdo.segsize == metric["expected_segsize"]
    assert block.type == metric["bl_type"]


def test_empty_load_single_after_load_single(single_block_fixture):
    """Попытка загрузить еще блок после single load"""
    block, metric = single_block_fixture

    with pytest.raises(RuntimeError):
        block.vdo.load_single_block("empty_path")


def test_empty__single_create_vdo_after_load_single(single_block_fixture):
    """Попытка загрузить еще блок после single load"""
    block, metric = single_block_fixture

    with pytest.raises(RuntimeError):
        block.vdo._single_create_vdo("до проверки пути там не дойдёт")


def test_empty_load_single_wrong_path():
    """загрузка заведомо отсутствующего файла"""
    with pytest.raises(FileNotFoundError):
        VDO_FILE().load_single_block("this_is_wrong_path")


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


def test_empty_vdo_slots_integrity(empty_vdo_fixture):
    """Проверяет работу __slots__ на пустом VDO / синглтоне"""
    empty_vdo, _ = empty_vdo_fixture
    
    assert not hasattr(empty_vdo, "__dict__")
    
    with pytest.raises(AttributeError):
        empty_vdo.new_arbitrary_property = 42


def test_vdo_file_init_too_small_file():
    """Проверка создания пустого синглтона на слишком маленьком файле"""
    filename = 'too_small_carindb.bin'
    # тестовые файлы лежат в папке с тестами
    file_path = f"tests/fixtures/{filename}"
    
    # Дополнительная проверка на случай, если файла физически нет на диске
    if not os.path.exists(file_path):             # pragma: no cover
        pytest.skip(f"Тестовый файл {filename} не найден на диске, пропускаем.")

    empty_vdo = VDO_FILE()
    test_vdo = VDO_FILE(file_path)

    assert empty_vdo is test_vdo


def test_vdo_file_init_first_bl_not_0x12():
    """Проверка создания vdo, если первые 4 байта не 00 00 00 01"""
    filename = 'block_0x13_v30.bin'
    # тестовые файлы лежат в папке с тестами
    file_path = f"tests/fixtures/{filename}"
    
    # Дополнительная проверка на случай, если файла физически нет на диске
    if not os.path.exists(file_path):             # pragma: no cover
        pytest.skip(f"Тестовый файл {filename} не найден на диске, пропускаем.")

    empty_vdo = VDO_FILE()
    test_vdo = VDO_FILE(file_path)

    assert empty_vdo is test_vdo
