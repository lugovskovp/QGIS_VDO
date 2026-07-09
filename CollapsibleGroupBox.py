
from qgis.PyQt import QtWidgets, QtCore
from qgis.PyQt.QtWidgets import (QSizePolicy, QGroupBox,
                                 QStyleOptionGroupBox, QStyle)
# from qgis.PyQt.QtCore import QEasingCurve, pyqtProperty
from qgis.PyQt.QtGui import QMouseEvent

from QGIS_VDO.settings import Settings


# --------------------------------------------------------------------------------
# CollapsibleBox    AnimatedGroupBox

class AnimatedGroupBox(QGroupBox):    # Наследуемся от QGroupBox
    def __init__(self, parent=None):
        super().__init__(parent)

        # Переменная для хранения текста заголовка
        self._custom_title = ""
        # Переменная, хранящая состояние свернуто/развернуто
        self.isExpanded = True
        self._collapsed_height = 0
        self._original_height = None

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        pass

    # --- ПЕРЕХВАТ ЗАГОЛОВКА ИЗ QT DESIGNER ---
    def setTitle(self, title: str):
        """
        Этот метод uic вызовет автоматически сразу после __init__,
        передав туда строку из стандартного свойства 'title' в Designer.
        """
        # Сохраняем полученный текст в нашу внутреннюю переменную
        self._custom_title = title
        arrow = "▲" if self.isExpanded else "▼"
        super().setTitle(f"{arrow} {self._custom_title}")

    def title(self) -> str:
        """Переопределяем геттер, чтобы код извне мог получить заголовок методом .title()"""  # noqa
        return self._custom_title

    def mousePressEvent(self, event: QMouseEvent):
        # 1. Get the bounding box of the group box title text
        opt = QStyleOptionGroupBox()
        self.initStyleOption(opt)
        # 2. Check if the mouse click hits only the title area
        sc = self.style().hitTestComplexControl(QStyle.CC_GroupBox, opt, event.pos(), self)   # noqa
        if sc & QStyle.SC_GroupBoxLabel:
            print("You clicked the title!")
            # Trigger your custom action here
            self.toggle_state(not self.isExpanded)
        # Pass the event to the base class so regular clicks work
        super().mousePressEvent(event)

    def toggle_state(self, checked: bool):
        self.isExpanded = checked
        
        self.setTitle(self.title())
        
        if checked:
            # Развернуть: вернуть исходную высоту
            if self._original_height is not None:
                self.setFixedHeight(self._original_height)
                # self.setFixedHeight(200)
            for child in self.children():
                if isinstance(child, QtWidgets.QWidget):
                    child.setVisible(True)
            # self.setSizePolicy(QSizeP.Preferred, QSizePolicy.Preferred)
            # self.updateGeometry()
        else:
            # Свернуть: скрыть содержимое и уменьшить высоту
            self.adjustSize()
            # self._original_height = self.sizeHint().height()
            self._original_height = self.height()
            for child in self.children():
                if isinstance(child, QtWidgets.QWidget) and child is not self.findChild(QtWidgets.QCheckBox):   # noqa
                    # Не скрываем сам чекбокс в заголовке
                    child.setVisible(False)
            # Минимальная высота — только заголовок + рамка
            self.setFixedHeight(self.fontMetrics().height() + 10)
            self.updateGeometry()
        # Сохраняем в настройках видимость
        name = self.objectName()
        Settings.setShowGroupBoxEnabled(name, checked)

    # Опционально: можно переопределить sizeHint, чтобы он учитывал состояние
    def sizeHint(self):
        base = super().sizeHint()
        if not self.isChecked():
            # Возвращаем минимальную высоту (только заголовок)
            return QtCore.QSize(base.width(), self.fontMetrics().height() + 100)
        return base
