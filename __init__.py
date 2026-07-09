''' Carindb VDO
A QGIS plugin
Systeme Guidage Carminat C-IQ navigation database viewer

        begin                : 2026-05-12
        copyright            : (C) 2026 by Sweet Home
        email                : p.lugovskov@gmail.com
        git sha              : https://github.com/lugovskovp/QGIS_VDO

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.'''

import os
import sys

from QGIS_VDO.CollapsibleGroupBox import AnimatedGroupBox    # noqa

# Get the path to your plugin's 'ext_libs' folder
plugin_dir = os.path.dirname(__file__)
ext_libs_path = os.path.join(plugin_dir, "ext_libs")

# Inject it into the system path if it isn't there already
if ext_libs_path not in sys.path:
    sys.path.insert(0, ext_libs_path)


def classFactory(iface):
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
