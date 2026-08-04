import pytest   # type: ignore # noqa

# from pathlib import Path

# from QGIS_VDO.vdo.blocks import block_0x12
from QGIS_VDO.vdo.datatypes import VDO_FILE

from fixtures import FIXTURES_DIR


def test_block_0x12_fails_on_wrong_type_map_fixture(request):
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
