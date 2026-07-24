"""
Основной dockedWidget
feat: DrawAlmanacArea еще и maps при создании рисует
"""

import os
import re

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtWidgets import QRadioButton, QButtonGroup
from qgis.PyQt.QtCore import QMetaType
from qgis.core import (Qgis, QgsProject, QgsVectorLayer, QgsField, QgsLayerTreeLayer,
                       QgsLayerTreeGroup, QgsCoordinateTransform)

from QGIS_VDO.settings import Settings, DEFAULT_SCALE
from QGIS_VDO.CollapsibleGroupBox import AnimatedGroupBox
from QGIS_VDO.vdo import VDO_FILE
from QGIS_VDO.vdo.blocks import (block_0x12,
                                 block_0x13,
                                 block_0x07,
                                 block_0x08,
                                 block_0x09)
from QGIS_VDO.vdo.blocks.block_0x07 import SCALE
from QGIS_VDO.vdo.consts import (NAME_LAYER_GLOBAL_BOUNDS,
                                 NAME_LAYER_ALMANACS,
                                 NAME_LAYER_MAPS)

from QGIS_VDO.ui_files.drawing import _DrawArea, getRendererByLayerName


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'QgisVdoDockwidgetBase.ui'))

# list groupbox collapsible - used for restore visibility
listGBC = ['groupBox_0veral', 'groupBox_area_A', 'groupBox_area_B',
           'groupBox_i_label', 'groupBox_i_description', 'groupBox_i_information',
           'gb_CategoriesPOI'
           ]
RB_SCALE_OBJNAME_PREFIX = 'rb_scale_'
SCALE_GROUP_NAME_PREFIX = 'Scale '
QTY_ALL_SCALES = 12


