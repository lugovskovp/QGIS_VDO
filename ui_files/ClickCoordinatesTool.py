"""
класс инструмента карты на базе QgsMapTool.
вызывается нажатием кнопки self.pb_getCoordinates
и выключается после получения и вывода в консоль координат, либо по нажатию esc
Он будет автоматически отключаться (деактивироваться) после первого клика
или при нажатии клавиши Esc.
"""

from qgis.gui import QgsMapTool
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QCursor


class ClickCoordinatesTool(QgsMapTool):
    def __init__(self, canvas, callback, deactivate_callback):
        super().__init__(canvas)
        self.canvas = canvas
        self.callback = callback
        self.deactivate_callback = deactivate_callback

    # Срабатывает при клике мыши на карту
    def canvasReleaseEvent(self, event):
        # Получаем координаты в СК проекта
        point = self.toMapCoordinates(event.pos())
        self.callback(point)
        # Отключаем инструмент после клика
        self.canvas.unsetMapTool(self)

    # Срабатывает при нажатии клавиш
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            # Отключаем инструмент по нажатию Esc
            self.canvas.unsetMapTool(self)
            # Сообщаем системе, что событие обработано
            event.accept()

    def activate(self):
        # Устанавливаем курсор-перекрестие при активации инструмента
        self.canvas.setCursor(QCursor(Qt.CrossCursor))
        #  забираем фокус ввода на холст карты для перехвата Esc
        self.canvas.setFocus()
        super().activate()

    # Срабатывает при деактивации инструмента (unsetMapTool)
    def deactivate(self):
        # Возвращаем стандартный курсор-стрелку при выключении
        self.canvas.setCursor(QCursor(Qt.ArrowCursor))
        self.deactivate_callback()
        super().deactivate()
