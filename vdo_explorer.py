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

import os.path
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QObject
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import Qgis, QgsMessageLog
from qgis.gui import QgisInterface

#from QGIS_VDO.vdo_setup import ICON_PATH_PLUGIN

ICON_PATH_PLUGIN = "resources/plugin.icons/qgis-vdo_i.svg"


class VDOExplorerPlugin:
    """The plugin class."""

    def __init__(self, iface: QgisInterface):
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'VDOExplorerPlugin_{}.qm'.format(locale))
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        '''self.iface.messageBar().pushMessage(
            self.tr('Plugin <b>{}</b> not found.').format(plugin),
            Qgis.Warning, 1)'''

    def tr(self, message: str) -> str:
        """Translate a string."""
        return QCoreApplication.translate('Plugin', message)

    def initGui(self):
        icon = QIcon(os.path.join(os.path.dirname(__file__), ICON_PATH_PLUGIN))
        self.action = QAction(icon, 'Go!', self.iface.mainWindow())
        self.action.triggered.connect(self.hide_show)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        del self.action

    def hide_show(self):
        QMessageBox.information(None, 'Minimal plugin', 'Do something useful here')
        msg = self.tr('<b>{}</b> asdasd reloaded in {} ms.').format("plugin", 67)

        self.iface.messageBar().pushMessage(msg, Qgis.Success)
        # Actual name of the "Plugins" tab in the message log panel
        # is localized, so we need to find it in QGIS' translations.
        # Don't pass the string value directly to QObject().tr()
        # to prevent local pylupdate from catching it.
        pluginsLogTabSourceName = "Plugins"
        pluginsLogTabName = QObject().tr(pluginsLogTabSourceName)
        QgsMessageLog.logMessage(msg, pluginsLogTabName, level=Qgis.Info)
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
