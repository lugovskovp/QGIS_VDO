''' Carindb VDO
A QGIS plugin VDOExplorerPlugin class
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
from qgis.PyQt.QtWidgets import QAction, QMenu, QToolButton, QMessageBox
from qgis.core import Qgis, QgsMessageLog
from qgis.gui import QgisInterface

from .settings import Settings

ICON_PATH_PLUGIN = "resources/plugin.icons/qgis-vdo_i.svg"
ICON_PATH_PLUGIN_CONFIG = "resources/plugin.icons/settings.svg"


class VDOExplorerPlugin:
    """The plugin class."""
    
    def __init__(self, iface: QgisInterface):
        self.iface = iface

        self.menu = None

        #
        #self.dockwidget = None

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

        # push варнинг - плагин стартовал
        # self.iface.messageBar().pushMessage(
        #     self.tr('Plugin <b>VDOExplorerPlugin</b> initialised.'), Qgis.Warning, 1)

    def tr(self, message: str) -> str:
        """Translate a string."""
        return QCoreApplication.translate('VDOExplorerPlugin', message)

    def initGui(self):
        """Add actions to the QGIS menu and toolbar."""
        icon = QIcon(os.path.join(os.path.dirname(__file__), ICON_PATH_PLUGIN))
        iconConf = QIcon(os.path.join(os.path.dirname(__file__),
                         ICON_PATH_PLUGIN_CONFIG))
        # В строку меню Модули добавить меню плагина
        self.menu = self.iface.pluginMenu().addMenu(icon, self.tr(
            "&Carindb VDO"))

        # Действие по-умолчанию - открыть файл
        self.actionLoadRecentCarindb = QAction(
            icon, self.tr("Load recent Carindb"))
        self.actionLoadRecentCarindb.setObjectName(
            "PluginReloader_ReloadRecentPlugin")
        self.actionLoadRecentCarindb.triggered.connect(self.loadDefaultCarindb)

        # Кнопка на панели
        self.toolButton = QToolButton()
        self.toolButton.setMenu(QMenu())
        self.toolButton.setToolButtonStyle(Settings.toolButtonStyle())
        self.toolButton.setPopupMode(
            QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        toolButtonMenu = self.toolButton.menu()

        # Add the actionLoadRecentCarindb to menu (to present its shortcut)
        # and set it to the tool buttton as the default action
        self.toolButton.setDefaultAction(self.actionLoadRecentCarindb)
        self.menu.addAction(self.actionLoadRecentCarindb)
        self.menu.addSeparator()
        #
        toolButtonMenu.addAction(self.actionLoadRecentCarindb)
        toolButtonMenu.addSeparator()

        # Create action for opening the settings window
        self.actionSettings = QAction(iconConf, self.tr("Configure"))
        self.actionSettings.triggered.connect(self.openConfigWindow)
        # add Setting action into menu and button
        toolButtonMenu.addAction(self.actionSettings)
        self.menu.addAction(self.actionSettings)

        self.iface.addToolBarWidget(self.toolButton)

        #self.iface.initializationCompleted.connect(self.updatePluginIcons)

    def unload(self):
        """Remove the plugin's actions from the QGIS menu and toolbars."""
        # self.iface.removeToolBarIcon(self.action)
        # del self.action
        if not self.menu:
            # The initGui() method was never called
            return
        self.iface.pluginMenu().removeAction(self.menu.menuAction())
        self.toolButton.deleteLater()
        pass

    def run(self):
        # if self.dockwidget == None:
        #     # Create the dockwidget (after translation) and keep reference
        #     self.dockwidget = Ui_VDODockWidget()
        #     pass
        self.iface

    def openConfigWindow(self):
        """Open the configuration dialog."""
        QMessageBox.information(None, self.tr('config windows'),
                                self.tr('configuration'))

    def loadDefaultCarindb(self):
        """Loading default"""
        QMessageBox.information(None, self.tr('load windows'),
                                self.tr('load Default Carindb'))

    def hide_show(self):
        QMessageBox.information(None, self.tr('Minimal plugin'),
                                self.tr('Do something useful here'))
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
