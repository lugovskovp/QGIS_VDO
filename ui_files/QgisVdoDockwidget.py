"""
Основной dockedWidget
feat: tabTopo_DrawAlmanacArea еще и maps при создании рисует
"""

import os
import re
from typing import cast

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (QRadioButton, QButtonGroup,
                                 QPushButton, QMessageBox, QCheckBox)
from qgis.core import (Qgis, QgsProject, QgsVectorLayer, QgsLayerTreeLayer,
                       QgsLayerTreeGroup, QgsCoordinateTransform, QgsFeatureRequest
                       )
from qgis.PyQt.QtCore import QCoreApplication


from QGIS_VDO.vdo_threading import FolderMapProcessingWorker, PaintMapsProcessingWorker
from QGIS_VDO.settings import Settings, DEFAULT_SCALE
from QGIS_VDO.vdo import VDO_FILE, COORD, BLADDR
from QGIS_VDO.vdo.consts import PATH_ICON
from QGIS_VDO.vdo.blocks import (
    block_0x12,
    block_0x13,
    block_0x07,
    block_0x08,
    block_0x09,
)
from QGIS_VDO.vdo.blocks.block_0x07 import SCALE

from QGIS_VDO.vdo import (
    NAME_LAYER_GLOBAL_BOUNDS,
    NAME_LAYER_ALMANACS,
    NAME_LAYER_SHAPES,
    NAME_LAYER_LINES,
    NAME_LAYER_POI,
)

from QGIS_VDO.ui_files import (
    AnimatedGroupBox,
    ClickCoordinatesTool,
    _DrawRectangleArea,
    _DrawPacketAreas,
    DrawPacketShapes,
    DrawPacketLines,
    DrawPacketPOIs,
)
from QGIS_VDO.ui_files.drawing import getCrsProjection, getLayer


# CRS_PROJECTION = "EPSG:4326"   # классическая проекция EPSG:4326 grad    EPSG:3395 - meters

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
BLOCKTYPEX_SCALEID = {
    "06" : 1,
    "01" : 2,
    "02" : 3,
    "03" : 4,
    "14" : 5,
    "15" : 6,
    "16" : 7,
    "1C" : 9,
    "1D" : 10,
    "1E" : 11
}

# Порядок групп в rootGroup сверху вниз: POIs -> Scale 0-5 -> Routes 0-3
# Единая конфигурация для всех scale-групп
GROUP_CONFIG = {
    0: {'name': 'Routes 0', 'category': 'routes', 'sort_num': 0},
    1: {'name': 'POIs', 'category': 'poi', 'sort_num': 1},
    2: {'name': 'Routes 3', 'category': 'routes', 'sort_num': 3},
    3: {'name': 'Routes 2', 'category': 'routes', 'sort_num': 2},
    4: {'name': 'Routes 1', 'category': 'routes', 'sort_num': 1},
    5: {'name': 'Scale 3', 'category': 'scale', 'sort_num': 3},
    6: {'name': 'Scale 1', 'category': 'scale', 'sort_num': 1},
    7: {'name': 'Scale 0', 'category': 'scale', 'sort_num': 0},
    8: {'name': 'Empty', 'category': 'empty', 'sort_num': 8},
    9: {'name': 'Scale 2', 'category': 'scale', 'sort_num': 2},
    10: {'name': 'Scale 4', 'category': 'scale', 'sort_num': 4},
    11: {'name': 'Scale 5', 'category': 'scale', 'sort_num': 5},
}

# Порядок категорий в rootGroup сверху вниз: POIs -> Scale 0-5 -> Routes 0-3
CATEGORY_ORDER = ['poi', 'scale', 'routes']

# Сообщения
MSG_NO_AREAS = 'Where are no Area_A, Area_B in this Carindb.'

# Типы блоков
GEO_BLOCK_TYPES = {0x14, 0x15, 0x16, 0x1C, 0x1D, 0x1E}
GEO_OR_POI_BLOCK_TYPES = GEO_BLOCK_TYPES | {0x06}
MAP_SCALE_IDS = {1, 5, 6, 7, 9, 10, 11}


def _get_group_name(scaleId: int) -> str:
    """Возвращает название группы по scaleId."""
    return GROUP_CONFIG[scaleId]['name']


def _get_group_category(scaleId: int) -> str:
    """Возвращает категорию группы по scaleId."""
    return GROUP_CONFIG[scaleId]['category']


def _get_group_sort_num(scaleId: int) -> int:
    """Возвращает номер сортировки группы по scaleId."""
    return GROUP_CONFIG[scaleId]['sort_num']


