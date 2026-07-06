import sys
import random
from qgis.PyQt import QtWidgets, QtCore, QtGui

# from PyQt5 import QtWidgets, QtCore


class CollapsibleGroupBox(QtWidgets.QGroupBox):

    # def __init__(self, title="", parent=None):
    def __init__(self, parent=None):
        # super().__init__(title, parent)
        super().__init__(parent)

        self.setCheckable(True)
        self.setChecked(True)  # по умолчанию раскрыто
        self._collapsed_height = 0
        self._original_height = None

        # Сохраняем высоту содержимого (без рамки и заголовка)
        self.toggled.connect(self._on_toggled)

    def _on_toggled(self, checked: bool):
        if checked:
            # Развернуть: вернуть исходную высоту
            # if self._original_height is not None:
            #     self.setMaximumHeight(self._original_height)
            for child in self.children():
                if isinstance(child, QtWidgets.QWidget):
                    child.setVisible(True)
        else:
            # Свернуть: скрыть содержимое и уменьшить высоту
            self._original_height = self.sizeHint().height()
            for child in self.children():
                if isinstance(child, QtWidgets.QWidget) and child is not self.findChild(QtWidgets.QCheckBox):   # noqa
                    # Не скрываем сам чекбокс в заголовке
                    child.setVisible(False)
            # Минимальная высота — только заголовок + рамка
            # self.setMaximumHeight(self.fontMetrics().height() + 20)
        pass

    # Опционально: можно переопределить sizeHint, чтобы он учитывал состояние
    def sizeHint(self):
        base = super().sizeHint()
        if not self.isChecked():
            # Возвращаем минимальную высоту (только заголовок)
            return QtCore.QSize(base.width(), self.fontMetrics().height() + 20)
        return base


# --------------------------------------------------------------------------------
# CollapsibleBox
class CollapsibleBox(QtWidgets.QWidget):
    def __init__(self, title="", parent=None):
        super(CollapsibleBox, self).__init__(parent)
        # super().__init__(title, parent)
        # super().__init__(parent)

        self.toggle_button = QtWidgets.QToolButton(
            text=title, checkable=True, checked=False
        )
        self.toggle_button.setStyleSheet("""
            QToolButton {
                border: 2px solid #09009B;
                border-radius: 4px;
                min-width:  145px;
                min-height:  30px;
            }
            QToolButton::checked {
                border: 2px solid #ff009B;
            }
        """)
        
        self.toggle_button.setToolButtonStyle(
            QtCore.Qt.ToolButtonTextBesideIcon
        )
        self.toggle_button.setArrowType(QtCore.Qt.RightArrow)
        self.toggle_button.pressed.connect(self.on_pressed)

        self.toggle_animation = QtCore.QParallelAnimationGroup(self)

        self.content_area = QtWidgets.QScrollArea(
            maximumHeight=0, minimumHeight=0
        )
        self.content_area.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self.content_area, b"maximumHeight")
        )

    @QtCore.pyqtSlot()
    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(
            QtCore.Qt.DownArrow if not checked else QtCore.Qt.RightArrow
        )
        self.toggle_animation.setDirection(
            QtCore.QAbstractAnimation.Forward
            if not checked
            else QtCore.QAbstractAnimation.Backward
        )
        self.toggle_animation.start()

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        collapsed_height = (
            self.sizeHint().height() - self.content_area.maximumHeight()
        )
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(500)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)
        

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        centralWidget = QtWidgets.QWidget()
        self.setCentralWidget(centralWidget)
        vlay = QtWidgets.QVBoxLayout(centralWidget)
        
        _list = ['PREMINT', 'ALPHABOT', 'SUPERFULL', 'FREENFT',]
        
        for i, title in enumerate(_list):
            box = CollapsibleGroupBox(title)
            vlay.addWidget(box)
            lay = QtWidgets.QVBoxLayout()
            lay.setSpacing(0)
            lay.setContentsMargins(0, 0, 0, 0)
            for j in range(3):
                textButton = "Button {}-{}".format(i, j)
                pushButton = QtWidgets.QPushButton(textButton, clicked=lambda _, t=textButton: print(t)) # noqa
                pushButton.setMaximumWidth(150)
                pushButton.setMinimumHeight(25)
                
                color = QtGui.QColor(*[random.randint(0, 255) for _ in range(3)])
                pushButton.setStyleSheet(
                    "background-color: {}; color : white;".format(color.name())
                )
                
                lay.addWidget(pushButton)
            box.setContentLayout(lay)
            
        vlay.addStretch()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.resize(640, 570)
    w.show()
    sys.exit(app.exec())
