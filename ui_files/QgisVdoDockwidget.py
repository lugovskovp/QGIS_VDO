"""


"""

import os
import re

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import QMetaType
from qgis.PyQt.QtGui import QColor
from qgis.core import (Qgis, QgsProject, QgsVectorLayer, QgsField,
                       QgsSingleSymbolRenderer, QgsFillSymbol,
                       QgsPointXY, QgsRectangle, QgsGeometry, QgsFeature,
                       QgsLayerTreeGroup, QgsCoordinateTransform)

from QGIS_VDO.settings import Settings
from QGIS_VDO.CollapsibleGroupBox import CollapsibleGroupBox
from QGIS_VDO.vdo import VDO_FILE
from QGIS_VDO.vdo.consts import NAME_LAYER_GLOBAL_BOUNDS
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
        # установить предыдуще установленную видимость groupBoxes
        GB = ['groupBox_0veral', 'groupBox_area_A', 'groupBox_area_B',
              'groupBox_i_label', 'groupBox_i_description', 'groupBox_i_information']
        for gb in GB:
            ch = Settings.ShowGroupBoxEnabled(gb)
            wi = self.findChild(CollapsibleGroupBox, gb)
            if wi is not None:
                wi.setChecked(ch)
        
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
            formatted = f"{self.vdo.file_size:,}".replace(',', ' ')
            self.l_vdo_size_val.setText(f"0x{self.vdo.file_size:04X} / {formatted}")
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

            # привязать pb_Action
            self.pb_Action.clicked.connect(self.pbActionEvent)

            # ----------------------------------------------
            pass
        else:   # if self.vdo.path is not None:
            # TODO: vdo None -> unactivate fields?
            pass
        pass

    def DrawTocAreas(self):
        """Отображает на карте area_A, area_b"""
        # Проверить наличие открытого/активного сохранённого проекта
        project = QgsProject.instance()
        if not project.fileName():
            # Сообщение - что надо, чтобы был открыт проект.
            self.iface.messageBar().pushMessage(
                    self.tr('Open/create any qgis project and reopen Carindb.'),   # noqa
                    Qgis.Warning, 3)
            return
        
        # old dbrev?
        if self.vdo.dbrev != 34:
            # Сообщение - что area a, b only in v.34
            self.iface.messageBar().pushMessage(
                    self.tr('Where are no Area_A, Area_B in this Carindb.'),   # noqa
                    Qgis.Warning, 3)
            return
        #
        root_group_name = self.vdo.QGISvdoGroupName
        # Access the main root of the QGIS layer tree
        root = project.layerTreeRoot()
        # If it doesn't exist, create it
        if not (root_group := root.findGroup(root_group_name)):
            root_group = root.insertGroup(0, root_group_name)

        layer_name = NAME_LAYER_GLOBAL_BOUNDS
        #  существует ли уже слой с таким именем в прямых потомках root группы
        found = False
        for child in root_group.children():
            # Проверяем, что это узел слоя (а не подгруппа) и имя совпадает
            if child.nodeType() == child.NodeLayer and child.name() == layer_name:
                found = True
                # Получаем сам объект слоя, он нужен для работы
                layer = child.layer()
                break
        
        if not found:
            # Создаем сам слой

            # Настраиваем параметры нового слоя в памяти (Memory Layer)
            # Формат: "ТипГеометрии?crs=EPSG:Код"  EPSG:4326 grad    EPSG:3395 - meters
            # Доступные типы: Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon  # noqa
            geometry_type = "Polygon?crs=EPSG:4326"
            layer = QgsVectorLayer(geometry_type, layer_name, "memory")

            # Добавляем атрибутивные поля (колонки) в таблицу нового слоя
            provider = layer.dataProvider()
            provider.addAttributes([
                QgsField("id", QMetaType.Type.Int),            # noqa 
                QgsField("name", QMetaType.Type.QString),      # noqa
                QgsField("value", QMetaType.Type.QString)      # noqa Double
            ])

            # Обновляем поля в слое после их добавления в провайдер
            layer.updateFields()

            # Настраиваем стиль (Символогию)
            # Создаем дефолтный символ для полигона
            symbol = QgsFillSymbol.createSimple({'name': 'square'})
            
            # НАСТРОЙКА ЦВЕТА ЗАЛИВКИ (RGBA: Красный, Зеленый, Синий, Альфа/Прозрачность от 0 до 255) # noqa
            # 128 в конце означает 50% прозрачности (0 - полностью прозрачный, 255 - сплошной)  # noqa
            fill_color = QColor(34, 139, 34, 20)   # Лесной зеленый с 20% прозрачностью
            symbol.setColor(fill_color)
            
            # НАСТРОЙКА ГРАНИЦЫ
            symbol.symbolLayer(0).setStrokeColor(QColor(0, 0, 0, 255))  # Черный цвет границы (сплошной) # noqa
            symbol.symbolLayer(0).setStrokeWidth(0.6)                   # Толщина границы в миллиметрах  # noqa
            # Доступные стили границы: Qt.SolidLine, Qt.DashLine, Qt.DotLine и т.д.
            
            # НАСТРОЙКА ОБЩЕЙ ПРОЗРАЧНОСТИ СЛОЯ (Альтернативный вариант от 0.0 до 1.0)
            # symbol.setOpacity(0.7) # 70% непрозрачности для всего символа целиком
            
            # 4. Применяем настроенный символ к рендереру слоя
            renderer = QgsSingleSymbolRenderer(symbol)
            layer.setRenderer(renderer)
            
            # Обновляем отображение слоя
            layer.triggerRepaint()

            # 5. Проверяем валидность и добавляем слой в нашу верхнюю группу
            if layer.isValid():
                # Регистрируем в проекте без автоматического отображения в панели (False)  # noqa
                QgsProject.instance().addMapLayer(layer, False) # noqa
                
                # Вставляем слой на первое место внутри нашей новой группы
                root_group.insertLayer(0, layer)
                print("Новый слой успешно создан в памяти и добавлен наверх!")
            else:
                print("Не удалось создать новый слой.")

        # hide all another vdo root groups but root_group_name
        self.iface.setActiveLayer(layer)
        root_group.setItemVisibilityChecked(True)
        if Settings.HideNonActiveVdoEnabled():
            # 1. Задаем регулярное выражение для поиска
            pattern = r"_0x[0-9a-f]{4,}$"
            regex = re.compile(pattern, re.IGNORECASE)

            for child in project.layerTreeRoot().children():
                if isinstance(child, QgsLayerTreeGroup):
                    if child.name() != root_group_name:
                        # Проверяем имя группы через regexp
                        if regex.search(child.name()):
                            child.setItemVisibilityChecked(False)

            pass

        # # If it doesn't exist, create it
        # if not (root_group := root.findGroup(root_group_name)):
        #     root_group = root.insertGroup(0, root_group_name)

        #
        bl_toc: block_0x12 = self.vdo.get_block(0)

        # Area_A bigger
        self._DrawArea(bl_toc.area_B, "Area_B", layer)
        self._DrawArea(bl_toc.area_A, "Area_A", layer)
        
        # Масштаб по границам слоя feat: приблизить карту по границам (содержимому) слоя
        # Получаем доступ к карте (холсту)
        canvas = self.iface.mapCanvas()
        # Создаем трансформер координат
        transform = QgsCoordinateTransform(layer.crs(), project.crs(), project)
        # Устанавливаем масштаб карты по границам слоя
        # Трансформируем границы слоя в СК проекта
        layer_extent = layer.extent()
        layer_extent.scale(1.2)
        project_extent = transform.transformBoundingBox(layer_extent)
        # Зумируем
        canvas.setExtent(project_extent)
        # Обновляем карту для отображения изменений
        canvas.refresh()
        pass

    def _DrawArea(self, area, area_name: str, layer: QgsVectorLayer) -> None:
        """
        Рисует прямоугольник в слое layer.
        Args:
            area (coord lb, coord rt)
            area_name: str
            layer: QgsVectorLayer
        """
        # если есть объект с таким именем - возврат
        # Перебираем все объекты слоя
        for feature in layer.getFeatures():
            # feature.id() — уникальный внутренний номер объекта в QGIS
            # feature.attributes() — список всех текстовых/числовых значений в таблице
            if feature.attribute('name') == area_name:
                return
            print(f"ID: {feature.id()} | {feature.attribute('name')} | Данные: {feature.attributes()}")  # noqa

        # если слой не poligone - возврат
        if not layer or layer.geometryType() != Qgis.GeometryType.Polygon:
            print("Ошибка: Пожалуйста, выберите ПОЛИГОНАЛЬНЫЙ слой для прямоугольника!")
            return

        # координаты точек
        p_lb = QgsPointXY(area[0].lon, area[0].lat)
        p_rt = QgsPointXY(area[1].lon, area[1].lat)

        # Создаем геометрию прямоугольника
        rect = QgsRectangle(p_lb, p_rt)
        geom = QgsGeometry.fromRect(rect)
        
        # Создаем новый объект (Feature) и присваиваем ему геометрию
        feature = QgsFeature()
        feature.setGeometry(geom)
        
        # Если в слое есть атрибуты, можно задать дефолтные значения (опционально)
        feature.setAttributes([1, area_name, f"{area[0].__repr__()}, {area[1].__repr__()}"])  # noqa

        # Начинаем редактирование слоя и добавляем объект
        layer.startEditing()
        success = layer.addFeature(feature)

        if success:
            layer.commitChanges()    # Сохраняем изменения
            layer.triggerRepaint()   # Обновляем карту
            print("Прямоугольник успешно добавлен на слой!")
        else:
            layer.rollBack()     # Отменяем правки в случае ошибки
            print("Не удалось добавить объект на слой.")

        pass

    def closeEvent(self, event):
        # self.closingPlugin.emit()
        # event.accept()
        pass

    def pbActionEvent(self, event):
        
        pass