class QgisVdoDockwidget(QtWidgets.QDockWidget, FORM_CLASS):  # type: ignore
    """
    Главный рабочий виджет для отображения выбранного carindb
    """
    vdo: VDO_FILE

    def _setupIcons(self) -> None:
        """Загрузить SVG-иконки для кнопок."""
        icon_zoom = QIcon(os.path.join(PATH_ICON, 'zoom_to_rect.svg'))
        icon_help = QIcon(os.path.join(PATH_ICON, 'help.svg'))

        if hasattr(self, 'pb_Country_center'):
            self.pb_Country_center.setIcon(icon_zoom)
        if hasattr(self, 'pb_Country_i'):
            self.pb_Country_i.setIcon(icon_help)

    def __init__(self, parent_plugin, iface, parent=None):
        """Constructor."""
        super(QgisVdoDockwidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # widgets-and-dialogs-with-auto-connect
        self.iface = iface
        # отрисовать
        self.setupUi(self)

        # Иконки (qrc убран из UI-файла, задаём в коде)
        self._setupIcons()

        # Проверить наличие открытого/активного сохранённого проекта
        if not self._isExistsOpenProject():
            return

        # Восстановить из настроек видимость groupBoxes
        self._restoreGroupBoxVisibility()

        # vdo
        self.vdo = parent_plugin.vdo
        if not self.vdo.is_empty:
            # >>> tab_info
            self._initTabInfo()

            # >>> tab_addr
            self._initTabAddr()

            # >>> tab_topo
            self._initTabTopo()

            # >>> tab_topo
            self._initTabBlock()

            # привязать pb_Action
            # self.pb_Action.clicked.connect(self.pbActionEvent)
            # ----------------------------------------------
            pass
        else:   # if self.vdo.is_empty:
            # TODO: vdo None -> make unactive groupbox?
            pass
        # DEBUG привязать pb_DebugClearVDO
        self.pb_DebugClearVDO.clicked.connect(self.pb_DebugClearVDOevent)

        pass    # def __init__(self, parent_plugin, iface, parent=None):

    def tr(self, message: str) -> str:
        """Translate a string."""
        return QCoreApplication.translate('VDOExplorerPlugin', message)

    def tabInfo_DrawTocAreas(self):
        """
        Отображает на карте area_A, area_B
        Скрывает и сворачивает остальные toc группы
        """
        # Проверить наличие открытого/активного сохранённого проекта
        if not self._isExistsOpenProject():
            return
        project: QgsProject = QgsProject.instance()
        if project is None:
            return

        # получаем корневой ТОС area layer в группе
        layer = getLayer(self._getRootGroup(), NAME_LAYER_GLOBAL_BOUNDS)

        # Скрываем другие vdo-группы при переключении файла
        root_group = self._getRootGroup()
        self._hide_other_vdo_groups(root_group)

        # hide all another vdo root groups but root_group_name
        self.iface.setActiveLayer(layer)
        root = project.layerTreeRoot()
        if root is None:
            return
        root_group = root.findGroup(self.vdo.QGISvdoGroupName)
        if root_group is None:
            return
        root_group.setItemVisibilityChecked(True)
        root_group.setExpanded(True)

        # Is dbrev old? no areas, show warning
        if self.vdo.dbrev != 34:
            self.iface.messageBar().pushMessage(
                self.tr(MSG_NO_AREAS),
                Qgis.Warning, 3)
            return

        # Отрисовка Areas и зум
        self._draw_areas_and_zoom(root_group, layer)

    def tabTopo_DrawAlmanacArea(self, idScale: int) -> None:
        """
        Добавляет слой Almanac, если не было его ранее
        отрисовывает валидные альманахи
        """
        # Проверить наличие открытого/активного сохранённого проекта
        if not self._isExistsOpenProject():
            return

        # Получить слой для альманаха
        layer = self._getScaleLayer(idScale, NAME_LAYER_ALMANACS)
        
        # Получить альманах и отрисовать содержимое - folder maps
        sc: SCALE = self.scales[idScale]
        bl_almanac: block_0x08 = self.vdo.get_block(sc.almanac_idx, sc.area[0], sc.area[1])   # noqa
        for (bladdr_fldr_val, coord_lb, coord_rt) in bl_almanac.get_items():  # noqa
            # при отрисовке поле name уникальное - второй раз не отрисовывается
            area = [(coord_lb.lat, coord_lb.lon),
                    (coord_rt.lat, coord_rt.lon)]  # noqa
            _DrawRectangleArea(area, f"0x{bladdr_fldr_val:X}", layer, "layout")  # noqa
            pass
        self.pb_LoadFolderMaps.setText(self.tr("Load {} layouts".format(bl_almanac.items_cnt())))   # noqa
        pass

    # <<<<<<<<<<<<< функции инициализации вкладок
           
    def _initTabInfo(self) -> None:
        """
        Инициализация вкладки Info
        """
        # path above overall info
        # ap = self.vdo.file_path.split("/")
        # actionName = ap[-2] + ":::" + ap[-1]
        # del ap
        ap = self.vdo.file_path.split("/")
        actionName = ap[-2] + ":::" + self.vdo.filename
        del ap
        self.groupBox_0veral.setTitle(actionName)
        # overall info
        self.l_vdo_dbrev_val.setText(f"0x{self.vdo.dbrev:02X} / {self.vdo.dbrev}")
        self.l_vdo_segsize_val.setText(f"0x{self.vdo.segsize:03X} / {self.vdo.segsize}")  # noqa
        formatted = f"{self.vdo.file_size:,}".replace(',', ' ')
        self.l_vdo_size_val.setText(f"0x{self.vdo.file_size:04X} / {formatted}")
        self.l_vdo_path_val.setText(self.vdo.file_path)
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

            # отрисовать области покрытия
            self.tabInfo_DrawTocAreas()
        # bl_13
        self.textBrowser_label.setPlainText(bl_bibliogr.str_label)
        self.textBrowser_descr.setPlainText(bl_bibliogr.str_description)
        self.textBrowser_info.setPlainText(bl_bibliogr.str_information)

    def _initTabAddr(self) -> None:
        """
        Инициализация вкладки Address
        
        """

        pass

    def _initTabTopo(self) -> None:
        """
        Инициализация вкладки Topo
        Собрать scale radioButtons в QButtonGroup
        (к моменту вызова _restoreScale список масштабов уже есть)
        """
        # Восстановить из настроек ранее установленный scale
        check_scale = Settings.ChousedScale()
        if self.scales[check_scale].is_empty:
            check_scale = DEFAULT_SCALE
        if self.scales[check_scale].is_empty:
            for i in range(QTY_ALL_SCALES):
                if not self.scales[i].is_empty:
                    check_scale = i
                    break
        # root group - vdo
        # root = self._getRootGroup()
        # Создаем ОБЩУЮ группу для всех радиокнопок масштабов
        self.button_group_scale = QButtonGroup(self)
        # добавляем в группу все кнопки rb_scale_[0..11]
        for scale_id in range(QTY_ALL_SCALES):
            rb_name = RB_SCALE_OBJNAME_PREFIX + str(scale_id)
            rb = self.tabWidget.findChild(QRadioButton, rb_name)
            # Изменить подпись: номер scale, value_a, масштаб от и до
            sc: SCALE = self.scales[scale_id]
            # rb.setText("{}  {}: {} - {}".format(scale_id, sc.value_a, sc.zoom_from, sc.zoom_to))  # noqa
            rb.setText("{}  {}: {} - {}".format(scale_id, _get_group_name(scale_id), sc.zoom_from, sc.zoom_to))  # noqa
            # Установить enabled|disabled
            rb.setEnabled(not sc.is_empty)
            # TODO: а не излишне ли?
            # параллельно с rb создаём группы масштабов для отображения.
            # УПД - не создаём, issue 85
            # if not sc.is_empty:
            #     gr_name = SCALE_GROUP_NAME_PREFIX + str(scale_id)
            #     if not (root.findGroup(gr_name)):
            #         root.insertGroup(-2, gr_name)
            # добавляем в группу rb
            self.button_group_scale.addButton(rb, scale_id)
            pass

        # Connect the change signal button_group_scale
        self.button_group_scale.buttonClicked.connect(self.on_rb_scale_changed)

        # Progress bar
        self.progressBarFolderMaps.setValue(0)
        self.pb_LoadFolderMaps.clicked.connect(self.start_loading_folders)

        # set from settings
        self._setScale(check_scale)

        pass

    # <<<< init tab Block

    def _initTabBlock(self) -> None:
        """
        Инициализация вкладки Block
        """
        # Привязываем вызов activate_coords_tool к кнопке
        self.pb_getCoordinates: QPushButton
        self.pb_loadBlock: QPushButton
        self.pb_getCoordinates.setCheckable(True)
        self.pb_getCoordinates.clicked.connect(self.tabBlock_activate_coords_tool)
        self.pb_loadBlock.clicked.connect(self.tabBlock_load_block)
        self.cb_LoadFolder : QCheckBox
        self.cb_LoadFolder.stateChanged.connect(self.tabBlock_cb_LoadFolder_changed)

    def tabBlock_cb_LoadFolder_changed(self) -> None:
        """Вызывается при изменении чекбокса cb_LoadFolder."""
        self.pb_loadBlock.setEnabled(not self.cb_LoadFolder.isChecked())
        if self.cb_LoadFolder.isChecked():
            self.pb_getCoordinates.setText(self.tr("Get and load FOLDER"))
        else:
            self.pb_getCoordinates.setText(self.tr("Get block"))

    def tabBlock_activate_coords_tool(self, checked):
        # сбросить показания прогресс бара
        self.progressBarLoadMapFromFolder.setValue(0)
        # Делаем кнопку активной визуально
        self.pb_loadBlock.setEnabled(False)
        self.cb_LoadFolder.setEnabled(False)
        # self.pb_getCoordinates.setChecked(True)
        if checked:
            # Создаем и устанавливаем инструмент
            self.tool = ClickCoordinatesTool(
                self.iface.mapCanvas(),
                self.tabBlock_on_coords_received,
                self.tabBlock_on_tool_deactivated
            )
            self.iface.mapCanvas().setMapTool(self.tool)
        else:
            # Выключаем инструмент, если кнопка была отжата пользователем
            current_tool = self.iface.mapCanvas().mapTool()
            # Делаем кнопку активной визуально
            self.pb_loadBlock.setEnabled(True)
            self.cb_LoadFolder.setEnabled(True)
            if hasattr(self, 'tool') and current_tool == self.tool:
                self.iface.mapCanvas().unsetMapTool(self.tool)

    def tabBlock_load_block(self):
        #
        bladdr = self.le_bladdr.text()
        if not bladdr:
            # пустое поле адреса блока
            return
        
        # bladdr = self.vdo.get_bladdr(int(bladdr, 16))
        block = self.vdo.get_block(self.vdo.get_bladdr(int(bladdr, 16)))
        if block is None:
            blockInfo = self.tr("Not valid block number")
            self.l_loadBlockInfo.setText(blockInfo)
            return
        else:
            blockInfo = f"{block.head}"
        self.l_loadBlockInfo.setText(blockInfo)

        if block.type not in GEO_OR_POI_BLOCK_TYPES:
            # 1-0x06, 2-0x01, 3-0x02, 4-0x03
            # загружать ТОЛЬКО географические блоки:    5-0x14 6-0x15 7-0x16   9-0x1c 10-1d, 11-1e
            # и 06 - spatial POIs
            return
        
        # определяем масштаб
        targetScale = BLOCKTYPEX_SCALEID[f"{block.type:02X}"]
        # слой по соответствию типа block, а не текущий
        scale_group = self._getScaleGroup(targetScale)
        if targetScale == 1:     # sc1 -> block 06 - spatial index POI
            layer_poi = getLayer(scale_group, NAME_LAYER_POI)
            pois = list(block.get_all_items_extended())
            DrawPacketPOIs(pois, layer_poi)
            # del layer_poi
            
        elif targetScale in MAP_SCALE_IDS:  # 5, 6, 7, 9, 10, 11
            layer_lines = getLayer(self._getScaleGroup(targetScale), NAME_LAYER_LINES)
            lines = [lin for lin in block.getObjects(isGetShapes=False)]
            DrawPacketLines(lines, layer_lines)

            layer_shape = getLayer(scale_group, NAME_LAYER_SHAPES)
            shapes = [shp for shp in block.getObjects(isGetLines=False)]
            DrawPacketShapes(shapes, layer_shape)

            # debug
            # objs = shapes + lines
            # for obj in objs:
            #     pass   # print(obj)

        # print(layer_shape)
        pass

    def paint_topo_objects(self, list_shp: list, list_lines: list):
        """
        Пакетная загрузка блоков карт фолдера
        list_shp    :list[GEO_SHAPES]
        list_lines  :list[GEO_LINES]
        """
        # ВАЖНО: Отключаем автоперерисовку холста QGIS на время добавления пачки,
        # чтобы QGIS не пытался перерисовывать карту на каждый чих.
        canvas = self.iface.mapCanvas()
        canvas.setRenderFlag(False)

        try:
            DrawPacketShapes(list_shp, self.curr_layer_shape)
            DrawPacketLines(list_lines, self.curr_layer_lines)
        finally:
            # Включаем отрисовку обратно
            canvas.setRenderFlag(True)
            canvas.refresh()  # Перерисовываем один раз за всю пачку

        # Сигнализируем потоку, что мы готовы к следующей порции данных
        self.thread.resume_processing()
        pass

    def tabBlock_on_coords_received(self, point):
        # Вывод координат в консоль
        # print(f"Координаты: X = {point.x():.4f}, Y = {point.y():.4f}")
        # Получаем текущую систему координат проекта
        project_crs = QgsProject.instance().crs()
        # Задаем целевую систему координат (модифицированную WGS 84)
        target_crs = getCrsProjection()
        # Создаем трансформатор координат
        transform = QgsCoordinateTransform(project_crs, target_crs, QgsProject.instance())  # noqa
        # Трансформируем точку клика
        transformed_point = transform.transform(point)
        # Из EPSG:4326 X — это долгота (Longitude), Y — широта (Latitude)
        lon = transformed_point.x()
        lat = transformed_point.y()
        srch_coord = COORD(lon, lat)
        # print(f"WGS 84 (EPSG:4326) -> Долгота (X): {lon:.6f}, Широта (Y): {lat:.6f}")
        self.l_lastSelectedCoords.setText(f"{srch_coord}")

        # Получаем номер блока с картой по srch_coord и текущему масштабу
        sc: SCALE = self.scales[self.currentIdScale]
        if srch_coord.lat < sc.area[0].lat or srch_coord.lat > sc.area[1].lat \
           or srch_coord.lon < sc.area[0].lon or srch_coord.lon > sc.area[1].lon:
            # не попал в квадрат lb-rt scale
            print(f"No way: {srch_coord} not in {sc.area}")
            return

        # ищем блок или фолдер
        isFindBlock = not self.cb_LoadFolder.isChecked()

        # в масштабе ищем имя блока или none
        bladdr_map: BLADDR = sc.find_by_coord(srch_coord, isFindBlock)
        # запишем в поле le_bladdr
        if bladdr_map is None:
            QMessageBox.warning(
                self, self.tr('Attention!'), self.tr('Finded nothing.'), QMessageBox.Ok)
        else:
            # грузим фолдер
            if not isFindBlock:
                # thread:
                self.le_bladdr.setText(f"0x{bladdr_map.head.bladdr.value:X}")
                self.start_loading_maps_in_folder(bladdr_map)       # threading
            else:
                self.le_bladdr.setText(f"0x{bladdr_map.value:X}")
                # и сразу загружаем блок
                self.tabBlock_load_block()
        pass

    def tabBlock_on_tool_deactivated(self):
        try:
            self.pb_getCoordinates.blockSignals(True)
            self.pb_getCoordinates.setChecked(False)
        finally:
            self.pb_getCoordinates.blockSignals(False)
        # Делаем кнопку активной визуально
        self.pb_loadBlock.setEnabled(not self.cb_LoadFolder.isChecked())
        self.cb_LoadFolder.setEnabled(True)

    # >>> initTabBlock

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
            # Сообщение - надо, чтобы был открыт проект.
            self.iface.messageBar().pushMessage(
                self.tr('Open/create any QGIS project and reopen Carindb.'), Qgis.Warning, 3)
            return False
        return True

    def _getRootGroup(self) -> QgsLayerTreeGroup:
        """
        Возвращает QgsLayerTreeGroup текущего файла vdo,
        создавая его при необходимости.
        """
        # Access the main root of the QGIS layer tree
        root_group = QgsProject.instance().layerTreeRoot().findGroup(self.vdo.QGISvdoGroupName)
        if root_group:
            return root_group

        root_group = self._ensure_root_group()
        if root_group is None:
            return root_group

        # И добавить слой bounds
        layer = getLayer(root_group, NAME_LAYER_GLOBAL_BOUNDS)
        self.iface.setActiveLayer(layer)

        # по значению настроек - скрываем все другие группы vdo
        self._hide_other_vdo_groups(root_group)

        # Is dbrev old? no areas, show warning
        if self.vdo.dbrev != 34:
            self.iface.messageBar().pushMessage(
                self.tr(MSG_NO_AREAS),
                Qgis.Warning, 3)
            return root_group

        # Areas from TOC block
        self._draw_areas_and_zoom(root_group, layer)

        return root_group

    def _ensure_root_group(self) -> QgsLayerTreeGroup | None:
        """Создаёт корневую группу VDO, если она не существует."""
        project: QgsProject = QgsProject.instance()
        if project is None:
            return None
        root_group = project.layerTreeRoot().insertGroup(0, self.vdo.QGISvdoGroupName)
        curr_group = QgsProject.instance().layerTreeRoot().findGroup(self.vdo.QGISvdoGroupName)
        if curr_group is None:
            return None
        curr_group.setItemVisibilityChecked(True)
        curr_group.setExpanded(True)
        return root_group

    def _hide_other_vdo_groups(self, root_group: QgsLayerTreeGroup) -> None:
        """Скрывает другие vdo-группы по regex, если включена настройка."""
        if not Settings.HideNonActiveVdoEnabled():
            return
        pattern = r"_0x[0-9a-f]{4,}$"
        regex = re.compile(pattern, re.IGNORECASE)
        for child in QgsProject.instance().layerTreeRoot().children():
            if isinstance(child, QgsLayerTreeGroup):
                if child.name() != root_group.name():
                    if regex.search(child.name()):
                        child.setItemVisibilityChecked(False)
                        child.setExpanded(False)

    def _draw_areas_and_zoom(self, root_group: QgsLayerTreeGroup, layer: QgsVectorLayer) -> None:
        """Отрисовка Areas и зум карты по их границам."""
        # Areas from TOC block
        bl_toc: block_0x12 = cast("block_0x12", self.vdo.get_block(0))
        area = [(bl_toc.area_B[0].lat, bl_toc.area_B[0].lon), (bl_toc.area_B[1].lat, bl_toc.area_B[1].lon)]
        _DrawRectangleArea(area, "Area_B", layer)
        area = [(bl_toc.area_A[0].lat, bl_toc.area_A[0].lon), (bl_toc.area_A[1].lat, bl_toc.area_A[1].lon)]
        _DrawRectangleArea(area, "Area_A", layer)

        # Масштаб по границам слоя
        canvas = self.iface.mapCanvas()
        project = QgsProject.instance()
        transform = QgsCoordinateTransform(layer.crs(), project.crs(), project)
        layer_extent = layer.extent()
        layer_extent.scale(1.2)
        project_extent = transform.transformBoundingBox(layer_extent)
        canvas.setExtent(project_extent)
        canvas.refresh()

    def _getScaleGroup(self, scaleId: int) -> QgsLayerTreeGroup | None:
        """
        Возвращает существующую группу scale,
        найдя её в rootGroup, либо создав.
        None при выходе за границы.
        """
        # проверка номера - должен быть среди self.scales
        if not (0 <= scaleId < len(self.scales)):
            # номера слоёв 0..11
            return None
        #
        # если пустая scale - создавать группу не надо
        if self.scales[scaleId].is_empty:
            return None
        #
        scaleGroup: QgsLayerTreeGroup
        rootGroup = self._getRootGroup()
        # поиск в существующих
        scaleGroup = rootGroup.findGroup(_get_group_name(scaleId))
        if scaleGroup:
            return scaleGroup
        #----------------------------------------------------------------------
        # такой не найдено - надо её создать лениво
        insert_index = self._find_insert_index_for_category(rootGroup, scaleId)

        # вставляем
        scaleGroup = rootGroup.insertGroup(insert_index, _get_group_name(scaleId))
        self.tabTopo_DrawAlmanacArea(scaleId)
        return scaleGroup

    def _getScaleLayer(self, scaleId: int, layerName: str) -> QgsVectorLayer:
        """
        Находит или создаёт слой с именем layerName в scale группе scaleId.
        Args:
            scaleId: int - номер scale [0..11]
            layerName: str наименование слоя
        Returns:
            layer: QgsVectorLayer
        """
        if not (scaleGroup := self._getScaleGroup(scaleId)):
            raise ValueError(f"Нет группы '{_get_group_name(scaleId)}' для scale {scaleId}")

        return getLayer(scaleGroup, layerName)

    def _find_insert_index_for_category(self, rootGroup: QgsLayerTreeGroup, scaleId: int) -> int:
        """
        Находит индекс для вставки группы с учётом категории и сортировки.
        Порядок: poi -> scale -> routes -> bounds-слой
        Внутри категории — по возрастанию sort_num из GROUP_CONFIG.
        """
        # Ищем bounds-слой — все группы вставляются перед ним
        bounds_index = self._find_bounds_layer_index(rootGroup)

        # Ищем позицию внутри категории (сортировка по sort_num)
        target_index = self._find_insert_index_within_category(rootGroup, scaleId)

        # Ограничиваем bounds-слоем
        return min(target_index, bounds_index)

    def _find_bounds_layer_index(self, rootGroup: QgsLayerTreeGroup) -> int:
        """Находит индекс bounds-слоя в rootGroup."""
        for i, child in enumerate(rootGroup.children()):
            if isinstance(child, QgsLayerTreeLayer):
                layer = child.layer()
                if layer and layer.name() == NAME_LAYER_GLOBAL_BOUNDS:
                    return i
        return len(rootGroup.children())

    def _find_insert_index_within_category(self, rootGroup: QgsLayerTreeGroup, scaleId: int) -> int:
        """
        Находит позицию вставки внутри категории с сортировкой по sort_num.
        Возвращает индекс, куда вставить новую группу.
        """
        category = GROUP_CONFIG[scaleId]['category']

        # Собираем все существующие группы этой категории с их sort_num
        category_groups = self._get_category_groups(rootGroup, category)

        # Если групп этой категории ещё нет — ищем позицию после последней группы предыдущей категории
        if not category_groups:
            return self._find_first_index_in_category(rootGroup, category)

        # Сортируем существующие группы по sort_num
        category_groups.sort(key=lambda x: x[0])

        # Ищем позицию для вставки: между группами с меньшим и большим sort_num
        return self._find_insert_position_in_sorted_list(category_groups, scaleId)

    def _get_category_groups(self, rootGroup: QgsLayerTreeGroup, category: str) -> list:
        """Возвращает список (sort_num, index) для всех групп данной категории."""
        result = []
        for i, child in enumerate(rootGroup.children()):
            if isinstance(child, QgsLayerTreeGroup):
                child_name = child.name()
                for sid in GROUP_CONFIG:
                    if child_name == GROUP_CONFIG[sid]['name'] and sid < len(GROUP_CONFIG):
                        if GROUP_CONFIG[sid]['category'] == category:
                            result.append((GROUP_CONFIG[sid]['sort_num'], i))
                            break
        return result

    def _find_first_index_in_category(self, rootGroup: QgsLayerTreeGroup, category: str) -> int:
        """Находит индекс для первой группы в категории."""
        prev_category_idx = CATEGORY_ORDER.index(category) - 1
        if prev_category_idx < 0:
            return 0

        prev_category = CATEGORY_ORDER[prev_category_idx]
        last_prev_index = self._find_last_group_index_by_category(rootGroup, prev_category)

        if last_prev_index >= 0:
            return last_prev_index + 1
        return 0

    def _find_last_group_index_by_category(self, rootGroup: QgsLayerTreeGroup, category: str) -> int:
        """Находит индекс последней группы данной категории."""
        last_index = -1
        for i, child in enumerate(rootGroup.children()):
            if isinstance(child, QgsLayerTreeGroup):
                child_name = child.name()
                for sid in GROUP_CONFIG:
                    if child_name == GROUP_CONFIG[sid]['name'] and sid < len(GROUP_CONFIG):
                        if GROUP_CONFIG[sid]['category'] == category:
                            last_index = i
                        break
        return last_index

    def _find_insert_position_in_sorted_list(self, sorted_groups: list, scaleId: int) -> int:
        """
        Находит позицию вставки в отсортированный список (sort_num, index).
        Возвращает индекс в rootGroup, куда вставить группу.
        """
        new_sort_num = GROUP_CONFIG[scaleId]['sort_num']

        for existing_sort_num, existing_index in sorted_groups:
            if new_sort_num < existing_sort_num:
                return existing_index

        # new_sort_num > всех существующих — вставляем в конец
        last_sort_num, last_index = sorted_groups[-1]
        if new_sort_num > last_sort_num:
            return last_index + 1

        # new_sort_num уже существует — возвращаем его индекс
        return last_index

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

    # ------ фоновая загрузка контуров на tabTopo <<<<<<<<<<<<

    def start_loading_folders(self):
        """
        Load folders with maps on tabTopo
        """
        # Блокируем кнопку от повторного нажатия
        self.pb_LoadFolderMaps.setEnabled(False)
        
        # Список для хранения кнопок, которые УЖЕ БЫЛИ отключены
        self.disabled_buttons = []
        # Блокируем группу, запоминая изначально выключенные кнопки
        for button in self.button_group_scale.buttons():
            if not button.isEnabled():
                # Если кнопка уже была disabled, запоминаем её
                self.disabled_buttons.append(button)
            else:
                # Если кнопка была активна — выключаем её на время загрузки
                button.setEnabled(False)

        self.progressBarFolderMaps.setValue(0)

        # Получить альманах
        sc: SCALE = self.scales[self.currentIdScale]
        almanac_block: block_0x08 = self.vdo.get_block(sc.almanac_idx, sc.area[0], sc.area[1])   # noqa
        
        # Делаем слой активным в интерфейсе
        self.layer_maps = self._getScaleLayer(self.currentIdScale, NAME_LAYER_ALMANACS)
        self.iface.setActiveLayer(self.layer_maps)

        # Инициализируем поток, передав ему параметры папки
        self.thread = FolderMapProcessingWorker(self.progressBarFolderMaps, almanac_block)   # noqa

        # СВЯЗЫВАЕМ СИГНАЛЫ С РЕАЛЬНОЙ ЛОГИКОЙ ДОК-ВИДЖЕТА
        self.thread.count_signal.connect(self._set_progress_max)
        self.thread.progress_signal.connect(self._update_gui_with_result)
        self.thread.safe_drawing_map_signal.connect(self._safe_drawing_contour_map)
        self.thread.finished.connect(self.on_finished_loading_contours)
        self.thread.start()

    # РЕАЛЬНАЯ ЛОГИКА ОБРАБОТКИ КАЖДОЙ ПАПКИ КАРТ
    def _safe_drawing_contour_map(self, areas_packet: list) -> None:
        """
        Потокобезопасная отрисовка контуров карт
        """
        # # Получить слой для folder maps
        _DrawPacketAreas(areas_packet, self.layer_maps)
        # _DrawArea([point_lb, point_rt], f"0x{bl_map_val:X}", self.layer_maps)  # noqa

    def _update_gui_with_result(self, progress_bar, percent, block_folder_value):
        """
        универсальная обработка сигнала: Обновляем прогресс-бар
        """
        progress_bar.setValue(percent)
        # Например: добавление в QListWidget, отрисовка слоя, парсинг метаданных и т.д.   # noqa
        # print(f"_update_gui_with_result: Док-виджет обрабатывает карту: {block_folder_value}")

    def _set_progress_max(self, progress_bar, total_count):
        """
        универсальная обработка сигнала:
        """
        if total_count == 0:
            progress_bar.setMaximum(100)
        else:
            progress_bar.setMaximum(total_count)
    
    def on_finished_loading_contours(self):
        """
        Finish Loading folders with maps on tabTopo
        """
        self.pb_LoadFolderMaps.setEnabled(True)
        # Восстанавливаем состояние кнопок
        for button in self.button_group_scale.buttons():
            # Если кнопка есть в списке изначально отключенных — оставляем её disabled
            if button in self.disabled_buttons:
                button.setEnabled(False)
            else:
                # Все остальные кнопки делаем снова активными
                button.setEnabled(True)

    # >>>>>>>>>>>>------ фоновая загрузка контуров на tabTopo

    # # ------ фоновая загрузка топоосновы карт на tabBlock <<<<<<<<<<<<

    def start_loading_maps_in_folder(self, folder_block: block_0x09):
        """
        Load folders with maps on tabTopo by pb_getCoordinates
        """
        # self.progressBarLoadMapFromFolder.setValue(0)

        # инициализируем слои для добавления
        block = self.vdo.get_block(next(folder_block.get_valid_blocks()))
        if block.type not in GEO_BLOCK_TYPES:
            # 1-0x06, 2-0x01, 3-0x02, 4-0x03
            # загружать ТОЛЬКО географические блоки:    5-0x14 6-0x15 7-0x16   9-0x1c 10-1d, 11-1e
            return

        # Список для хранения кнопок от повторного нажатия
        self.temp_disable = []
        bt = [self.cb_LoadFolder, self.pb_getCoordinates, self.pb_loadBlock, self.le_bladdr]
        for button in bt:
            if button.isEnabled():
                self.temp_disable.append(button)
                # выключаем её на время загрузки
                button.setEnabled(False)

        # определяем масштаб
        targetScale = BLOCKTYPEX_SCALEID[f"{block.type:02X}"]
        # слой по соответствию типа block, а не текущий
        self.curr_layer_lines = getLayer(self._getScaleGroup(targetScale), NAME_LAYER_LINES)
        self.curr_layer_shape = getLayer(self._getScaleGroup(targetScale), NAME_LAYER_SHAPES)

        # Делаем слой активным в интерфейсе
        self.iface.setActiveLayer(self.curr_layer_shape)

        # Инициализируем поток, передав ему параметры папки
        self.thread = PaintMapsProcessingWorker(self.progressBarLoadMapFromFolder, folder_block)   # noqa

        # СВЯЗЫВАЕМ СИГНАЛЫ С РЕАЛЬНОЙ ЛОГИКОЙ ДОК-ВИДЖЕТА
        self.thread.count_signal.connect(self._set_progress_max)
        self.thread.progress_signal.connect(self._update_gui_with_result)
        self.thread.safe_drawing_maps_signal.connect(self.paint_topo_objects)
        self.thread.finished.connect(self.on_finished_loading_folders)
        self.thread.start()

    def on_finished_loading_folders(self):
        """
        Finish Loading maps from folder on tabBlock
        """
        # Восстанавливаем состояние кнопок
        for button in self.temp_disable:
            # Все кнопки делаем снова активными
            button.setEnabled(True)

    # >>>>>>>>>>>>------ фоновая загрузка топоосновы карт на tabBlock

    def on_rb_scale_changed(self, button) -> None:
        """
        Triggered when any radio button in the group scale is clicked/changed
        """
        scale_id = self.button_group_scale.id(button)
        if scale_id == -1 or scale_id >= len(self.scales):
            return
        self.currentIdScale = scale_id
        # сохраняем номер масштаба в settings
        Settings.setChousedScale(self.currentIdScale)

        # Получить слой для folder maps и сделать его активным
        self.layer_maps = self._getScaleLayer(self.currentIdScale, NAME_LAYER_ALMANACS)
        self.iface.setActiveLayer(self.layer_maps)

        # Отрисовать area альманаха
        self.tabTopo_DrawAlmanacArea(self.currentIdScale)

        # Проверить, есть ли уже загруженные тайлы (variant=map)
        if not self._has_map_features(self.layer_maps):
            # Если тайлов нет — запустить загрузку
            self.start_loading_folders()

        # tabBlock set l_currScaleId
        # TODO: text must get from consts scqales?
        self.l_currScaleId.setText(f"{self.currentIdScale}")

        # Отключить видимость для всех групп iface
        # root group - vdo
        root_gr = self._getRootGroup()
        for id in range(QTY_ALL_SCALES):
            # кроме POI
            if id == 1:
                continue
            gr_name = _get_group_name(id)
            if gr := root_gr.findGroup(gr_name):
                gr.setItemVisibilityChecked(id == self.currentIdScale)

        # TODO: del?
        #  что то делаем
        # print(f"Selected: {button.text()} (ID: {self.button_group_scale.id(button)})")

    def _has_map_features(self, layer: QgsVectorLayer) -> bool:
        """
        Проверяет, есть ли в слое объекты с variant='map'.
        """
        field_idx = layer.fields().indexOf('variant')
        if field_idx == -1:
            return False

        request = QgsFeatureRequest().setFilterExpression("\"variant\" = 'map'")
        for feature in layer.getFeatures(request):
            return True
        return False

    def closeEvent(self, event):
        self.tabBlock_activate_coords_tool(False)
        event.accept()
        super().closeEvent(event)

    def pbActionEvent(self, event):
        # action для кнопки
        pass

    def pb_DebugClearVDOevent(self, event):
        # TODO:DEBUG only! Удаляет текущую группу VDO из слоёв проекта.
        root = QgsProject.instance().layerTreeRoot()
        group4del = self._getRootGroup()
        for child in root.children():
            # if child.nodeType() == 0 and child.name() == 'YourGroupName':
            if child == group4del:
                root.removeChildNode(group4del)     # remove child group
                break
        return

    # >>>>>>>>>>>>>> работа с эвентами
