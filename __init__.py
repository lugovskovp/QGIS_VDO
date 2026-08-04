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

import os
import sys

from QGIS_VDO.ui_files import AnimatedGroupBox   # noqa

# <<< bitarray import
# Get the path to your plugin's 'ext_libs' folder
plugin_dir = os.path.dirname(__file__)
ext_libs_path = os.path.join(plugin_dir, "ext_libs")

# Inject it into the system path if it isn't there already
if ext_libs_path not in sys.path:
    sys.path.insert(0, ext_libs_path)

from bitarray import bitarray           # type: ignore # noqa
from bitarray.util import ba2int        # type: ignore # noqa

# >>> bitarray import


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
