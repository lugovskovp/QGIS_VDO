import pytest
from unittest.mock import MagicMock, patch

from qgis.gui import QgsMapCanvas
from qgis.core import QgsPointXY
from qgis.PyQt.QtCore import Qt, QPoint
# from qgis.PyQt.QtGui import QCursor

from QGIS_VDO.ui_files.ClickCoordinatesTool import ClickCoordinatesTool


# Фикстуру qgis_app УДАЛИЛИ, так как её автоматически предоставляет плагин pytest-qgis

@pytest.fixture
def tool_setup():
    # Создаем настоящий холст
    canvas = QgsMapCanvas()
    
    # Мокаем методы управления инструментами и фокусом
    canvas.unsetMapTool = MagicMock()
    canvas.setFocus = MagicMock()
    
    mock_callback = MagicMock()
    mock_deactivate_callback = MagicMock()
    
    tool = ClickCoordinatesTool(canvas, mock_callback, mock_deactivate_callback)
    
    return tool, canvas, mock_callback, mock_deactivate_callback


def test_init(tool_setup):
    """Тест инициализации класса"""
    tool, canvas, mock_callback, mock_deactivate_callback = tool_setup
    
    assert tool.canvas == canvas
    assert tool.callback == mock_callback
    assert tool.deactivate_callback == mock_deactivate_callback


def test_activate(tool_setup):
    """Тест активации инструмента"""
    tool, canvas, _, _ = tool_setup
    
    with patch('qgis.gui.QgsMapTool.activate') as mock_super_activate:
        tool.activate()
        
        assert canvas.cursor().shape() == Qt.CrossCursor
        canvas.setFocus.assert_called_once()
        mock_super_activate.assert_called_once()


def test_deactivate(tool_setup):
    """Тест деактивации инструмента"""
    tool, canvas, _, mock_deactivate_callback = tool_setup
    
    with patch('qgis.gui.QgsMapTool.deactivate') as mock_super_deactivate:
        tool.deactivate()
        
        assert canvas.cursor().shape() == Qt.ArrowCursor
        mock_deactivate_callback.assert_called_once()
        mock_super_deactivate.assert_called_once()


def test_canvas_release_event(tool_setup):
    """Тест клика мыши по карте"""
    tool, canvas, mock_callback, _ = tool_setup
    
    mock_event = MagicMock()
    click_pos = QPoint(100, 200)
    mock_event.pos.return_value = click_pos
    
    expected_point = QgsPointXY(55.7558, 37.6173)
    
    # Мокаем метод прямо на инстансе инструмента
    mock_to_map = MagicMock(return_value=expected_point)
    tool.toMapCoordinates = mock_to_map
    
    tool.canvasReleaseEvent(mock_event)
    
    mock_to_map.assert_called_once_with(click_pos)
    mock_callback.assert_called_once_with(expected_point)
    canvas.unsetMapTool.assert_called_once_with(tool)


def test_key_press_event_escape(tool_setup):
    """Тест нажатия клавиши Escape"""
    tool, canvas, _, _ = tool_setup
    
    mock_event = MagicMock()
    mock_event.key.return_value = Qt.Key_Escape
    
    tool.keyPressEvent(mock_event)
    
    canvas.unsetMapTool.assert_called_once_with(tool)
    mock_event.accept.assert_called_once()


def test_key_press_event_other_key(tool_setup):
    """Тест нажатия любой другой клавиши (не Esc)"""
    tool, canvas, _, _ = tool_setup
    
    mock_event = MagicMock()
    mock_event.key.return_value = Qt.Key_Return
    
    tool.keyPressEvent(mock_event)
    
    canvas.unsetMapTool.assert_not_called()
    mock_event.accept.assert_not_called()
