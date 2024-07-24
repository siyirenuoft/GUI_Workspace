import sys
import csv
from PyQt6.QtGui import QAction
import pyqtgraph as pg
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMenuBar, QFileDialog, 
                             QVBoxLayout, QWidget, QDialog, QLineEdit, QPushButton, QLabel,
                             QGraphicsView, QGraphicsScene, QGraphicsEllipseItem)
from PyQt6.QtGui import QAction, QColor, QPen, QPainter
from PyQt6.QtCore import Qt, QRectF

class Actuator(QGraphicsEllipseItem):
    def __init__(self, x, y, radius, color, parent=None):
        super().__init__(0, 0, radius*2, radius*2, parent)
        self.setPos(x - radius, y - radius)
        self.setBrush(color)
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, event):
        self.setPen(QPen(Qt.GlobalColor.red, 2))

    def hoverLeaveEvent(self, event):
        self.setPen(QPen(Qt.GlobalColor.black, 1))

class ActuatorCanvas(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHints(self.renderHints() | QPainter.RenderHint.Antialiasing)

        self.actuators = []
        self.colors = [QColor(255, 0, 0), QColor(0, 255, 0), QColor(0, 0, 255),
                       QColor(255, 255, 0), QColor(255, 0, 255), QColor(0, 255, 255)]
        self.color_index = 0

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = self.mapToScene(event.pos())
            self.add_actuator(pos.x(), pos.y())
        elif event.button() == Qt.MouseButton.RightButton:
            self.remove_actuator(event.pos())

    def add_actuator(self, x, y):
        color = self.colors[self.color_index % len(self.colors)]
        actuator = Actuator(x, y, 10, color)
        self.scene.addItem(actuator)
        self.actuators.append(actuator)
        self.color_index += 1

    def remove_actuator(self, pos):
        item = self.itemAt(pos)
        if isinstance(item, Actuator):
            self.scene.removeItem(item)
            self.actuators.remove(item)

class InputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Input Sampling Frequency")
        self.layout = QVBoxLayout(self)
        
        self.label = QLabel("Enter sampling frequency (Hz):")
        self.layout.addWidget(self.label)
        
        self.input = QLineEdit(self)
        self.layout.addWidget(self.input)
        
        self.button = QPushButton("OK", self)
        self.button.clicked.connect(self.accept)
        self.layout.addWidget(self.button)

    def get_value(self):
        return int(self.input.text()) if self.input.text().isdigit() else None

class WaveformData:
    def __init__(self):
        self.magnitude = []
        self.sampling_frequency = 0

class FileHandler:
    @staticmethod
    def load_csv(filename):
        data = WaveformData()
        try:
            with open(filename, 'r') as file:
                csv_reader = csv.reader(file)
                data.magnitude = []
                for row in csv_reader:
                    if row and len(row) > 0:  # Check if row is not empty
                        try:
                            data.magnitude.append(float(row[0]))
                        except ValueError:
                            print(f"Warning: Skipping invalid value: {row[0]}")
                if not data.magnitude:
                    print("Warning: No valid data found in the CSV file.")
        except Exception as e:
            print(f"Error reading CSV file: {str(e)}")
        return data

class MenuBar(QMenuBar):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_menus()

    def create_menus(self):
        file_menu = self.addMenu("File")
        
        new_action = QAction("New Workspace", self)
        new_action.triggered.connect(self.new_workspace)
        file_menu.addAction(new_action)
        
        open_action = QAction("Open File", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

    def new_workspace(self):
        print("New Workspace")  # Placeholder for now

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)")
        if filename:
            dialog = InputDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                sampling_frequency = dialog.get_value()
                if sampling_frequency is not None:
                    data = FileHandler.load_csv(filename)
                    if data.magnitude:
                        data.sampling_frequency = sampling_frequency
                        self.parent().update_waveform(data)
                    else:
                        print("No valid data to display")
                else:
                    print("Invalid sampling frequency")

class WaveformCanvas(pg.PlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackground('w')
        self.showGrid(x=True, y=True)
        self.setLabel('left', 'Magnitude')
        self.setLabel('bottom', 'Time (s)')

    def update_plot(self, data):
        self.clear()
        if data.magnitude and data.sampling_frequency:
            time = np.arange(len(data.magnitude)) / data.sampling_frequency
            self.plot(time, data.magnitude, pen='b')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Haptics Pattern Design App")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.menu_bar = MenuBar(self)
        self.setMenuBar(self.menu_bar)

        self.waveform_canvas = WaveformCanvas()
        self.layout.addWidget(self.waveform_canvas)

        self.actuator_canvas = ActuatorCanvas()
        self.layout.addWidget(self.actuator_canvas)

        # Placeholder for MultitrackEditor
        self.multitrack_editor = QWidget()
        self.layout.addWidget(self.multitrack_editor)

    def update_waveform(self, data):
        self.waveform_canvas.update_plot(data)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())