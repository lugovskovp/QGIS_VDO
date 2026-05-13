''' Carindb VDO
A QGIS plugin Settings class
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
from qgis.PyQt.QtCore import Qt, QSettings


class Settings():
    """A helper class for handling reloader's all QSettings."""

    PREFIX = '/QGIS_VDO'
    """QSettings branch used by the plugin"""

    DEFAULT_RECENT_FILES_COUNT = 5

    # RecentFilesCount
    @classmethod
    def RecentFilesCount(cls) -> int:
        """Get the number of recent plugins to display in the menu."""
        val = QSettings().value(f'{cls.PREFIX}/RecentFilesCount',
                                cls.DEFAULT_RECENT_FILES_COUNT,
                                type=int)
        return val

    @classmethod
    def setRecentFilesCount(cls, count: int) -> None:
        """Set number of recent plugins to display in the menu."""
        QSettings().setValue(f'{cls.PREFIX}/RecentFilesCount', count)

    # LastFileNamePath
    @classmethod
    def LastFileNamePath(cls) -> str:
        """ Get last opened folder """
        path = QSettings().value(f'{cls.PREFIX}/LastFileNamePath',
                                 '', type=str)
        return path

    @classmethod
    def setLastFileNamePath(cls, path: os.path) -> None:
        """ Setting last opened file path """
        QSettings().setValue(f'{cls.PREFIX}/LastFileNamePath', path)

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
        return QSettings().value(f'{cls.PREFIX}/toolButtonTextEnabled',
                                 True, type=bool)

    @classmethod
    def setToolButtonTextEnabled(cls, state: bool) -> None:
        """Enable or disable text displayed beside the toolbar icon."""
        QSettings().setValue(f'{cls.PREFIX}/toolButtonTextEnabled', state)
