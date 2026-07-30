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
if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):

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
    except ImportError:
        # Инструкция на случай, если локальный pytest запущен вне окружения QGIS
        raise ImportError(
            "Не удалось импортировать QGIS локально. "
            "Запустите pytest через Python-окружение QGIS или OSGeo4W Shell."
        )
    
import pytest                       # type: ignore  # noqa
from QGIS_VDO.vdo.datatypes import VDO_FILE      # noqa
# Явно импортируем фикстуру, чтобы pytest её увидел
from fixtures import bin_file_path      # noqa


@pytest.fixture(scope="function")
def custom_vdo():
    vdo = VDO_FILE()
    vdo.segsize = 2048
    vdo.dbrev = 34
    vdo.path = "C:/Work/fake_test_file.vdo"
    return vdo


@pytest.fixture(scope="function")
def real_vdo(bin_file_path):                # noqa
    vdo = VDO_FILE(bin_file_path)
    return vdo
