"""


"""

import os

from qgis.PyQt import QtWidgets, uic

# from qgis.PyQt import QtGui, QtWidgets, uic
# from qgis.PyQt.QtCore import pyqtSignal
# from PyQt5.QtWidgets import QVBoxLayout, QPushButton        #QWidget, QPushButton, QHBoxLayout, QVBoxLayout # noqa

# from .text_browser_dialog import TextBrowserDialog  # show Abstract, bibliogr, copyright files # noqa
from ..vdo import VDO_FILE


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'QgisVdoDockwidgetBase.ui'))


class QgisVdoDockwidget(QtWidgets.QDockWidget, FORM_CLASS):
    """

    """
    vdo: VDO_FILE = None
    """ vdo file"""

    def __init__(self, parent_plugin, iface, parent=None):
        """Constructor."""
        super(QgisVdoDockwidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.iface = iface
        self.vdo = parent_plugin.vdo
        
        self.setupUi(self)
        # vdo info
        bl_tos = self.vdo.get_block(0)
        #
        self.l_vdo_path.setText(self.vdo.path)
        # self.l_vdo_path.
        pass

    def closeEvent(self, event):
        # self.closingPlugin.emit()
        # event.accept()
        pass
