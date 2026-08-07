"""
Легковесный поток для итерации по картам
"""

# import time

from qgis.PyQt.QtCore import QThread, pyqtSignal

from QGIS_VDO.vdo import BLADDR  # , COORD
from QGIS_VDO.vdo.consts import struct_UINT
from QGIS_VDO.vdo.blocks import (block_0x08,
                                 block_0x09)


# Легковесный поток для итерации по картам - класс фонового потока для подсчета/загрузки карт  # noqa
class FolderMapProcessingWorker(QThread):
    # Сигнал передает: (индекс текущего шага в int, имя обрабатываемого файла в str)
    progress_signal = pyqtSignal(int, str)
    #
    count_signal = pyqtSignal(int)
    # Safe drawing areas packet signal
    safe_drawing_map_signal = pyqtSignal(list)

    def __init__(self, almanac_block: block_0x08):
        super().__init__()
        self.almanac_block = almanac_block
        
    def run(self):
        # Получить список из альманаха
        total_blocks = self.almanac_block.items_cnt()
        self.count_signal.emit(total_blocks)
        if not total_blocks:
            return

        # bl_folder  block_0x09
        index = 0
        for (bla_val, origin, rt_max) in self.almanac_block.get_items():
            index += 1

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
            self.progress_signal.emit(index + 1, f"{bl_folder}")
