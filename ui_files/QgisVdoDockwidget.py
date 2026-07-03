"""


"""

import os

from qgis.PyQt import QtWidgets, uic

# from qgis.PyQt import QtGui, QtWidgets, uic
# from qgis.PyQt.QtCore import pyqtSignal
# from PyQt5.QtWidgets import QVBoxLayout, QPushButton        #QWidget, QPushButton, QHBoxLayout, QVBoxLayout # noqa

# from .text_browser_dialog import TextBrowserDialog  # show Abstract, bibliogr, copyright files # noqa

from QGIS_VDO.vdo import VDO_FILE
from QGIS_VDO.vdo.blocks import block_0x12, block_0x13

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'QgisVdoDockwidgetBase.ui'))


class QgisVdoDockwidget(QtWidgets.QDockWidget, FORM_CLASS):
    """

    """
    vdo: VDO_FILE = None
    """current vdo file"""

    def __init__(self, parent_plugin, iface, parent=None):
        """Constructor."""
        super(QgisVdoDockwidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # widgets-and-dialogs-with-auto-connect
        self.iface = iface
        
        self.setupUi(self)
        
        self.vdo = parent_plugin.vdo
        #
        if self.vdo.path is not None:
            # path above overall info
            ap = self.vdo.path.split("/")
            actionName = ap[-2] + ":::" + ap[-1]
            self.groupBox_0veral.setTitle(actionName)
            # overall info
            self.l_vdo_dbrev_val.setText(f"0x{self.vdo.dbrev:02X} / {self.vdo.dbrev}")
            self.l_vdo_segsize_val.setText(f"0x{self.vdo.segsize:03X} / {self.vdo.segsize}")  # noqa
            fsize = os.path.getsize(self.vdo.path)
            formatted = f"{fsize:,}".replace(',', ' ')
            self.l_vdo_size_val.setText(formatted)
            self.l_vdo_path_val.setText(self.vdo.path)
            # vdo info
            bl_toc: block_0x12 = self.vdo.get_block(0)
            bl_bibliogr: block_0x13 = self.vdo.get_block(bl_toc.bladdr_bibliogr)
            # area_a-b only in rev34
            if self.vdo.dbrev != 34:
                self.groupBox_area_A.hide()
                self.groupBox_area_B.hide()
            else:
                # инфо areas на панель
                self.l_Alb_coord.setText(bl_toc.area_A[0].__repr__())
                self.l_Art_coord.setText(bl_toc.area_A[1].__repr__())
                self.l_Blb_coord.setText(bl_toc.area_B[0].__repr__())
                self.l_Brt_coord.setText(bl_toc.area_B[1].__repr__())
                # отрисовать

                pass
            # bl_13
            self.textBrowser_label.setPlainText(bl_bibliogr.str_label)
            self.textBrowser_descr.setPlainText(bl_bibliogr.str_description)
            self.textBrowser_info.setPlainText(bl_bibliogr.str_information)

        else:
            # TODO: vdo None -> unactive fields
            pass

        # vdo info
        #bl_tos = self.vdo.get_block(0)

        # self.l_vdo_path.
        
        pass

    def closeEvent(self, event):
        # self.closingPlugin.emit()
        # event.accept()
        pass
