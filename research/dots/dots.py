import sys
import struct
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt, QPoint


def load_dots_from_bin(bin_path: str) -> list[int]:
    """Read big-endian (x, y) word pairs from binary file starting at offset 0x650."""
    count = 0x2E4  # number of coordinate pairs
    offset = 0x650
    pair_size = 4  # 2 × word (2 bytes each)

    with open(bin_path, "rb") as f:
        data = f.read()

    dots_xy: list[int] = []
    for i in range(count):
        start = offset + i * pair_size
        x, y = struct.unpack(">HH", data[start : start + pair_size])
        dots_xy.extend([x, y])

    return dots_xy


BIN_FILE = Path(__file__).parent / "carindb_1E345000h_1800h_калининград.bin"
dots_xy = load_dots_from_bin(str(BIN_FILE))


class CanvasWidget(QWidget):
    WIDTH = 800
    HEIGHT = 600
    MAX_COORD = 0xA000  # максимальное значение x и y

    def __init__(self):
        super().__init__()
        self.resize(self.WIDTH, self.HEIGHT)

        # Фиксированный масштаб: 0..0xA00 на оба измерения
        self.x_min = 0
        self.x_max = self.MAX_COORD
        self.y_min = 0
        self.y_max = self.MAX_COORD

        self.view_w = self.WIDTH
        self.view_h = self.HEIGHT

        # Сохраняем пропорцию для квадратного масштабирования
        scale_x = self.view_w / (self.x_max - self.x_min)
        scale_y = self.view_h / (self.y_max - self.y_min)
        self.scale = min(scale_x, scale_y)

        # Центрируем с отступами
        self.offset_x = int((self.view_w - (self.x_max - self.x_min) * self.scale) / 2)
        self.offset_y = int((self.view_h - (self.y_max - self.y_min) * self.scale) / 2)

    def _map(self, x: int, y: int) -> QPoint:
        mx = self.offset_x + x * self.scale
        my = self.offset_y + (self.y_max - y) * self.scale
        return QPoint(int(mx), int(my))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Рамка области координат
        pen_border = QPen(Qt.gray, 1)
        painter.setPen(pen_border)
        painter.drawRect(0, 0, self.view_w, self.view_h)

        # Точки-крестики
        pen_dot = QPen(Qt.red, 2)
        painter.setPen(pen_dot)

        for i in range(0, len(dots_xy), 2):
            x = dots_xy[i]
            y = dots_xy[i + 1]
            point = self._map(x, y)
            self._draw_cross(painter, point)

        painter.end()

    def _draw_cross(self, painter, point):
        size = 6
        painter.drawLine(
            point.x() - size, point.y() - size,
            point.x() + size, point.y() + size,
        )
        painter.drawLine(
            point.x() + size, point.y() - size,
            point.x() - size, point.y() + size,
        )


class DotsWindow(QMainWindow):
    WIDTH = 120
    HEIGHT = 80

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Точки-крестики")
        self.resize(800, 600)

        canvas = CanvasWidget()
        self.setCentralWidget(canvas)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DotsWindow()
    window.show()
    sys.exit(app.exec_())
