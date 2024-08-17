from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QPen, QBrush

class CustomCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(800)
        self.setMinimumHeight(200)
        self.slider_value = 0
        self.slider_width = 5
        self.slider_height = 150
        self.slider_rect = QRect(self.slider_value, self.height() // 2 - self.slider_height // 2, self.slider_width, self.slider_height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(Qt.GlobalColor.black, 2))

        # Draw the circles
        # painter.setBrush(QBrush(Qt.GlobalColor.blue))
        # circle_diameter = 30
        # for i in range(3):
        #     painter.drawEllipse(QRect(100 + i * 200, 50, circle_diameter, circle_diameter))

        # Draw the rectangles
        rect_width = 200
        rect_height = 30
        for i in range(3):
            rect = QRect(100 + i * 200, 40+i*50, rect_width, rect_height)
            if rect.intersects(self.slider_rect):
                painter.setBrush(QBrush(Qt.GlobalColor.green))
            else:
                painter.setBrush(QBrush(Qt.GlobalColor.darkGreen))
            painter.drawRect(rect)

        # Draw the slider (moving rectangle)
        painter.setBrush(QBrush(Qt.GlobalColor.red))
        self.slider_rect = QRect(self.slider_value * (self.width() - self.slider_width) // 1000, 
                                 self.height() // 2 - self.slider_height // 2, 
                                 self.slider_width, self.slider_height)
        painter.drawRect(self.slider_rect)

    def mousePressEvent(self, event):
        if self.slider_rect.contains(event.position().toPoint()):
            self.slider_value = (event.position().x() - self.slider_width // 2) * 1000 // (self.width() - self.slider_width)
            self.slider_value = max(0, min(1000, self.slider_value))
            self.update()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.slider_value = (event.position().x() - self.slider_width // 2) * 1000 // (self.width() - self.slider_width)
            self.slider_value = max(0, min(1000, self.slider_value))
            self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Custom Canvas with Slider, Circles, and Rectangles')
        self.setGeometry(100, 100, 800, 200)  # Adjust size as needed

        # Create the custom canvas
        self.custom_canvas = CustomCanvas()

        # Set up the layout
        self.setCentralWidget(self.custom_canvas)

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
