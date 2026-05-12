''' Carindb VDO
A QGIS plugin Settings UI class
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
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QWidget

from .settings import Settings


FORM_CLASS = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), 'ConfigurationDialogBase.ui'))[0]


class ConfigurationDialog(QDialog, FORM_CLASS):
    """Plugin Reloader Configuration Window."""

    def __init__(self, parent: QWidget):
        """Pseudoconstructor."""
        super().__init__(parent)
        self.setupUi(self)
        self.cbToolButtonText.setChecked(Settings.toolButtonTextEnabled())
        if rpc := Settings.RecentFilesCount():
            self.sbRecentFilesCount.setValue(rpc)

    def accept(self):
        """Accept."""
        Settings.setToolButtonTextEnabled(self.cbToolButtonText.isChecked())
        Settings.setRecentFilesCount(self.sbRecentFilesCount.value())
        super().accept()
