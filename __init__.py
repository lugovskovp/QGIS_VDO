#-----------------------------------------------------------
# Copyright (C) 2026 Paul Lugovskov
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------

# flake8: noqa: QGS105      # игнор передачи iface по значению, а не импорт его
import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox


def classFactory(iface):
    return MinimalPlugin(iface)


class MinimalPlugin:
    def __init__(self, iface):  # type: ignore
        self.iface = iface

    def initGui(self):
        icon = QIcon(os.path.join(os.path.dirname(__file__), "resources/plugin.icons/qgis-vdo_i.svg"))
        self.action = QAction(icon, 'Go!', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        del self.action

    def run(self):
        QMessageBox.information(None, 'Minimal plugin', 'Do something useful here')
        self.iface


'''from enum import Enum
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
