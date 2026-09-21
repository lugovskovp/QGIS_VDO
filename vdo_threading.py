"""
Легковесный поток для итерации по картам
"""

import time
from qgis.PyQt.QtWidgets import QProgressBar
from qgis.PyQt.QtCore import QThread, pyqtSignal

from QGIS_VDO.vdo import BLADDR  # , COORD
from QGIS_VDO.vdo.consts import struct_UINT     # noqa for tests
from QGIS_VDO.vdo.blocks import (block_0x08,
                                 block_0x09)


#   # noqa
class FolderMapProcessingWorker(QThread):
    """
    Легковесный поток для итерации по картам
    класс фонового потока для подсчета/загрузки контуров карт на tabTopo
    """
    # Сигнал передает: (индекс текущего шага в int, имя обрабатываемого файла в str)
    progress_signal = pyqtSignal(object, int, str)      # self.progressBarFolderMaps
    # сигнал счётчика
    count_signal = pyqtSignal(object, int)      #
    # Safe drawing areas packet signal
    safe_drawing_map_signal = pyqtSignal(list)

    def __init__(self, progress_bar: QProgressBar, almanac_block: block_0x08):
        super().__init__()
        self.almanac_block = almanac_block
        self.progress_bar = progress_bar
        
    def run(self):
        # Получить список из альманаха
        total_blocks = self.almanac_block.items_cnt()
        progress_bar = self.progress_bar
        self.count_signal.emit(progress_bar, total_blocks)
        if not total_blocks:
            return

        # bl_folder  block_0x09
        index = 0
        for (bla_val, origin, rt_max) in self.almanac_block.get_items():
            index += 1

            # bla = self.almanac_block.vdo.get_bladdr(bla_val)
            bla = BLADDR(struct_UINT.pack(bla_val), self.almanac_block.vdo)
            bl_folder: block_0x09 = self.almanac_block.vdo.get_block(bla, origin, rt_max)  # noqa
            #cnt_map = bl_folder.items_cnt()
            # Пакет координат
            areas_packet = []
            # (bladdr_map_val, lon_min, lat_min, lon_max, lat_max)
            for (bl_map_val, lon_min, lat_min, lon_max, lat_max) in bl_folder.get_items():
                # {"area": [(lat, lon), (lat, lon)], "name": "Имя1"}, ...
                area = {"area": [(lat_min, lon_min), (lat_max, lon_max)], "name": f"0x{bl_map_val:X}"}  # noqa
                areas_packet.append(area)
                # debug print
                # print(area)
                
            # Сигналом отправляем ВСЁ содержимое block_folder_maps
            self.safe_drawing_map_signal.emit(areas_packet)  # noqa

            # Имитация тяжелого чтения файла с диска
            # time.sleep(0.01)
            
            # Отправляем данные в главный поток DockWidget
            self.progress_signal.emit(progress_bar, index + 1, f"{bl_folder}")


TRANSMIT_QUANT = 10


class PaintMapsProcessingWorker(QThread):
    """
    Легковесный поток для итерации по картам
    класс фонового потока для подсчета/загрузки карт на tabBlock
    """
    # Сигнал передает: (progressBar, индекс текущего шага в int, имя обрабатываемого файла в str)
    progress_signal = pyqtSignal(object, int, str)      # self.progressBarLoadMapFromFolder
    count_signal = pyqtSignal(object, int)              # сигнал счётчика to progressBarLoadMapFromFolder
    safe_drawing_maps_signal = pyqtSignal(list, list)   # Safe drawing areas packet signal, shapes, lines
    gui_ready_for_next = True       # Флаг готовности главного потока принять следующую пачку

    def __init__(self, progress_bar: QProgressBar, folder_block: block_0x09):
        super().__init__()
        self.folder_block = folder_block
        self.progress_bar = progress_bar
        self.gui_ready_for_next = True
        
    def run(self):
        # Обнуление счетчика
        total_blocks = self.folder_block.li_valid.cnt
        progress_bar = self.progress_bar
        self.count_signal.emit(progress_bar, total_blocks)  # к-во блоков для отрисовки
        if not total_blocks:
            return

        # bl_folder  block_0x09
        map_blocks = [bl for bl in self.folder_block.get_valid_blocks()]

        block = self.folder_block.vdo.get_block(map_blocks[0])
        if block.type not in [0x14, 0x15, 0x16, 0x1c, 0x1d, 0x1e]:
            # 1-0x06, 2-0x01, 3-0x02, 4-0x03
            # загружать ТОЛЬКО географические блоки:    5-0x14 6-0x15 7-0x16   9-0x1c 10-1d, 11-1e
            return

        index = 0
        for i in range(0, len(map_blocks), TRANSMIT_QUANT):
            batch = map_blocks[i:i + 10]
            obj_list_shp = []
            obj_list_lin = []
            for bla in batch:
                # здесь формируем пакет объектов для отрисовки
                map: block_0x09 = self.folder_block.vdo.get_block(bla)
                obj_list_shp += [shp for shp in map.getObjects(isGetLines=False)]
                obj_list_lin += [shp for shp in map.getObjects(isGetShapes=False)]
                index += 1
                # Отправляем данные в главный поток DockWidget
                self.progress_signal.emit(progress_bar, index + 1, f"{map}")

            # # Ждем, пока главный поток обработает предыдущую пачку
            while not self.gui_ready_for_next:
                time.sleep(0.01)  # Короткая пауза, чтобы не грузить процессор

            self.gui_ready_for_next = False      # Блокируем отправку следующей, пока GUI занят
            # Отправляем пакет в QGIS
            self.safe_drawing_maps_signal.emit(obj_list_shp, obj_list_lin)

    def resume_processing(self):
        """Этот метод вызовет главный поток, когда закончит работу"""
        self.gui_ready_for_next = True
        return
