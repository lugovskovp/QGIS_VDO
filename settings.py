''' Carindb VDO
A QGIS plugin Settings class
Systeme Guidage Carminat C-IQ navigation database viewer

        begin                : 2026-05-12
        copyright            : (C) 2026 by Sweet Home
        email                : p.lugovskov@gmail.com
        git sha              : https://github.com/lugovskovp/QGIS_VDO

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.'''

import os.path
from qgis.PyQt.QtCore import Qt, QSettings


class Settings():
    """A helper class for handling reloader's all QSettings."""

    PREFIX = '/QGIS_VDO'
    """QSettings branch used by the plugin"""
    DEFAULT_RECENT_FILES_COUNT = 5
    """Max showed number of files carindb in menu"""
    MAX_RECENT_FILES_COUNT = 21
    """Maximal stored quontity files carindb in menu"""

    # Value names for saving|loading
    NAME_RECENT_FILES = 'RecentFiles'
    NAME_RECENT_FILES_COUNT = 'RecentFilesCount'
    NAME_LAST_PATH = 'LastFileNamePath'
    NAME_TOOL_BUTTON_TEXT = 'toolButtonTextEnabled'

    # RecentFilesCount
    @classmethod
    def RecentFilesCount(cls) -> int:
        """Get the number of recent plugins to display in the menu."""
        val = QSettings().value(f'{cls.PREFIX}/{cls.NAME_RECENT_FILES_COUNT}',
                                cls.DEFAULT_RECENT_FILES_COUNT,
                                type=int)
        return val

    @classmethod
    def setRecentFilesCount(cls, count: int) -> None:
        """Set number of recent plugins to display in the menu."""
        QSettings().setValue(f'{cls.PREFIX}/{cls.NAME_RECENT_FILES_COUNT}', count)

    # LastFileNamePath
    @classmethod
    def LastFileNamePath(cls) -> str:
        """ Get last opened folder """
        path = QSettings().value(f'{cls.PREFIX}/{cls.NAME_LAST_PATH}',
                                 '', type=str)
        return path

    @classmethod
    def setLastFileNamePath(cls, path: os.path) -> None:
        """ Setting last opened file path """
        QSettings().setValue(f'{cls.PREFIX}/{cls.NAME_LAST_PATH}', path)

    # RecentFiles
    @classmethod
    def RecentFiles(cls, ListAll: bool = False) -> list[str]:
        """ Get sorted (by design) list last loaded carindb
        
        :param listAll: List all stored plugins instead of cropping
        to the currently configured number.
        """
        files_vdo = list(QSettings().value(f'{cls.PREFIX}/{cls.NAME_RECENT_FILES}',
                                           '', type=str))
        if not ListAll:
            files_vdo = files_vdo[:cls.RecentFilesCount()]
        return files_vdo

    @classmethod
    def updateRecentFiles(cls, recentFile: str):
        """ Set the recently carindb list. The most recent first."""
        all_files = cls.RecentFiles(True)
        if recentFile in all_files:
            all_files.remove(recentFile)
        all_files = [recentFile] + all_files
        all_files = all_files[:cls.MAX_RECENT_FILES_COUNT]
        QSettings().setValue(f'{cls.PREFIX}/{cls.NAME_RECENT_FILES}', all_files)

    def clearRecentFiles(cls):
        """ Setting recently files to []"""
        QSettings().setValue(f'{cls.PREFIX}/{cls.NAME_RECENT_FILES}', [])

    # toolButtonStyle
    @classmethod
    def toolButtonStyle(cls) -> Qt.ToolButtonStyle:
        """Get toolbar button style (with text or icon only)."""
        if cls.toolButtonTextEnabled():
            buttonStyle = Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        else:
            buttonStyle = Qt.ToolButtonStyle.ToolButtonIconOnly
        return buttonStyle
    
    @classmethod
    def toolButtonTextEnabled(cls) -> bool:
        """Whether to display text beside the toolbar icon."""
        return QSettings().value(f'{cls.PREFIX}/{cls.NAME_TOOL_BUTTON_TEXT}',
                                 True, type=bool)

    @classmethod
    def setToolButtonTextEnabled(cls, state: bool) -> None:
        """Enable or disable text displayed beside the toolbar icon."""
        QSettings().setValue(f'{cls.PREFIX}/{cls.NAME_TOOL_BUTTON_TEXT}', state)
