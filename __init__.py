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
    from bitarray.util import ba2int        # type: ignore # noqa
except ImportError:
    logger.info("Библиотека bitarray не найдена. Попытка автоматической установки...")
    try:
        # sys.executable гарантирует, что мы используем именно тот Python,
        # в котором сейчас запущен QGIS (включая ваш Docker-контейнер)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "bitarray"])
        from bitarray import bitarray                     # type: ignore # noqa
        from bitarray.util import ba2int    # type: ignore # noqa
        logger.info("Библиотека bitarray успешно установлена!")
    except Exception as e:
        logger.error(f"Не удалось автоматически установить bitarray: {e}")
        # Здесь можно вызвать QMessageBox, чтобы предупредить пользователя,
        # если плагин запускается в графическом интерфейсе QGIS
# >>> bitarray import
# type: ignore # noqa


from QGIS_VDO.ui_files import AnimatedGroupBox   # noqa


def classFactory(iface):                # pragma: no cover
    # Весь этот блок теперь официально игнорируется тестами
    """Load VDOExplorerPlugin class from file VDOExplorer.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #return MinimalPlugin(iface)
    from QGIS_VDO.vdo_explorer import VDOExplorerPlugin
    return VDOExplorerPlugin(iface)


if __name__ == "__main__":
    """Standalone execution."""
    pass
