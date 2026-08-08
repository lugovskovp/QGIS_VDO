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

    def canvasReleaseEvent(self, event):
        # 1. Получаем координаты точки клика
        point = self.toMapCoordinates(event.pos())
        
        # 2. Передаем координаты в callback (вывод в консоль / заполнение полей)
        if self.callback:
            self.callback(point)
            
        # 3. Сбрасываем инструмент холста.
        # setMapTool(None) безопасно деактивирует текущий инструмент и вызовет deactivate()
        self.canvas.setMapTool(None)

    def keyPressEvent(self, event):
        # Корректная проверка нажатия Esc для PyQt5/PyQt6
        if event.key() == Qt.Key_Escape or event.key() == 16777216:
            event.accept()
            self.canvas.setMapTool(None)

    def activate(self):
        super().activate()
        # Устанавливаем перекрестие и забираем фокус для перехвата клавиатуры
        self.canvas.setCursor(QCursor(Qt.CrossCursor))
        self.canvas.setFocus()

    def deactivate(self):
        # Возвращаем стандартный стрелочный курсор
        self.canvas.setCursor(QCursor(Qt.ArrowCursor))
        
        # Вызываем колбэк деактивации (например, чтобы "отжать" кнопку pb_getCoordinates)
        if self.deactivate_callback:
            self.deactivate_callback()
            
        super().deactivate()


Как теперь правильно подключить этот инструмент к вашей кнопке:В основном коде вашего плагина
(где инициализируется интерфейс и кнопка self.pb_getCoordinates) логика должна выглядеть так:

python
# Метод внутри вашего главного класса плагина
def initGui(self):
    # Делаем кнопку переключаемой (чтобы она оставалась нажатой, пока инструмент активен)
    self.pb_getCoordinates.setCheckable(True)
    self.pb_getCoordinates.clicked.connect(self.toggle_coordinate_tool)

def toggle_coordinate_tool(self):
    if self.pb_getCoordinates.isChecked():
        # Создаем и активируем инструмент
        self.coord_tool = ClickCoordinatesTool(
            canvas=self.iface.mapCanvas(),
            callback=self.print_coordinates,
            deactivate_callback=self.on_tool_deactivated
        )
        self.iface.mapCanvas().setMapTool(self.coord_tool)
    else:
        # Если кнопку отжали вручную
        self.iface.mapCanvas().setMapTool(None)

def print_coordinates(self, point):
    # Вывод в консоль QGIS (в СК проекта)
    print(f"Координаты клика: X: {point.x():.5f}, Y: {point.y():.5f}")

def on_tool_deactivated(self):
    # Этот метод вызовется автоматически при любом выключении инструмента (клик или Esc)
    # Гарантируем, что кнопка на панели вернется в "отжатое" состояние
    self.pb_getCoordinates.setChecked(False)


Используйте код с осторожностью.Если вы хотите доработать этот инструмент, дайте знать:

Нужно ли автоматически трансформировать координаты в WGS-84 (Долгота/Широта), если проект сохранен в другой
системе координат (например, UTM)?

Требуется ли визуально подсвечивать точку клика на карте временным маркером (QgsVertexMarker)?

"""
