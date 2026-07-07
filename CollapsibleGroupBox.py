
from qgis.PyQt import QtWidgets, QtCore
from QGIS_VDO.settings import Settings


class CollapsibleGroupBox(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)

        # name = self.objectName()
        self.setCheckable(True)
        self.setChecked(True)  # по умолчанию раскрыто
        self._collapsed_height = 0
        self._original_height = None

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
        # Сохраняем в настройках видимость
        name = self.objectName()
        Settings.setShowGroupBoxEnabled(name, checked)
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
