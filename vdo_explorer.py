''' Carindb VDO
A QGIS plugin VDOExplorerPlugin class
Systeme Guidage Carminat C-IQ navigation database viewer

        begin                : 2023-01-08
        copyright            : (C) 2026 by Sweet Home
        email                : p.lugovskov@gmail.com
        git sha              : https://github.com/lugovskovp/QGIS_VDO

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.'''

import os.path
from functools import partial
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication   # , QObject
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu, QToolButton, QMessageBox, QFileDialog
#from qgis.core import Qgis, QgsMessageLog
from qgis.gui import QgisInterface

from .settings import Settings
from .ConfigurationDialog import ConfigurationDialog


ICON_PATH_PLUGIN = "resources/plugin.icons/qgis-vdo_i.svg"
ICON_PATH_PLUGIN_CONFIG = "resources/plugin.icons/gears_i.svg"
ICON_PATH_PLUGIN_OPEN = "resources/plugin.icons/folder_i.svg"
ICON_PATH_PLUGIN_ALERT = "resources/plugin.icons/icon_alert.svg"
ACTION_LOAD_NEW_CARINDB = "CarindbVDO_chooseNewCarindb"
ACTION_CLEAR_RECENT_CARINDB = "CarindbVDO_clearRecentList"


class VDOExplorerPlugin:
    """The plugin class."""

    actionForPlugin: dict[str, QAction] = {}
    """ Список последних открытых carindb """

    icon = QIcon(os.path.join(os.path.dirname(__file__), ICON_PATH_PLUGIN))
    """ Иконка плагина """

    iconAlert = QIcon(os.path.join(os.path.dirname(__file__),
                                   ICON_PATH_PLUGIN_ALERT))
    """ Иконка - предупреждение """

    iconOpen = QIcon(os.path.join(os.path.dirname(__file__),
                                  ICON_PATH_PLUGIN_OPEN))
    """ Иконка открытия файла """

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
        iconConf = QIcon(os.path.join(os.path.dirname(__file__),
                         ICON_PATH_PLUGIN_CONFIG))
        # В меню Модули добавить меню плагина
        self.menu = self.iface.pluginMenu().addMenu(self.icon, self.tr("&Carindb VDO"))
        # Кнопка на панели
        self.toolButton = QToolButton()
        self.toolButton.setToolButtonStyle(Settings.toolButtonStyle())
        self.toolButton.setPopupMode(
            QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        # Действие  открыть новый файл
        self.actionChooseNewCarindb = QAction(
            self.iconOpen, self.tr("Load Carindb ..."))
        self.actionChooseNewCarindb.setObjectName(ACTION_LOAD_NEW_CARINDB)
        self.actionChooseNewCarindb.triggered.connect(self.chooseNewCarindb)
        # Действие - очистить весь список последних файлов
        self.actionClearRecent = QAction(self.iconAlert,
                                         self.tr("Clear ALL RECENT FILES list"))
        self.actionClearRecent.setObjectName(ACTION_CLEAR_RECENT_CARINDB)
        self.actionClearRecent.triggered.connect(self.clearRecentList)
        # Действие  Настройки Create action for opening the settings window
        self.actionSettings = QAction(iconConf, self.tr("Configure"))
        self.actionSettings.triggered.connect(self.openConfigWindow)
        self.RegenerateMenu()
        self.iface.addToolBarWidget(self.toolButton)

    def unload(self):
        """Remove the plugin's actions from the QGIS menu and toolbars."""
        # self.iface.removeToolBarIcon(self.action)
        # del self.action
        if not self.menu:
            # The initGui() method was never called
            return
        self.iface.pluginMenu().removeAction(self.menu.menuAction())
        self.toolButton.deleteLater()
    
    def RegenerateMenu(self) -> None:
        " (re?)create menu and button menu "
        #--- clear menu values if needed
        self.toolButton.setMenu(QMenu())
        toolButtonMenu = self.toolButton.menu()
        self.iface.pluginMenu().removeAction(self.menu.menuAction())
        # В меню Модули добавить меню плагина
        self.menu = self.iface.pluginMenu().addMenu(self.icon, self.tr("&Carindb VDO"))
        #--- create actions
        # Create files for recently processed Действия из ранее открывавшихся файлов
        self.actionForPlugin = {}
        for f in Settings.RecentFiles():
            self.actionForPlugin[f] = self.createActionForPlugin(f)
        # и добавить открыть новый файл
        self.actionForPlugin[ACTION_LOAD_NEW_CARINDB] = self.actionChooseNewCarindb
        # Add all the rest of the actions to the menu and the toolbar
        defAction = self.actionChooseNewCarindb
        for action in self.actionForPlugin.values():
            if defAction == self.actionChooseNewCarindb and action.icon().isNull():
                # если дефолтное значение, но иконка текущего - null
                defAction = action
            toolButtonMenu.addAction(action)
            self.menu.addAction(action)
        # установить defauil action
        self.toolButton.setDefaultAction(defAction)
        self.toolButton.setIcon(self.icon)
        # Добавляем визуальные разделители
        toolButtonMenu.addSeparator()
        self.menu.addSeparator()
        # add Setting action into menu and button
        toolButtonMenu.addAction(self.actionSettings)
        self.menu.addAction(self.actionSettings)
        if Settings.ShowClearRecentFilesEnabled:
            self.menu.addAction(self.actionClearRecent)
        self.iface

    def run(self):
        # if self.dockwidget == None:
        #     # Create the dockwidget (after translation) and keep reference
        #     self.dockwidget = Ui_VDODockWidget()
        #     pass
        self.iface

    def openConfigWindow(self):
        """Open the configuration dialog."""
        dlg = ConfigurationDialog(self.iface.mainWindow())
        dlg.exec()
        if dlg.result():
            # обновить вид кнопки - с надписью или без
            if self.toolButton.toolButtonStyle() != Settings.toolButtonStyle():
                self.toolButton.setToolButtonStyle(Settings.toolButtonStyle())
            self.RegenerateMenu()
        
    def chooseNewCarindb(self):
        """ File open dialog and call load file func, if success"""
        vdof_dlg = QFileDialog()
        # Ожидаемый результат - один файл
        vdof_dlg.setFileMode(QFileDialog.ExistingFile)
        fp = Settings.LastFileNamePath()    # fp = 'C:/VDO/db_src/1. BNL_13_14/carindb'
        fileNamePath, _ = vdof_dlg.getOpenFileName(None,
                                                   self.tr("Load carindb file"), fp, "")
        if fileNamePath:
            # adding LastFileNamePath into settings
            Settings.setLastFileNamePath(fileNamePath)
            # try to load carindb file
            if self.loadCarindb(fileNamePath):
                # if sucess, add into actionsForPlugin
                pass
            pass

    def loadCarindb(self, path: os.path) -> bool:
        """ Load carindb file

        :param path: A path for loading carindb file.
        :type path: os.path
        """
        Settings.updateRecentFiles(path)
        self.RegenerateMenu()

        if os.path.exists(path):
            return True
        # self.iface.messageBar().pushMessage(
        # self.tr('Plugin <b>{}</b> not found.').format(plugin),
        # Qgis.Warning, 1)
        return False

    def isCarinb(self, filePath: os.path) -> bool:
        """ А carindb ли файл?

        :param path: A path for checking carindb file.
        :type path: os.path
        """
        #
        actionDir, actionName = os.path.split(filePath)
        res = actionName == 'carindb'
        #
        return res

    def createActionForPlugin(self, filePath: os.path) -> QAction:
        """ Create action from path

        :param path: A path to carindb file for creating QAction.
        :type path: os.path
        """
        # генерим имя
        ap = filePath.split("/")
        actionName = ap[-2] + ":::" + ap[-1]
        # а есть ли файл?
        run = partial(self.alertCarindb, filePath)
        if not os.path.isfile(filePath):
            action = QAction(self.iconAlert,
                             self.tr('Not found: {}').format(actionName))
        # а carindb ли это?
        elif not self.isCarinb(filePath):
            action = QAction(self.iconAlert,
                             self.tr('Not carindb: {}').format(actionName))
        else:
            action = QAction(actionName)
            run = partial(self.loadCarindb, filePath)   # в разных ветках разные экшен
        #
        action.setToolTip(filePath)     # where its showing?
        action.setStatusTip(filePath)   # show in status string
        action.triggered.connect(run)
        return action

    def alertCarindb(self, filePath: os.path) -> None:
        """ action Delete problem path and|or rebuild menu

        :param path: A path for ploblem carindb file.
        :type path: os.path
        """
        #if file carindb not found
        if not os.path.isfile(filePath):
            msg = self.tr('Can`t find file.\nDo you want\
 to remove path from recent?\n{}').format(filePath)
            res = QMessageBox.question(None,
                                       self.tr('Delete from recent files'),
                                       msg,
                                       QMessageBox.Yes | QMessageBox.Cancel,
                                       QMessageBox.Cancel)
            if res == QMessageBox.Cancel:
                return
            else:
                Settings.removeRecentFiles(filePath)
                self.RegenerateMenu()
                msg = self.tr('Do you want to load another carindb?')
                res = QMessageBox.question(None,
                                           self.tr('Open another carindb'),
                                           msg,
                                           QMessageBox.Yes | QMessageBox.Cancel,
                                           QMessageBox.Yes)
                if res == QMessageBox.Yes:
                    self.chooseNewCarindb()
                    self.RegenerateMenu()
                return
        #if file in path - not carindb file
        if not self.isCarinb(filePath):
            msg = self.tr('This is not carindb by inner structure.\nDo you want\
 to remove path from recent?\n{}').format(filePath)
            res = QMessageBox.question(None,
                                       self.tr('Delete from recent files'),
                                       msg,
                                       QMessageBox.Yes | QMessageBox.Cancel,
                                       QMessageBox.Cancel)
            if res == QMessageBox.Cancel:
                return
            else:
                Settings.removeRecentFiles(filePath)
                self.RegenerateMenu()
                msg = self.tr('Do you want to load another carindb?')
                res = QMessageBox.question(None,
                                           self.tr('Open another carindb'),
                                           msg,
                                           QMessageBox.Yes | QMessageBox.Cancel,
                                           QMessageBox.Yes)
                if res == QMessageBox.Yes:
                    self.chooseNewCarindb()
                    self.RegenerateMenu()
                return

    def clearRecentList(self) -> None:
        """ Clearing ALL recent list """
        Settings.clearRecentFiles()
        self.RegenerateMenu()


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
