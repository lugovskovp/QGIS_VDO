import os
import sys
# from unittest.mock import MagicMock

# 1. Жесткая настройка путей для всех уровней вложенности
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXT_LIBS_DIR = os.path.join(BASE_DIR, "ext_libs")

for path in [BASE_DIR, EXT_LIBS_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

# 2. Изоляция QGIS (Продвинутые заглушки для пакетов)
if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):          # pragma: no cover

    # Фикс для глубоких подпапок: если Python не может найти QGIS_VDO как пакет,
    # мы помогаем ему, импортируя его принудительно прямо из conftest
    try:
        import QGIS_VDO     # noqa
    except ModuleNotFoundError:
        # Если импорт не прошел стандартно, добавляем родительскую папку родительской папки
        PARENT_OF_BASE = os.path.dirname(BASE_DIR)
        if PARENT_OF_BASE not in sys.path:
            sys.path.insert(0, PARENT_OF_BASE)

    # class MockPackage(MagicMock):
    #     __path__ = []

    # qgis_mock = MockPackage()
    # pyqt5_mock = MockPackage()

    # sys.modules['qgis'] = qgis_mock
    # sys.modules['qgis.PyQt'] = qgis_mock.PyQt
    # sys.modules['qgis.PyQt.QtCore'] = qgis_mock.PyQt.QtCore
    # sys.modules['qgis.PyQt.QtWidgets'] = qgis_mock.PyQt.QtWidgets
    # sys.modules['qgis.PyQt.QtGui'] = qgis_mock.PyQt.QtGui
    # sys.modules['qgis.core'] = qgis_mock.core
    # sys.modules['qgis.gui'] = qgis_mock.gui
    # sys.modules['qgis.utils'] = qgis_mock.utils
    
    # sys.modules['PyQt5'] = pyqt5_mock
    # sys.modules['PyQt5.QtCore'] = pyqt5_mock.QtCore
    # sys.modules['PyQt5.QtWidgets'] = pyqt5_mock.QtWidgets
    # sys.modules['PyQt5.QtGui'] = pyqt5_mock.QtGui


else:
    # Этот блок выполнится НА ЛОКАЛЬНОМ КОМПЬЮТЕРЕ
    # Если вы запускаете тесты из IDE (PyCharm/VS Code), убедитесь,
    # что в её настройках Python Interpreter указан Python из папки QGIS.
    try:
        import qgis.core   # noqa
    except ImportError:           # pragma: no cover
        # Инструкция на случай, если локальный pytest запущен вне окружения QGIS
        raise ImportError(
            "Не удалось импортировать QGIS локально. "
            "Запустите pytest через Python-окружение QGIS или OSGeo4W Shell."
        )
    
import pytest                       # type: ignore  # noqa
from QGIS_VDO.vdo.datatypes import VDO_FILE      # noqa

# Явно импортируем фикстуру, чтобы pytest её увидел
from fixtures import bin_file_path      # noqa
from QGIS_VDO.vdo.blocks import block_0x13, block_0x07       # noqa


# Словарь ожидаемых значений прямо внутри файла с тестами
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
                            "bl_0x12.area_A": '(41.264594N 12.107514E, 59.895456N 29.673966E)',
                            "bl_201": block_0x07,
                            "is_empty": False,
                            "filename": "carindb34_0h_6800h.bin",
                                                   },
                        "DB34_0h_3A01h.bin": {
                            "dbrev": 34,
                            "segsize": 512,
                            "file_size": 0x3A01,  # реальный размер файла в байтах
                            "bl_0x12.area_A": '(35.317104N 9.161808W, 70.479517N 93.151702E)',
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
    file_path = f"tests/fixtures/{filename}"
    
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
    file_path = f"tests/fixtures/{filename}"
            
    vdo = VDO_FILE(file_path)
    return vdo, expected
