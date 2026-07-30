import os
import sys

# 1. Настройка путей (работает везде: и локально, и на GitHub)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXT_LIBS_DIR = os.path.join(BASE_DIR, "ext_libs")

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if EXT_LIBS_DIR not in sys.path:
    sys.path.insert(0, EXT_LIBS_DIR)

# 2. Умный импорт QGIS: настоящая библиотека локально ИЛИ заглушка на GitHub
if os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI") == "true":
    # Этот блок выполнится ТОЛЬКО на GitHub Actions
    from unittest.mock import MagicMock

    class MockModule(MagicMock):
        @classmethod
        def __getattr__(cls, name):
            return MagicMock()

    # Изолируем окружение GitHub от отсутствующих библиотек
    if os.environ.get("CI"):
        for module in ['qgis', 'qgis.core', 'qgis.gui', 'qgis.utils', 'PyQt5']:
            sys.modules[module] = MagicMock()
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
    
    import pytest   # type: ignore
    from QGIS_VDO.vdo.datatypes import VDO_FILE

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
