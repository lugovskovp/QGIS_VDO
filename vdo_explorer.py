''' VDOExplorerPlugin class
A QGIS plugin
Systeme Guidage Carminat C-IQ navigation database viewer

        begin                : 2023-01-08
        copyright            : (C) 2023 by Sweet Home
        email                : p.lugovskov@gmail.com
        git sha              : https://github.com/lugovskovp/QGIS_VDO

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.'''

import os
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox

#from QGIS_VDO.vdo_setup import ICON_PATH_PLUGIN

ICON_PATH_PLUGIN = "resources/plugin.icons/qgis-vdo_i.svg"


class VDOExplorerPlugin:
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        icon = QIcon(os.path.join(os.path.dirname(__file__), ICON_PATH_PLUGIN))
        self.action = QAction(icon, 'Go!', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        del self.action

    def run(self):
        QMessageBox.information(None, 'Minimal plugin', 'Do something useful here')
        self.iface


'''
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QAbstractItemModel, QModelIndex, Qt
from qgis.PyQt.QtGui import (
    QBrush,
    QFont,
    QGuiApplication,
    QIcon,
    QMovie,
    QPalette,
)

from osminfo.openstreetmap.models import OsmElement, OsmResultTree, OsmTag
from osminfo.openstreetmap.tag2link import TagLink
from osminfo.ui.icon import qgis_icon'''
