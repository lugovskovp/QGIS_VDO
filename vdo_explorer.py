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

from qgis.PyQt.QtCore import Qt, QSettings, QTranslator, QCoreApplication   # , QObject
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu, QToolButton, QMessageBox, QFileDialog, QDockWidget   # noqa
from qgis.core import Qgis  # , QgsMessageLog
from qgis.gui import QgisInterface

from .vdo import VDO_FILE
from .settings import Settings
from .ui_files.ConfigurationDialog import ConfigurationDialog
from .ui_files.QgisVdoDockwidget import QgisVdoDockwidget

#import logging

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

    vdo: VDO_FILE = None
    """ vdo carindb file """

    dockwidget: QDockWidget = None
    """ main dockwidget """

    def __init__(self, iface: QgisInterface):
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        self.iface = iface
        self.menu = None

        # QgsMessageLog.logMessage("Your plugin code has been executed correctly",
        #                          'MyPlugin', level=Qgis.MessageLevel.Info)
        # QgsMessageLog.logMessage("Your plugin code might have some problems",
        #                          level=Qgis.MessageLevel.Warning)
        # QgsMessageLog.logMessage("Your plugin code has crashed!",
        #                          level=Qgis.MessageLevel.Critical)
        
        #
        # self.log = logging.getLogger(__name__)
        # self.log.setLevel(logging.INFO)

        # filename = self.plugin_dir + '/log/myapp.log'
        # ch = logging.FileHandler(filename)
        # ch.setLevel(logging.INFO)

        # строка формата сообщения
        # strfmt = '[%(asctime)s] [%(name)s] [%(levelname)s] > %(message)s'
        # строка формата времени
        # datefmt = '%Y-%m-%d %H:%M:%S'
        # создаем форматтер
        # formatter = logging.Formatter(fmt=strfmt, datefmt=datefmt)

        # добавляем форматтер к 'ch'
        # ch.setFormatter(formatter)
        # добавляем ch в регистратор
        # self.log.addHandler(ch)

        # self.log.debug('__init__')
        #
        #self.dockwidget = None

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
        # self.log.debug('initGui <')
        iconConf = QIcon(os.path.join(os.path.dirname(__file__),
                         ICON_PATH_PLUGIN_CONFIG))
        # В меню Модули добавить меню плагина
        self.menu = self.iface.pluginMenu().addMenu(self.icon, self.tr("&Carindb VDO"))
        # Кнопка на панели
        self.toolButton = QToolButton()
        self.toolButton.setToolButtonStyle(Settings.toolButtonStyle())
        self.toolButton.setPopupMode(
            QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.toolButton.setMenu(QMenu())
        # Действие  открыть новый файл
        self.actionChooseNewCarindb = QAction(
            self.iconOpen, self.tr("Load Carindb ..."))
        self.actionChooseNewCarindb.setObjectName(ACTION_LOAD_NEW_CARINDB)
        self.actionChooseNewCarindb.triggered.connect(self.chooseNewCarindb)
        # Действие - очистить весь список последних файлов
        #if Settings.clearRecentFiles:
        self.actionClearRecent = QAction(self.iconAlert,
                                         self.tr("Clear ALL RECENT FILES list"))
        self.actionClearRecent.setObjectName(ACTION_CLEAR_RECENT_CARINDB)
        self.actionClearRecent.triggered.connect(self.clearRecentList)
        # Действие  Настройки Create action for opening the settings window
        self.actionSettings = QAction(iconConf, self.tr("Configure"))
        self.actionSettings.triggered.connect(self.openConfigWindow)
        self.RegenerateMenu()
        self.iface.addToolBarWidget(self.toolButton)
        # self.log.debug('initGui >')

    def unload(self):
        """Remove the plugin's actions from the QGIS menu and toolbars."""
        # self.log.debug('unload <')
        # self.iface.removeToolBarIcon(self.action)
        # del self.action
        if not self.menu:
            # The initGui() method was never called
            return
        if self.dockwidget is not None:
            self.iface.removeDockWidget(self.dockwidget)
            self.dockwidget = None
        self.iface.pluginMenu().removeAction(self.menu.menuAction())
        self.toolButton.deleteLater()
    
    def RegenerateMenu(self) -> None:
        """ (re?)create menu and button menu """
        # self.log.debug('RegenerateMenu <')
        
        #--- create actions
        # Create files for recently processed Действия из ранее открывавшихся файлов
        self.actionForPlugin = {}
        for f in Settings.RecentFiles():
            self.actionForPlugin[f] = self.createActionForPath(f)
        # и добавить открыть новый файл
        self.actionForPlugin[ACTION_LOAD_NEW_CARINDB] = self.actionChooseNewCarindb
        # Очистка меню
        toolButtonMenu = self.toolButton.menu()
        toolButtonMenu.clear()
        self.menu.clear()
        # Add all the rest of the actions to the menu and the toolbar
        defAction = self.actionChooseNewCarindb
        for action in self.actionForPlugin.values():
            if defAction == self.actionChooseNewCarindb and action.icon().isNull():
                # если дефолтное значение, но иконка текущего  = null (валидный vdo)
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
        if Settings.ShowClearRecentFilesEnabled():
            self.menu.addSeparator()
            self.menu.addAction(self.actionClearRecent)
        # self.log.debug('RegenerateMenu >')

    def run(self):
        """Run method that loads and starts the plugin"""
        if not self.pluginIsActive:
            self.pluginIsActive = True

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:     # noqa
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = QgisVdoDockwidget()
        
    def openConfigWindow(self):
        """Open the configuration dialog."""
        # self.log.debug('openConfigWindow <')
        dlg = ConfigurationDialog(self.iface.mainWindow())
        dlg.exec()
        if dlg.result():
            # обновить вид кнопки - с надписью или без
            if self.toolButton.toolButtonStyle() != Settings.toolButtonStyle():
                self.toolButton.setToolButtonStyle(Settings.toolButtonStyle())
            self.RegenerateMenu()
        
    def chooseNewCarindb(self):
        """ File open dialog and call load file func, if success"""
        # self.log.debug('chooseNewCarindb <')
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
        # self.log.debug('chooseNewCarindb >')

    def loadCarindb(self, path: os.path) -> bool:
        """ Load carindb file (if changed carindb)

        :param path: A path for loading carindb file.
        :type path: os.path
        """
        # self.log.debug('loadCarindb <')
        Settings.updateRecentFiles(path)
        self.RegenerateMenu()

        if os.path.exists(path):
            # open vdo
            if self.vdo is not None:
                if self.vdo.path != path:
                    # path поменялся
                    # TODO: а открыт ли уже dockwidget?
                    self.iface.removeDockWidget(self.dockwidget)
                    self.dockwidget = None
                    self.vdo = VDO_FILE(path)
            else:   # vdo None
                self.vdo = VDO_FILE(path)

            self.ShowMainWidget()
            return True
        # self.iface.messageBar().pushMessage(
        # self.tr('Plugin <b>{}</b> not found.').format(plugin),
        # Qgis.Warning, 1)
        self.vdo = None
        return False

    def isCarinb(self, filePath: os.path) -> bool:
        """ А carindb ли формата файл?

        :param path: A path for checking carindb file.
        :type path: os.path
        """
        # self.log.debug('isCarinb <' + filePath)
        # первые 8 байт любого carindb
        CORRECT_VDO_BEGIN = b'\x00\x00\x00\x01\x00\x12\x00\x00'
        with open(filePath, 'rb') as f:
            if f.read(8) == CORRECT_VDO_BEGIN:
                return True
            return False
        
    def createActionForPath(self, filePath: os.path) -> QAction:
        """ Create action from path

        :param path: A path to carindb file for creating QAction.
        :type path: os.path
        """
        # self.log.debug('isCarinb < ' + filePath)
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
        # self.log.debug('alertCarindb < ' + filePath)
        #if file carindb not found
        if not os.path.isfile(filePath):
            msg = self.tr('Can`t find file.\nDo you want to remove path from recent?\n{}').format(filePath) # noqa
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
            msg = self.tr('This is not carindb by inner structure.\nDo you want to remove path from recent?\n{}').format(filePath)  # noqa
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
        # self.log.debug('alertCarindb <')
        Settings.clearRecentFiles()
        self.RegenerateMenu()
        # self.log.debug('clearRecentList >')

    def ShowMainWidget(self):
        """открывает главный dockwidget"""
        if self.vdo.path is not None:
            if self.dockwidget is None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = QgisVdoDockwidget(self, self.iface)
                self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)  # noqa
            # если widget есть, то показать
            self.dockwidget.show()
            self.dockwidget.DrawTocAreas()
            return
        else:
            # self.vdo.path is None:
            # Сообщение - что надо, чтобы был открыт file.
            self.iface.messageBar().pushMessage(
                        self.tr('Open any Carindb file.'),   # noqa
                        Qgis.Warning, 3)
            pass

        return


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
