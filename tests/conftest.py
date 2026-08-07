import pytest                       # type: ignore  # noqa
import os


from .fixtures import FIXTURES_DIR
# from QGIS_VDO.tests.fixtures import FIXTURES_DIR

from QGIS_VDO.vdo.datatypes import VDO_FILE      # noqa

from QGIS_VDO.vdo.blocks import block_0x13, block_0x07       # noqa


EXPECTED_VDO_METRICS = {"carindb30_0h_9000h.bin": {
                            "dbrev": 30,
                            "segsize": 2048,
                            "file_size": 36864,
                            "bl_0x12.area_A": 'None',
                            "bl_201": block_0x07,
                            "is_empty": False,
                            "filename": "carindb30_0h_9000h.bin",
                            },
                        "carindb34_0h_6800h.bin": {
                            "dbrev": 34,
                            "segsize": 2048,
                            "file_size": 0x6800,  # 0x6800,
                            "bl_0x12.area_A": '(41.264602N 12.107522E, 59.895467N 29.673977E)',
                            "bl_201": block_0x07,
                            "is_empty": False,
                            "filename": "carindb34_0h_6800h.bin",
                                                   },
                        "DB34_0h_3A01h.bin": {
                            "dbrev": 34,
                            "segsize": 512,
                            "file_size": 0x3A01,  # реальный размер файла в байтах
                            "bl_0x12.area_A": '(35.317110N 9.161804W, 70.479530N 93.151725E)',
                            "bl_201": block_0x13,
                            "is_empty": False,
                            "filename": "DB34_0h_3A01h.bin",
                            },
                        "wrong_vdo_file_name": {
                            "dbrev": 30,
                            "segsize": 2048,
                            "file_size": 0,  # реальный размер файла в байтах
                            "bl_0x12.area_A": None,
                            "bl_201": None,
                            "is_empty": True,
                            "filename": "",
                            }
                        }


# Перечисляем имена файлов, которые реально должны существовать для тестов
VALID_FILES = [
    "carindb30_0h_9000h.bin",
    "carindb34_0h_6800h.bin",
    "DB34_0h_3A01h.bin"
]


@pytest.fixture(
    scope="function",
    params=VALID_FILES,
    ids=VALID_FILES  # Красивые имена тестов в консоли
)       # scope="function")  scope="session",
def real_vdo_fixture(request):
    """
    Автоматически создает экземпляр VDO_FILE для каждого валидного файла
    и возвращает кортеж (объект_vdo, ожидаемые_метрики)
    """
    filename = request.param
    expected = EXPECTED_VDO_METRICS[filename]
    
    # тестовые файлы лежат в папке с тестами
    file_path = FIXTURES_DIR / filename
    
    # Дополнительная проверка на случай, если файла физически нет на диске
    if not os.path.exists(file_path):             # pragma: no cover
        pytest.skip(f"Тестовый файл {filename} не найден на диске, пропускаем.")
        
    vdo = VDO_FILE(file_path)
    return vdo, expected


@pytest.fixture
def empty_vdo_fixture():
    """Фикстура для проверки поведения пустого/невалидного синглтона"""
    vdo = VDO_FILE("wrong_vdo_file_name")
    expected = EXPECTED_VDO_METRICS["wrong_vdo_file_name"]
    return vdo, expected


@pytest.fixture(
    scope="function",
    params=list(EXPECTED_VDO_METRICS),
    ids=list(EXPECTED_VDO_METRICS)  # Красивые имена тестов в консоли
)       # scope="function")  scope="session",
def all_vdo_fixture(request):
    """
    Автоматически создает экземпляр VDO_FILE для каждого файла
    и возвращает кортеж (объект_vdo, ожидаемые_метрики)
    """
    filename = request.param
    expected = EXPECTED_VDO_METRICS[filename]
    
    # тестовые файлы лежат в папке с тестами
    file_path = FIXTURES_DIR / filename
            
    vdo = VDO_FILE(file_path)
    return vdo, expected