class QgisVdoDockwidget(QtWidgets.QDockWidget, FORM_CLASS):
    """
    Главный рабочий виджет для отображения выбранного carindb
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

        # Восстановить из настроек видимость groupBoxes
        self._restoreGroupBoxVisibility()

        # vdo
        self.vdo = parent_plugin.vdo
        if self.vdo.path is not None:
            # >>> tab_info
            self._initTabInfo()

            # >>> tab_addr

            # >>> tab_topo
            self._initTabTopo()

            # привязать pb_Action
            # self.pb_Action.clicked.connect(self.pbActionEvent)
            # ----------------------------------------------
            pass
        else:   # if self.vdo.path is not None:
            # TODO: vdo None -> make unactive groupbox?
            pass
        pass    # def __init__(self, parent_plugin, iface, parent=None):

    def DrawTocAreas(self):
        """
        Отображает на карте area_A, area_b
        Скрывает и сворачивает остальные toc группы
        """
        # Проверить наличие открытого/активного сохранённого проекта
        if not self._isExistsOpenProject():
            return
        project = QgsProject.instance()

        # получаем корневой ТОС area layer в группе
        layer = self._getRootAreaLayer()

        # hide all another vdo root groups but root_group_name
        self.iface.setActiveLayer(layer)
        root = project.layerTreeRoot()
        root_group = root.findGroup(self.vdo.QGISvdoGroupName)
        root_group.setItemVisibilityChecked(True)
        root_group.setExpanded(True)  # False — свернуть, True — развернуть

        # по значению настроек - скрываем все другие группы vdo
        if Settings.HideNonActiveVdoEnabled():
            # Задаем регулярное выражение для поиска корневых vdo групп
            pattern = r"_0x[0-9a-f]{4,}$"
            regex = re.compile(pattern, re.IGNORECASE)
            for child in project.layerTreeRoot().children():
                if isinstance(child, QgsLayerTreeGroup):
                    if child.name() != root_group.name():
                        # Проверяем имя группы через regexp
                        if regex.search(child.name()):
                            child.setItemVisibilityChecked(False)
                            child.setExpanded(False)  # False — свернуть, True — развернуть # noqa
            pass

        # Is dbrev old? no areas, show warning
        if self.vdo.dbrev != 34:
            # Сообщение - что area a, b only in v.34
            self.iface.messageBar().pushMessage(
                    self.tr('Where are no Area_A, Area_B in this Carindb.'),   # noqa
                    Qgis.Warning, 3)
            return

        # Areas from TOC block
        bl_toc: block_0x12 = self.vdo.get_block(0)
        area = [(bl_toc.area_B[0].lat, bl_toc.area_B[0].lon), (bl_toc.area_B[1].lat, bl_toc.area_B[1].lon)]  # noqa
        _DrawArea(area, "Area_B", layer)   # Area_A is bigger
        area = [(bl_toc.area_A[0].lat, bl_toc.area_A[0].lon), (bl_toc.area_A[1].lat, bl_toc.area_A[1].lon)]  # noqa
        _DrawArea(area, "Area_A", layer)
        
        # >>> Масштаб по границам слоя: приблизить карту по границам (содержимому) слоя
        # Получаем доступ к карте (холсту)
        canvas = self.iface.mapCanvas()
        # Создаем трансформер координат
        transform = QgsCoordinateTransform(layer.crs(), project.crs(), project)
        # Трансформируем границы слоя в СК проекта
        layer_extent = layer.extent()
        layer_extent.scale(1.2)     # отступ +20% от границ
        project_extent = transform.transformBoundingBox(layer_extent)
        # Зуммируем
        canvas.setExtent(project_extent)
        # Обновляем карту для отображения изменений
        canvas.refresh()
        pass

    def DrawAlmanacArea(self, idScale: int) -> None:
        """
        Добавляет слой Almanac, если не было его ранее
        отрисовывает валидные альманахи
        """
        # Проверить наличие открытого/активного сохранённого проекта
        if not self._isExistsOpenProject():
            return

        # Получить слой для альманаха.abs
        layer = self._getLayer(idScale, NAME_LAYER_ALMANACS, 'Polygon')
        # Получить слой для альманаха.abs
        layer_maps = self._getLayer(idScale, NAME_LAYER_MAPS, 'Polygon')
        
        # Получить альманах и отрисовать
        sc: SCALE = self.scales[idScale]
        bl_almanac: block_0x08 = self.vdo.get_block(sc.almanac_idx, sc.area[0], sc.area[1])   # noqa
        for (bladdr_fldr_val, lat0, lon0, lat1, lon1) in bl_almanac.get_items():  # noqa
            #             print(bladdr_fldr, point_lb, point_rt)
            # при отрисовке поле name уникальное - второй раз не отрисовывается
            area = [(lat0, lon0), (lat1, lon1)]  # noqa
            _DrawArea(area, f"0x{bladdr_fldr_val:X}", layer)  # noqa
            # break
            if False:
                bladdr_map: block_0x09
                _DrawArea([point_lb, point_rt], f"0x{bladdr_map}".replace(' ', ''), layer_maps)  # noqa
            # и отрисовываем контуры блоков карт
            # bl_folder: block_0x09 = self.vdo.get_block(bladdr_fldr_val)
            # for (bladdr_map, point_lb, point_rt) in bl_folder.items(point_fldr_lb):
            #     # _DrawArea([point_lb, point_rt], f"0x{bladdr_map}".replace(' ', ''), layer_maps)  # noqa
            #     pass  (203.910287S 75.001364W, 86.000034N 214.908958E)
            pass
    
        print(NAME_LAYER_ALMANACS)
        pass

    # <<<<<<<<<<<<< функции инициализации вкладок
           
    def _initTabInfo(self) -> None:
        """
        Инициализация вкладки Info
        """
        # path above overall info
        ap = self.vdo.path.split("/")
        actionName = ap[-2] + ":::" + ap[-1]
        del ap
        self.groupBox_0veral.setTitle(actionName)
        # overall info
        self.l_vdo_dbrev_val.setText(f"0x{self.vdo.dbrev:02X} / {self.vdo.dbrev}")
        self.l_vdo_segsize_val.setText(f"0x{self.vdo.segsize:03X} / {self.vdo.segsize}")  # noqa
        formatted = f"{self.vdo.file_size:,}".replace(',', ' ')
        self.l_vdo_size_val.setText(f"0x{self.vdo.file_size:04X} / {formatted}")
        self.l_vdo_path_val.setText(self.vdo.path)
        del formatted
        # vdo info
        bl_toc: block_0x12 = self.vdo.get_block(0)
        bl_bibliogr: block_0x13 = self.vdo.get_block(bl_toc.bladdr_bibliogr)
        bl_scales: block_0x07 = self.vdo.get_block(bl_toc.bladdr_scales)
        self.scales = bl_scales.scales
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
            pass
        # bl_13
        self.textBrowser_label.setPlainText(bl_bibliogr.str_label)
        self.textBrowser_descr.setPlainText(bl_bibliogr.str_description)
        self.textBrowser_info.setPlainText(bl_bibliogr.str_information)

    def _initTabTopo(self) -> None:
        """
        Инициализация вкладки Topo
        Собрать scale radioButtons в QButtonGroup
        (к моменту вызова _restoreScale список масштабов уже есть)
        """
        # Восстановить из настроек ранее установленный scale
        checkScale = Settings.ChousedScale()
        if self.scales[checkScale].isEmpty:
            checkScale = DEFAULT_SCALE
        if self.scales[checkScale].isEmpty:
            for i in range(QTY_ALL_SCALES):
                if not self.scales[i].isEmpty:
                    checkScale = i
                    break
        # root group - vdo
        root = self._getRootGroup()
        # Создаем ОБЩУЮ группу для всех радиокнопок масштабов
        self.button_group_scale = QButtonGroup(self)
        # добавляем в группу все кнопки rb_scale_[0..11]
        for id in range(QTY_ALL_SCALES):
            rb_name = RB_SCALE_OBJNAME_PREFIX + str(id)
            rb = self.tabWidget.findChild(QRadioButton, rb_name)
            # Изменить подпись: номер scale, value_a, масштаб от и до
            sc: SCALE = self.scales[id]
            rb.setText("{}  {}: {} - {}".format(id, sc.value_a, sc.zoom_from, sc.zoom_to))  # noqa
            # Установить enabled|disabled
            rb.setEnabled(not sc.isEmpty)
            # параллельно с rb создаём группы масштабов для отображения.
            if not sc.isEmpty:
                gr_name = SCALE_GROUP_NAME_PREFIX + str(id)
                if not (root.findGroup(gr_name)):
                    root.insertGroup(-2, gr_name)
            # добавляем в группу rb
            self.button_group_scale.addButton(rb, id)
            pass
        # Connect the change signal button_group_scale
        self.button_group_scale.buttonClicked.connect(self.on_rb_scale_changed)

        # set from settings
        self._setScale(checkScale)

        pass
        
    # >>>>>>>>>>> функции инициализации вкладок

    def _setScale(self, idScale: int) -> None:
        """
        Установить, как checked scale
        Attention! NOT checked enabled!!!
        """
        button = self.button_group_scale.button(idScale)
        button.setChecked(True)
        self.on_rb_scale_changed(button)

    def _isExistsOpenProject(self) -> bool:
        """
        Проверить наличие открытого/активного сохранённого проекта
        """
        project = QgsProject.instance()
        if not project.fileName():
            # Сообщение - что надо, чтобы был открыт проект.
            self.iface.messageBar().pushMessage(
                    self.tr('Open/create any qgis project and reopen Carindb.'),   # noqa
                    Qgis.Warning, 3)
            return False
        return True

    def _getRootGroup(self) -> QgsLayerTreeGroup:
        """
        Возвращает QgsLayerTreeGroup текущего файла vdo
        """
        # Access the main root of the QGIS layer tree
        root = QgsProject.instance().layerTreeRoot()
        # If root_group_name doesn't exist, create it
        if not (root_group := root.findGroup(self.vdo.QGISvdoGroupName)):
            root_group = root.insertGroup(0, self.vdo.QGISvdoGroupName)
        return root_group

    def _getLayer(self, scaleId: int, layerName: str, layerType: str) -> QgsVectorLayer:
        """
        Находит или создаёт слой с именем layerName в scale scaleId
        Args:
            scaleId: int - номер scale [0..11]
            layerName: str наименование слоя
            layerType: str Тип геометрии [Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon]  # noqa
        Returns:
            layer: QgsVectorLayer
        """
        # группа /root_group/scale_X
        gr_name = SCALE_GROUP_NAME_PREFIX + str(scaleId)
        if not (scaleGroup := self._getRootGroup().findGroup(gr_name)):
            # какого хера то?
            raise ValueError(f"Нет группы {gr_name}")
        del gr_name
        # В группе ищем слой
        for child in scaleGroup.children():
            # Проверяем, что дочерний элемент — это слой и его имя совпадает
            if isinstance(child, QgsLayerTreeLayer) and child.name() == layerName:
                layer = child.layer()
                # Убеждаемся, что это векторный слой
                if isinstance(layer, QgsVectorLayer):
                    return layer
                else:
                    raise ValueError(f"Что не так с {layer.name()}")

        # <<< Слой не найден. Создаём новый.
        # для начала самое время проверить валидность типа
        if layerType not in ['Point', 'LineString', 'Polygon', 'MultiPoint',
                             'MultiLineString', 'MultiPolygon']:
            raise ValueError(f"Тип геометрии слоя {layerType} вне валидных ['Point', 'LineString', 'Polygon', 'MultiPoint', 'MultiLineString', 'MultiPolygon']")  # noqa
        # Настраиваем параметры нового слоя в памяти (Memory Layer)
        layer = QgsVectorLayer(f"{layerType}?crs=EPSG:4326", layerName, "memory")

        # Добавляем атрибутивные поля (колонки) в таблицу нового слоя
        provider = layer.dataProvider()
        provider.addAttributes([
            # QgsField("id", QMetaType.Type.Int),            # noqa 
            QgsField("name", QMetaType.Type.QString)      # noqa
            # QgsField("value", QMetaType.Type.QString)      # noqa Double
        ])
        # Обновляем поля в слое после их добавления в провайдер
        layer.updateFields()

        # получаем рендерер - свойства отображения слоя
        renderer = getRendererByLayerName(layerName)
        layer.setRenderer(renderer)
        del renderer
        # Обновляем отображение слоя
        layer.triggerRepaint()
        # Проверяем валидность и добавляем слой в нашу верхнюю группу
        if layer.isValid():
            # Регистрируем в проекте без автоматического отображения в панели (False)  # noqa
            QgsProject.instance().addMapLayer(layer, False) # noqa
            # Вставляем слой на последнее место внутри нашей новой группы
            scaleGroup.insertLayer(0, layer)
            # print("Новый слой успешно создан в памяти и добавлен наверх!")
            return layer
        else:
            print("Не удалось создать новый слой.")
            pass

    def _getRootAreaLayer(self) -> QgsVectorLayer:
        """
        возвращает слой NAME_LAYER_GLOBAL_BOUNDS в корневой рабочей группе
        """
        layer_name = NAME_LAYER_GLOBAL_BOUNDS
        root_group = self._getRootGroup()
        #  существует ли уже слой с таким именем в прямых потомках root группы
        for child in root_group.children():
            # Проверяем, что это узел слоя (а не подгруппа) и имя совпадает
            if child.nodeType() == child.NodeLayer and child.name() == layer_name:
                # Получаем сам объект слоя, он нужен для работы
                layer = child.layer()
                return layer

        # нет, слой с таким именем не найден - создаём его в root
        # Настраиваем параметры нового слоя в памяти (Memory Layer)
        # Формат: "ТипГеометрии?crs=EPSG:Код"  EPSG:4326 grad    EPSG:3395 - meters
        # Доступные типы: Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon  # noqa
        geometry_type = "Polygon?crs=EPSG:4326"
        layer = QgsVectorLayer(geometry_type, layer_name, "memory")
        del geometry_type

        # Добавляем атрибутивные поля (колонки) в таблицу нового слоя
        provider = layer.dataProvider()
        # provider.addAttributes([
        #     # QgsField("id", QMetaType.Type.Int),            # noqa 
        #     QgsField("name", QMetaType.Type.QString)      # noqa
        #     # QgsField("value", QMetaType.Type.QString)      # noqa Double
        # ])
        provider.addAttributes([QgsField("name", QMetaType.Type.QString)])
        # Обновляем поля в слое после их добавления в провайдер
        layer.updateFields()

        # получаем рендерер - свойства отображения слоя
        renderer = getRendererByLayerName(NAME_LAYER_GLOBAL_BOUNDS)
        layer.setRenderer(renderer)
        del renderer
        # Обновляем отображение слоя
        layer.triggerRepaint()
        # Проверяем валидность и добавляем слой в нашу верхнюю группу
        if layer.isValid():
            # Регистрируем в проекте без автоматического отображения в панели (False)  # noqa
            QgsProject.instance().addMapLayer(layer, False) # noqa
            
            # Вставляем слой на последнее место внутри нашей новой группы
            root_group.insertLayer(-1, layer)
            # print("Новый слой успешно создан в памяти и добавлен наверх!")
            return layer
        else:
            print("Не удалось создать новый слой.")
            pass

    def _restoreGroupBoxVisibility(self) -> None:
        """
        Восстанавливает ранее сохранённые настройки
        свёрнутых/развёрнутых groupBoxCollapsible
        """
        for gb in listGBC:
            state = Settings.ShowGroupBoxEnabled(gb)
            widget = self.findChild(AnimatedGroupBox, gb)
            if widget is not None:
                widget.toggle_state(state)

    # <<<<<<<<<< работа с эвентами

    def on_rb_scale_changed(self, button) -> None:
        """
        Triggered when any radio button in the group scale is clicked/changed
        """
        idScale = self.button_group_scale.id(button)
        # сохраняем номер масштаба в settings
        Settings.setChousedScale(idScale)
        # отрисовать area альманаха
        self.DrawAlmanacArea(idScale)

        # Отключить видимость для всех групп
        # root group - vdo
        root_gr = self._getRootGroup()
        for id in range(QTY_ALL_SCALES):
            gr_name = SCALE_GROUP_NAME_PREFIX + str(id)
            if gr := root_gr.findGroup(gr_name):
                gr.setItemVisibilityChecked(id == idScale)

        # что то делаем
        print(f"Selected: {button.text()} (ID: {self.button_group_scale.id(button)})")

    def closeEvent(self, event):
        # self.closingPlugin.emit()
        # event.accept()
        pass

    def pbActionEvent(self, event):
        # action для кнопки
        pass

    # >>>>>>>>>>>>>> работа с эвентами
