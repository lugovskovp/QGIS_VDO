'''
Copyright (C) 2026 Lugovskov Pavel

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://gnu.org>.


Carindb VDO
A QGIS plugin
Systeme Guidage Carminat C-IQ navigation database viewer

        begin                : 2026-05-12
        copyright            : (C) 2026 by Sweet Home
        email                : p.lugovskov@gmail.com
        git sha              : https://github.com/lugovskovp/QGIS_VDO

try:
    import bitarray
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "bitarray"])

'''

import sys
import subprocess
import logging

logger = logging.getLogger("MyQgisPlugin")

# <<< bitarray import
try:
    from bitarray import bitarray                         # type: ignore # noqa
    from bitarray.util import ba2int                      # type: ignore # noqa
except ImportError:
    logger.info("Библиотека bitarray не найдена. Попытка безопасной установки...")
    try:
        # Формируем аргументы для pip
        # Использование --user изолирует пакет в домашней директории пользователя,
        # что решает проблему прав администратора в Windows/OSGeo4W и Linux
        pip_args = [sys.executable, "-m", "pip", "install", "--user", "bitarray"]
        
        # Добавляем флаг совместимости с PEP 668 только если Python >= 3.11
        if sys.version_info >= (3, 11):
            pip_args.append("--break-system-packages")

        # Запускаем установку скрыто (без всплывающих окон консоли на Windows)
        # и с таймаутом, чтобы QGIS не завис навсегда, если пропал интернет
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        process = subprocess.Popen(
            pip_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            text=True
        )
        
        # Ждем максимум 45 секунд (bitarray компилируется/скачивается быстро)
        stdout, stderr = process.communicate(timeout=45)

        if process.returncode != 0:
            raise RuntimeError(f"Pip вернул код {process.returncode}. Ошибка: {stderr}")

        # Принудительно обновляем пути поиска модулей, так как папка --user могла создаться только что
        import importlib
        importlib.invalidate_caches()
        
        # Повторная попытка импорта
        from bitarray import bitarray                     # type: ignore # noqa
        from bitarray.util import ba2int                  # type: ignore # noqa
        logger.info("Библиотека bitarray успешно установлена в пользовательское окружение!")
        
    except Exception as e:
        logger.error(f"Не удалось автоматически установить bitarray: {e}")
        # Если импорт не удался, мы не падаем здесь, а даем QGIS загрузить плагин,
        # но внутри classFactory или инициализации самого плагина вызовем красивый QMessageBox.
# >>> bitarray import


# Импорты UI делаем строго ПОСЛЕ блока установки зависимостей
try:
    from QGIS_VDO.ui_files import AnimatedGroupBox       # noqa
except ImportError as e:
    logger.error(f"Ошибка импорта UI компонентов плагина: {e}")


def classFactory(iface):
    """Load VDOExplorerPlugin class from file VDOExplorer.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    # Защита на случай, если bitarray так и не удалось поставить
    try:
        from bitarray import bitarray                   # type: ignore # noqa
    except ImportError:
        from qgis.pyqt.QtWidgets import QMessageBox     # type: ignore # noqa
        QMessageBox.critical(
            iface.mainWindow(),
            "Ошибка запуска QGIS_VDO",
            "Для работы плагина необходима библиотека 'bitarray'.\n\n"
            "Пожалуйста, установите её вручную через консоль:\n"
            "pip install bitarray"
        )
        return None

    from QGIS_VDO.vdo_explorer import VDOExplorerPlugin
    return VDOExplorerPlugin(iface)


if __name__ == "__main__":
    """Standalone execution."""
    pass    # type: ignore # noqa
