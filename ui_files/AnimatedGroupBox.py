"""

"""
from qgis.PyQt import QtWidgets, QtCore
from qgis.PyQt.QtWidgets import QSizePolicy, QGroupBox, QStyleOptionGroupBox, QStyle
from qgis.PyQt.QtGui import QMouseEvent

from QGIS_VDO.settings import Settings


class AnimatedGroupBox(QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._custom_title = ""
        self.isExpanded = True
        self._original_height = None

        # Разрешаем панели сжиматься до минимума по вертикали
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def setTitle(self, title: str):
        """Автоматически вызывается uic при загрузке .ui файла."""
        self._custom_title = title
        arrow = "▲" if self.isExpanded else "▼"
        super().setTitle(f"{arrow} {self._custom_title}")

    def title(self) -> str:
        """Геттер для получения чистого заголовка без стрелочек."""
        return self._custom_title

    def mousePressEvent(self, event: QMouseEvent):
        """Перехват клика по заголовку."""
        opt = QStyleOptionGroupBox()
        self.initStyleOption(opt)
        
        # Проверяем, попал ли клик именно в область текста/заголовка
        sc = self.style().hitTestComplexControl(QStyle.CC_GroupBox, opt, event.pos(), self)
        if sc & QStyle.SC_GroupBoxLabel:
            self.toggle_state(not self.isExpanded)
            event.accept()  # Говорим системе, что событие обработано
            return
            
        super().mousePressEvent(event)

    def toggle_state(self, checked: bool):
        """Переключение состояния свернуто/развернуто."""
        self.isExpanded = checked
        self.setTitle(self.title())
        
        # Рассчитываем базовую высоту заголовочной части с учетом High DPI
        title_height = self.fontMetrics().height() + self.style().pixelMetric(QStyle.PM_LayoutTopMargin) * 2

        if checked:
            # --- РАЗВЕРНУТЬ ---
            # Возвращаем все дочерние виджеты в исходную видимость
            for child in self.children():
                if isinstance(child, QtWidgets.QWidget):
                    child.setVisible(True)
            
            # Снимаем ограничения по высоте
            self.setMaximumHeight(16777215)  # QWIDGETSIZE_MAX
            if self._original_height is not None:
                self.resize(self.width(), self._original_height)
        else:
            # --- СВЕРНУТЬ ---
            # Сохраняем текущую высоту перед скрытием
            self._original_height = self.height()
            
            # Скрываем абсолютно ВСЕ дочерние элементы интерфейса внутри панели
            for child in self.children():
                if isinstance(child, QtWidgets.QWidget):
                    child.setVisible(False)
            
            # Ограничиваем максимальную высоту только размером заголовка
            self.setMaximumHeight(title_height)
            
        # Обязательно уведомляем родительский Layout, что геометрия виджета изменилась
        self.updateGeometry()
        if self.parentWidget() and self.parentWidget().layout():
            self.parentWidget().layout().activate()

        # Сохраняем состояние в настройки QGIS плагина
        name = self.objectName()
        if name:  # Защита на случай, если objectName не задан в Designer
            Settings.setShowGroupBoxEnabled(name, checked)

    def sizeHint(self) -> QtCore.QSize:
        """Корректировка подсказки размера для системы автоверстки."""
        base = super().sizeHint()
        if not self.isExpanded:
            # Если свернуто, сообщаем компоновщику минимально необходимую высоту заголовка
            title_height = self.fontMetrics().height() + self.style().pixelMetric(QStyle.PM_LayoutTopMargin) * 2
            return QtCore.QSize(base.width(), title_height)
        return base
