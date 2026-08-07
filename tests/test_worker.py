import pytest    # type: ignore # noqa
from unittest.mock import MagicMock, patch
from qgis.PyQt.QtCore import QEventLoop

from QGIS_VDO.vdo_threading import FolderMapProcessingWorker


WORKER_MODULE = 'QGIS_VDO.vdo_threading'


@pytest.fixture
def mock_vdo_structures():
    """Фикстура для создания связанных мок-объектов VDO."""
    mock_vdo = MagicMock()
    mock_almanac = MagicMock()
    mock_almanac.vdo = mock_vdo
    
    mock_bl_folder = MagicMock()
    mock_bl_folder.__str__.return_value = "Mocked_Folder_0x09"
    mock_vdo.get_block.return_value = mock_bl_folder
    
    return {
        "almanac": mock_almanac,
        "vdo": mock_vdo,
        "folder": mock_bl_folder
    }


def test_worker_empty_almanac(mock_vdo_structures):
    """Тест сценария, когда в альманахе нет элементов, с ручным QEventLoop."""
    mock_almanac = mock_vdo_structures["almanac"]
    mock_almanac.items_cnt.return_value = 0
    
    worker = FolderMapProcessingWorker(mock_almanac)
    
    # Создаем локальный цикл событий
    loop = QEventLoop()
    
    # Переменная для сохранения аргументов сигнала
    captured_args = []
    
    # Слот для сохранения данных и выхода из цикла
    def on_count_signal(val):
        captured_args.append(val)
        loop.quit()
        
    worker.count_signal.connect(on_count_signal)
    
    # Также выходим из цикла, если поток вдруг завершился без сигнала
    worker.finished.connect(loop.quit)
    
    # Запускаем поток и ждем обработки
    worker.start()
    loop.exec_()  # noqa Блокирует тест, пока не вызовется loop.quit()
    
    # Проверяем перехваченный аргумент
    assert captured_args == [0]
    
    # Очищаем память
    worker.wait()
    worker.deleteLater()


@patch(f'{WORKER_MODULE}.BLADDR')
@patch(f'{WORKER_MODULE}.struct_UINT')
def test_worker_processing_flow(mock_struct_uint, mock_bladdr_cls, mock_vdo_structures):
    """Тест успешного цикла обработки элементов альманаха с ручным QEventLoop."""
    mock_almanac = mock_vdo_structures["almanac"]
    mock_bl_folder = mock_vdo_structures["folder"]
    
    mock_almanac.items_cnt.return_value = 1
    mock_almanac.get_items.return_value = [(123, "origin_data", "rt_max_data")]
    
    mock_lb = MagicMock(lat=55.75, lon=37.61)
    mock_rt = MagicMock(lat=56.00, lon=38.00)
    # (bl_map_val, lon_min, lat_min, lon_max, lat_max)
    mock_bl_folder.get_items.return_value = [(0xABC, mock_lb.lon, mock_lb.lat, mock_rt.lon, mock_rt.lat)]
    
    mock_struct_uint.pack.return_value = b'\x00\x00\x00\x00'
    
    worker = FolderMapProcessingWorker(mock_almanac)
    
    # Слоты-шпионы для сбора результатов из сигналов
    results = {
        "count": [],
        "map": [],
        "progress": []
    }
    
    worker.count_signal.connect(lambda val: results["count"].append(val))
    worker.safe_drawing_map_signal.connect(lambda val: results["map"].append(val))
    worker.progress_signal.connect(lambda idx, name: results["progress"].append((idx, name)))
    
    # Используем цикл событий для ожидания завершения потока
    loop = QEventLoop()
    worker.finished.connect(loop.quit)
    
    worker.start()
    loop.exec_()  # noqa Ждем окончания работы run() воркера
    
    # Проверяем count_signal
    assert results["count"] == [1]
    
    # Проверяем структуру пакета координат из safe_drawing_map_signal
    expected_area = {
        "area": [(55.75, 37.61), (56.00, 38.00)],
        "name": "0xABC"
    }
    assert results["map"] == [[expected_area]]
    
    # Проверяем progress_signal (index + 1 = 2)
    assert results["progress"] == [(2, "Mocked_Folder_0x09")]
    
    # Очищаем память
    worker.wait()
    worker.deleteLater()
