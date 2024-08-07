import sys
import os
import queue
import matplotlib
import numpy as np
import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as Navi
from matplotlib.figure import Figure
from matplotlib.pyplot import scatter
import matplotlib.ticker as ticker
import random
from PyQt6 import QtCore, QtWidgets, QtGui, QtMultimedia
from PyQt6 import uic
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from datetime import date, datetime
matplotlib.use('QtAgg')
from matplotlib.colors import to_rgba
import json

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QTreeWidgetItem, QDialog
from PyQt6.QtCore import Qt, pyqtSlot, QPoint
from PyQt6.QtGui import QPen, QColor, QBrush, QFont
from PyQt6.QtCore import pyqtSignal

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=8, height=2, dpi=100, app_reference=None):
        self.app_reference = app_reference  # Reference to Haptics_App
        self.current_signal = None  # Track the current signal
        bg_color = (134/255, 150/255, 167/255)
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor=bg_color)
        self.axes = self.fig.add_axes([0.1, 0.15, 0.8, 0.8])  # Use add_axes to create a single plot
        self.axes.set_facecolor(bg_color)

        # Convert RGB to rgba using matplotlib.colors.to_rgba
        spine_color = to_rgba((240/255, 235/255, 229/255))

        self.axes.tick_params(axis='x', colors=spine_color, labelsize=8)  # Adjust tick label size here
        self.axes.tick_params(axis='y', colors=spine_color, labelsize=8)  # Adjust tick label size here
        self.axes.spines['bottom'].set_color(spine_color)
        self.axes.spines['top'].set_color(spine_color)
        self.axes.spines['right'].set_color(spine_color)
        self.axes.spines['left'].set_color(spine_color)
        self.axes.set_ylabel('Amplitude', fontsize=9.5, color=spine_color)  # Adjust font size here

        # Move x-axis label to the right side
        self.set_custom_xlabel('Time (s)', fontsize=9.5, color=spine_color)  # Custom method for xlabel

        super(MplCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.setStyleSheet("background-color: rgb(134, 150, 167); color: spine_color;")
        self.fig.tight_layout()

        # Enable drag and drop
        self.setAcceptDrops(True)

        # Draw initial empty plot
        self.plot([], [])

    def set_custom_xlabel(self, xlabel, fontsize=9.5, color='black'):
        self.axes.set_xlabel('')  # Remove default xlabel
        self.axes.annotate(xlabel, xy=(1.01, -0.01), xycoords='axes fraction', fontsize=fontsize,
                           color=color, ha='left', va='center')

    def plot(self, x, y):
        self.axes.clear()
        bg_color = (134/255, 150/255, 167/255)
        # Convert RGB to rgba using matplotlib.colors.to_rgba
        spine_color = to_rgba((240/255, 235/255, 229/255))
        self.axes.set_facecolor(bg_color)
        
        if len(x) == len(y):
            self.axes.plot(x, y, color=spine_color)
        else:
            print(f"Error: x and y must have the same length, but have shapes {x.shape} and {y.shape}")
        
        # Set x and y labels
        self.set_custom_xlabel('Time (s)', fontsize=9.5, color=spine_color)  # Custom method for xlabel
        self.axes.set_ylabel('Amplitude', fontsize=9.5, color=spine_color)  # Adjust font size here
        
        self.axes.tick_params(axis='x', colors=spine_color, labelsize=8)  # Adjust tick label size here
        self.axes.tick_params(axis='y', colors=spine_color, labelsize=8)  # Adjust tick label size here
        self.axes.spines['bottom'].set_color(spine_color)
        self.axes.spines['top'].set_color(spine_color)
        self.axes.spines['right'].set_color(spine_color)
        self.axes.spines['left'].set_color(spine_color)
        self.draw()

    def add_signal(self, signal_data, combine):
        new_signal = np.array(signal_data["data"])
        # print("new",new_signal)
        if combine and self.current_signal is not None:
            #print("current",self.current_signal)
            # print("new",new_signal)
            self.current_signal = self.current_signal + new_signal
            #print("combine", self.current_signal)
        else:
            self.current_signal = new_signal
        t = np.linspace(0, 1, len(self.current_signal))
        self.plot(t, self.current_signal)

    def clear_plot(self):
        self.current_signal = None
        self.plot([], [])

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        item = event.source().selectedItems()[0]
        signal_type = item.text(0)
        if signal_type in self.app_reference.imported_signals:  # Check if it's an imported signal
            imported_signal = self.app_reference.imported_signals.get(signal_type)
            # print(imported_signal)
            self.add_signal(imported_signal, combine=True)
        elif signal_type in self.app_reference.custom_signals:  # Check if it's a custom signal
            custom_signal = self.app_reference.custom_signals.get(signal_type)
            self.add_signal(custom_signal, combine=True)
        elif signal_type in self.app_reference.signal_templates:  # Check if it's a provided signal template
            template_signal = self.app_reference.signal_templates.get(signal_type)
            self.add_signal(template_signal, combine=True)
        else:
            self.add_signal(signal_type, combine=False)  # Show the signal itself when clicked

    # def dropEvent(self, event):
    #     item = event.source().selectedItems()[0]
    #     signal_type = item.text(0)
    #     print(f"dropEvent - signal_type: {signal_type}")
    #     if signal_type in self.app_reference.imported_signals:
    #         signal_data = self.app_reference.imported_signals[signal_type]
    #         print(f"dropEvent - signal_data: {signal_data}")
    #         self.app_reference.add_signal(signal_type, combine=True)
    #     else:
    #         print("dropEvent - signal not found in imported_signals")


# Define the ACTUATOR_CONFIG dictionary
ACTUATOR_CONFIG = {
    "LRA": {
        "text_vertical_offset": -0.5,
        "text_horizontal_offset": 0.5,
        "font_size_factor": 0.9,
        "min_font_size": 6,
        "max_font_size": 12
    },
    "VCA": {
        "text_vertical_offset": -1,
        "text_horizontal_offset": 0.25,
        "font_size_factor": 0.9,
        "min_font_size": 6,
        "max_font_size": 12
    },
    "M": {
        "text_vertical_offset": -0.8,
        "text_horizontal_offset": 0.25,
        "font_size_factor": 0.9,
        "min_font_size": 6,
        "max_font_size": 12
    }
}

# Predefined color list for actuators (20 colors)
COLOR_LIST = [
    QColor(194, 166, 159),  # Pale Taupe
    QColor(171, 205, 239),  # Light Blue
    QColor(194, 178, 128),  # Khaki
    QColor(242, 215, 213),  # Misty Rose
    QColor(204, 204, 255),  # Lavender
    QColor(200, 202, 167),  # Pale Goldenrod
    QColor(180, 144, 125),  # Tan
    QColor(150, 143, 132),  # Dark Gray
    QColor(206, 179, 139),  # Burly Wood
    QColor(160, 159, 153),  # Light Slate Gray
    QColor(158, 175, 163),  # Dark Sea Green
    QColor(175, 167, 191),  # Thistle
    QColor(224, 224, 224),  # Gainsboro
    QColor(192, 192, 192),  # Silver
    QColor(230, 159, 125),  # Peach
    QColor(255, 182, 193),  # Light Pink
    QColor(139, 121, 94),   # Umber
    QColor(169, 196, 176),  # Dark Moss Green
    QColor(144, 175, 197),  # Cadet Blue
    QColor(188, 170, 164)   # Rosy Brown
]

# Function to generate a contrasting color
def generate_contrasting_color(existing_colors):
    while True:
        new_color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        contrast = all(abs(new_color.red() - color.red()) + abs(new_color.green() - color.green()) + abs(new_color.blue() - color.blue()) > 200 for color in existing_colors)
        if contrast:
            return new_color



class Actuator(QGraphicsItem):
    properties_changed = pyqtSignal(str, str, str)  # Signal to indicate properties change: id, type, color

    def __init__(self, x, y, size, color, actuator_type, id, predecessor=None, successor=None):
        super().__init__()
        self.setPos(x, y)
        self.size = size
        self.color = color
        self.actuator_type = actuator_type
        self.id = id
        self.predecessor = predecessor
        self.successor = successor
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

        # Apply configuration
        config = ACTUATOR_CONFIG.get(self.actuator_type, ACTUATOR_CONFIG["LRA"])
        self.text_vertical_offset = config["text_vertical_offset"]
        self.text_horizontal_offset = config["text_horizontal_offset"]
        self.font_size_factor = config["font_size_factor"]
        self.min_font_size = config["min_font_size"]
        self.max_font_size = config["max_font_size"]

        # Calculate initial font size
        self.font_size = self.calculate_font_size()        

    def calculate_font_size(self):
        base_size = self.size / 2 * self.font_size_factor
        id_length = len(self.id)
        if id_length > 3:
            base_size *= 3 / id_length
        return max(self.min_font_size, min(base_size, self.max_font_size))

    def get_color_name(self, color):
        colors = [
            (QColor(255, 0, 0), "Red"),
            (QColor(0, 255, 0), "Green"),
            (QColor(0, 0, 255), "Blue"),
            (QColor(255, 255, 0), "Yellow"),
            (QColor(255, 0, 255), "Magenta"),
            (QColor(0, 255, 255), "Cyan")
        ]
        for qcolor, name in colors:
            if qcolor == color:
                return name
        return "Unknown"

    def boundingRect(self):
        return QRectF(-self.size/2, -self.size/2, self.size, self.size)

    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        
        if self.actuator_type == "LRA":
            painter.drawEllipse(self.boundingRect())
        elif self.actuator_type == "VCA":
            painter.drawRect(self.boundingRect())
        else:  # "M"
            painter.drawRoundedRect(self.boundingRect(), 5, 5)
        
        # Set font size
        font = painter.font()
        font.setPointSizeF(self.calculate_font_size())
        painter.setFont(font)
        
        # Calculate text position
        rect = self.boundingRect()
        text_rect = QRectF(rect.left() + self.text_horizontal_offset,
                           rect.top() + self.text_vertical_offset,
                           rect.width(),
                           rect.height())
        
        # Draw text
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.id)

    def hoverEnterEvent(self, event):
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def hoverLeaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        canvas_rect = self.scene().views()[0].canvas_rect  # Get the canvas rectangle

        # Get the current position and bounding rectangle of the actuator
        new_pos = self.pos()
        bounding_rect = self.boundingRect().translated(new_pos)

        # Calculate the adjusted position to keep the actuator within the canvas
        if bounding_rect.left() < canvas_rect.left():
            new_pos.setX(canvas_rect.left() + self.size / 2)
        if bounding_rect.right() > canvas_rect.right():
            new_pos.setX(canvas_rect.right() - self.size / 2)
        if bounding_rect.top() < canvas_rect.top():
            new_pos.setY(canvas_rect.top() + self.size / 2)
        if bounding_rect.bottom() > canvas_rect.bottom():
            new_pos.setY(canvas_rect.bottom() - self.size / 2)

        # Set the new position if it has changed
        if new_pos != self.pos():
            self.setPos(new_pos)

    
    def adjust_text_position(self, vertical_offset, horizontal_offset):
        self.text_vertical_offset = vertical_offset
        self.text_horizontal_offset = horizontal_offset
        self.update()

    def adjust_font_size(self, factor, min_size, max_size):
        self.font_size_factor = factor
        self.min_font_size = min_size
        self.max_font_size = max_size
        self.update()
    
    def update_properties(self, actuator_type, color):
        self.actuator_type = actuator_type
        self.color = color
        self.update()
        self.properties_changed.emit(self.id, self.actuator_type, self.color.name())

class ActuatorPropertiesDialog(QDialog):
    def __init__(self, actuator, parent=None):
        super().__init__(parent)
        self.actuator = actuator
        self.setWindowTitle("Actuator Properties")
        self.layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        self.id_input = QLineEdit(actuator.id)
        form_layout.addRow("ID:", self.id_input)

        type_layout = QHBoxLayout()
        self.type_group = QButtonGroup(self)
        self.lra_radio = QRadioButton("LRA")
        self.vca_radio = QRadioButton("VCA")
        self.m_radio = QRadioButton("M")
        self.type_group.addButton(self.lra_radio)
        self.type_group.addButton(self.vca_radio)
        self.type_group.addButton(self.m_radio)
        type_layout.addWidget(self.lra_radio)
        type_layout.addWidget(self.vca_radio)
        type_layout.addWidget(self.m_radio)
        form_layout.addRow("Type:", type_layout)

        self.predecessor_input = QLineEdit(actuator.predecessor or "")
        self.successor_input = QLineEdit(actuator.successor or "")
        form_layout.addRow("Predecessor:", self.predecessor_input)
        form_layout.addRow("Successor:", self.successor_input)

        self.layout.addLayout(form_layout)

        button = QPushButton("OK")
        button.clicked.connect(self.accept)
        self.layout.addWidget(button)

        self.set_initial_type()

    def set_initial_type(self):
        if self.actuator.actuator_type == "LRA":
            self.lra_radio.setChecked(True)
        elif self.actuator.actuator_type == "VCA":
            self.vca_radio.setChecked(True)
        else:
            self.m_radio.setChecked(True)

    def get_type(self):
        if self.lra_radio.isChecked():
            return "LRA"
        elif self.vca_radio.isChecked():
            return "VCA"
        else:
            return "M"

class SelectionBar(QGraphicsItem):
    def __init__(self, scene, parent=None):
        super().__init__()
        self.setPos(10, 10)  # Default location in the top left corner
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.selection_icons = []
        self.scene = scene
        self.create_selection_icons()

    def create_selection_icons(self):
        actuator_types = ["LRA", "VCA", "M"]
        for i, act_type in enumerate(actuator_types):
            icon = Actuator(0, 0, 20, QColor(240, 235, 229), act_type, act_type)
            icon.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            icon.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
            icon.setPos(i*30 ,0)
            icon.setPos(-100, i * 30)
            icon.adjust_font_size(0.3, 6, 12)  # Adjust font size here
            self.selection_icons.append(icon)
            self.scene.addItem(icon)


class ActuatorCanvas(QGraphicsView):
    actuator_added = pyqtSignal(str, str, str, int, int)  # Signal to indicate an actuator is added with its properties
    properties_changed = pyqtSignal(str, str, str, str)
    actuator_deleted = pyqtSignal(str)  # Signal to indicate an actuator is deleted

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHints(QPainter.RenderHint.Antialiasing)

        self.actuators = []
        self.branch_colors = {}
        self.color_index = 0  # Index for the color list

        # Set background color to rgb(134, 150, 167)
        self.setBackgroundBrush(QBrush(QColor(134, 150, 167)))
        self.setSceneRect(-1000, -1000, 2000, 2000)  # Large scene to allow panning
        
        self.canvas_rect = QRectF(0, 0, 400, 300)
        self.white_rect_item = None
        self.scale_line = None
        self.scale_text = None
        self.update_canvas_visuals()

        self.setMouseTracking(True)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        self.setAcceptDrops(True)  # Allow drop events

        self.panning = False
        self.last_pan_point = QPointF()
        self.actuator_size = 20

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            actuator_type = event.mimeData().text()
            pos = self.mapToScene(event.position().toPoint())
            
            # Check if the drop position is within the allowed "white area"
            if self.is_drop_allowed(pos):
                self.add_actuator(pos.x(), pos.y(), actuator_type=actuator_type)
                event.acceptProposedAction()
            else:
                event.ignore()

    def add_actuator(self, x, y, new_id=None, actuator_type="LRA", predecessor=None, successor=None):
        if new_id is None:
            new_id = self.generate_next_id()
        
        branch = new_id.split('.')[0]
        if branch not in self.branch_colors:
            if self.color_index < len(COLOR_LIST):
                self.branch_colors[branch] = COLOR_LIST[self.color_index]
                self.color_index += 1
            else:
                self.branch_colors[branch] = generate_contrasting_color(list(self.branch_colors.values()))
        color = self.branch_colors[branch]

        if predecessor is None or successor is None:
            predecessor, successor = self.get_predecessor_successor(new_id)

        actuator = Actuator(x, y, self.actuator_size, color, actuator_type, new_id, predecessor, successor)
        self.scene.addItem(actuator)
        self.actuators.append(actuator)

        # Emit signal when an actuator is added
        self.actuator_added.emit(new_id, actuator_type, color.name(), x, y)

        # Update the predecessor's successor
        if predecessor:
            for act in self.actuators:
                if act.id == predecessor:
                    act.successor = new_id
                    break

        actuator.update()

    def is_drop_allowed(self, pos):
        return self.canvas_rect.contains(pos)


    def update_canvas_visuals(self):
        if self.white_rect_item:
            self.scene.removeItem(self.white_rect_item)
        
        # Set canvas color to a custom RGB value, e.g., (240, 235, 229)
        self.colored_rect_item = self.scene.addRect(self.canvas_rect, QPen(Qt.GlobalColor.black), QBrush(QColor(240, 235, 229)))
        self.colored_rect_item.setZValue(-999)

        if self.scale_line:
            self.scene.removeItem(self.scale_line)
        if self.scale_text:
            self.scene.removeItem(self.scale_text)

        self.scale_line = self.scene.addLine(self.canvas_rect.left() + 10, self.canvas_rect.bottom() - 10,
                                             self.canvas_rect.left() + 110, self.canvas_rect.bottom() - 10,
                                             QPen(Qt.GlobalColor.black, 2))
        self.scale_text = self.scene.addText("100 mm")
        text_rect = self.scale_text.boundingRect()
        self.scale_text.setPos(self.canvas_rect.left() + 50 - text_rect.width() / 2, self.canvas_rect.bottom() - 15 - text_rect.height())
        self.scale_line.setZValue(1000)
        self.scale_text.setZValue(1000)

    def update_scale_position(self):
        if self.scale_line and self.scale_text:
            self.scale_line.setLine(self.canvas_rect.left() + 10, self.canvas_rect.bottom() - 10,
                                    self.canvas_rect.left() + 110, self.canvas_rect.bottom() - 10)
            text_rect = self.scale_text.boundingRect()
            self.scale_text.setPos(self.canvas_rect.left() + 50 - text_rect.width() / 2, self.canvas_rect.bottom() - 15 - text_rect.height())

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        parent_app = self.window()  # Get the main window (Haptics_App)

        # Check if the item is in the selection view's scene
        selection_items = parent_app.selection_view.scene().items()
        if isinstance(item, Actuator) and item in selection_items:
            self.drag_start_pos = event.pos()
            self.dragging_item = item
            self.dragging_actuator = None  # Reset dragging actuator
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.panning = True
            self.last_pan_point = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton and isinstance(item, Actuator):
            self.show_context_menu(item, event.pos())
        else:
            super().mousePressEvent(event)


    def mouseMoveEvent(self, event):
        if self.panning:
            delta = event.pos() - self.last_pan_point
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self.last_pan_point = event.pos()
            event.accept()
        elif hasattr(self, 'dragging_item') and self.dragging_item:
            if not hasattr(self, 'dragging_actuator') or self.dragging_actuator is None:
                if (event.pos() - self.drag_start_pos).manhattanLength() >= QApplication.startDragDistance():
                    self.start_dragging_item(event)
            else:
                self.update_dragging_item(event)
            event.accept()
        else:
            super().mouseMoveEvent(event)


    def mouseReleaseEvent(self, event):
        if self.panning:
            self.panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        elif hasattr(self, 'dragging_item') and self.dragging_item:
            if hasattr(self, 'dragging_actuator') and self.dragging_actuator:
                pos = self.mapToScene(event.pos())
                if not self.is_drop_allowed(pos):
                    self.scene.removeItem(self.dragging_actuator)
                    self.actuators.remove(self.dragging_actuator)
                self.dragging_actuator = None
            self.dragging_item = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)


    def update_dragging_item(self, event):
        if hasattr(self, 'dragging_actuator') and self.dragging_actuator:
            pos = self.mapToScene(event.pos())
            self.dragging_actuator.setPos(pos.x(), pos.y())


    def start_dragging_item(self, event):
        item = self.dragging_item
        if item:
            actuator_type = item.actuator_type
            pos = self.mapToScene(event.pos())
            self.add_actuator(pos.x(), pos.y(), actuator_type=actuator_type)
            self.dragging_actuator = self.actuators[-1]  # Reference to the newly created actuator
            self.drag_start_pos = event.pos()  # Update drag start position

            # Example of using QPixmap if applicable
            pixmap = QPixmap(100, 100)  # Ensure pixmap is properly initialized
            if pixmap.isNull():
                print("Error: QPixmap is null")
            else:
                scaled_pixmap = pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio)
                drag = QDrag(self)
                mime_data = QMimeData()
                drag.setMimeData(mime_data)
                drag.setPixmap(scaled_pixmap)
                drag.exec()


    def wheelEvent(self, event: QWheelEvent):
        zoom_factor = 1.05  # Reduced from 1.25 to make zooming less sensitive

        old_pos = self.mapToScene(event.position().toPoint())

        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1 / zoom_factor, 1 / zoom_factor)

        new_pos = self.mapToScene(event.position().toPoint())

        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())

        self.update_scale_position()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.canvas_rect, Qt.AspectRatioMode.KeepAspectRatio)


    def generate_next_id(self):
        if not self.actuators:
            return "A.1"
        
        max_branch = max(act.id.split('.')[0] for act in self.actuators if '.' in act.id)
        max_number = max(int(act.id.split('.')[1]) for act in self.actuators if '.' in act.id and act.id.startswith(max_branch))
        
        return f"{max_branch}.{max_number + 1}"

    def get_predecessor_successor(self, new_id):
        branch, number = new_id.split('.')
        number = int(number)
        
        predecessor = None
        for act in reversed(self.actuators):
            if '.' in act.id:
                act_branch, act_number = act.id.split('.')
                if act_branch == branch and int(act_number) == number - 1:
                    predecessor = act.id
                    break
        
        return predecessor, None

    def show_context_menu(self, actuator, pos):
        menu = QMenu()
        edit_action = menu.addAction("Edit Properties")
        delete_action = menu.addAction("Delete")

        action = menu.exec(self.mapToGlobal(pos))
        if action == edit_action:
            self.edit_actuator_properties(actuator)
        elif action == delete_action:
            self.remove_actuator(actuator)


    def edit_actuator_properties(self, actuator):
        dialog = ActuatorPropertiesDialog(actuator, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            old_id = actuator.id
            new_id = dialog.id_input.text()
            actuator.id = new_id
            
            # Update color if branch has changed
            old_branch = old_id.split('.')[0]
            new_branch = new_id.split('.')[0]
            if old_branch != new_branch:
                if new_branch not in self.branch_colors:
                    self.branch_colors[new_branch] = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                actuator.color = self.branch_colors[new_branch]
            
            new_type = dialog.get_type()
            if new_type != actuator.actuator_type:
                actuator.actuator_type = new_type
                # Reapply configuration for new type
                config = ACTUATOR_CONFIG.get(actuator.actuator_type, ACTUATOR_CONFIG["LRA"])
                actuator.text_vertical_offset = config["text_vertical_offset"]
                actuator.text_horizontal_offset = config["text_horizontal_offset"]
                actuator.font_size_factor = config["font_size_factor"]
                actuator.min_font_size = config["min_font_size"]
                actuator.max_font_size = config["max_font_size"]
            
            actuator.predecessor = dialog.predecessor_input.text()
            actuator.successor = dialog.successor_input.text()
            
            actuator.size = self.actuator_size  # Use the canvas's actuator size
            
            actuator.update()
            
            # Update other actuators if necessary
            self.update_related_actuators(old_id, new_id)

            self.properties_changed.emit(old_id, new_id, new_type, actuator.color.name())
            # print(new_id, new_type, actuator.color.name())

    def update_related_actuators(self, old_id, new_id):
        for act in self.actuators:
            if act.predecessor == old_id:
                act.predecessor = new_id
            if act.successor == old_id:
                act.successor = new_id
            act.update()

    def remove_actuator(self, actuator):
        self.scene.removeItem(actuator)
        self.actuators.remove(actuator)
        self.actuator_deleted.emit(actuator.id)  # Emit the deletion signal

    def set_canvas_size(self, width, height):
        self.canvas_rect = QRectF(0, 0, width, height)
        self.update_canvas_visuals()
        self.fitInView(self.canvas_rect, Qt.AspectRatioMode.KeepAspectRatio)

    def create_actuator_branch(self, num_actuators, lra_count, vca_count, m_count, grid_pattern):
        # Get the next branch letter
        if not self.actuators:
            next_branch = 'A'
        else:
            max_branch = max(act.id.split('.')[0] for act in self.actuators if '.' in act.id)
            next_branch = chr(ord(max_branch) + 1)

        # Parse grid pattern
        rows, cols = map(int, grid_pattern.split('x'))

        calculated_size = min(self.canvas_rect.width() / (cols + 1), self.canvas_rect.height() / (rows + 1)) * 0.6
        self.actuator_size = min(calculated_size, 20)

        # Calculate spacing
        spacing_x = self.canvas_rect.width() / (cols + 1)
        spacing_y = self.canvas_rect.height() / (rows + 1)

        # Create actuators
        actuator_types = ['LRA'] * lra_count + ['VCA'] * vca_count + ['M'] * m_count
        random.shuffle(actuator_types)

        for i in range(num_actuators):
            row = i // cols
            col = i % cols
            x = spacing_x * (col + 1)
            y = spacing_y * (row + 1)

            new_id = f"{next_branch}.{i+1}"
            actuator_type = actuator_types[i] if i < len(actuator_types) else 'LRA'

            predecessor = f"{next_branch}.{i}" if i > 0 else None
            successor = f"{next_branch}.{i+2}" if i < num_actuators - 1 else None

            self.add_actuator(x, y, new_id, actuator_type, predecessor, successor)

        self.actuator_size = 20
        
        for actuator in self.actuators:
            actuator.size = self.actuator_size
            actuator.update()

        self.update()
    
    def clear_canvas(self):
        for actuator in self.actuators:
            self.scene.removeItem(actuator)
        self.actuators.clear()
        self.branch_colors.clear()
        self.actuator_size = 20  # Reset to default size
        self.update_canvas_visuals()


class SelectionBarView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.setScene(scene)
        self.setRenderHints(QPainter.RenderHint.Antialiasing)
        self.setFixedSize(100, 100)  # Adjust size as needed
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("background: transparent; border: none;")
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, Actuator):
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(item.actuator_type)
            drag.setMimeData(mime_data)
            drag.exec(Qt.DropAction.CopyAction)
        super().mousePressEvent(event)


class ActuatorPropertiesDialog(QDialog):
    def __init__(self, actuator, parent=None):
        super().__init__(parent)
        self.actuator = actuator
        self.setWindowTitle("Actuator Properties")
        self.layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        self.id_input = QLineEdit(actuator.id)
        form_layout.addRow("ID:", self.id_input)

        type_layout = QHBoxLayout()
        self.type_group = QButtonGroup(self)
        self.lra_radio = QRadioButton("LRA")
        self.vca_radio = QRadioButton("VCA")
        self.m_radio = QRadioButton("M")
        self.type_group.addButton(self.lra_radio)
        self.type_group.addButton(self.vca_radio)
        self.type_group.addButton(self.m_radio)
        type_layout.addWidget(self.lra_radio)
        type_layout.addWidget(self.vca_radio)
        type_layout.addWidget(self.m_radio)
        form_layout.addRow("Type:", type_layout)

        self.predecessor_input = QLineEdit(actuator.predecessor or "")
        self.successor_input = QLineEdit(actuator.successor or "")
        form_layout.addRow("Predecessor:", self.predecessor_input)
        form_layout.addRow("Successor:", self.successor_input)

        self.layout.addLayout(form_layout)

        button = QPushButton("OK")
        button.clicked.connect(self.accept)
        self.layout.addWidget(button)

        self.set_initial_type()

    def set_initial_type(self):
        if self.actuator.actuator_type == "LRA":
            self.lra_radio.setChecked(True)
        elif self.actuator.actuator_type == "VCA":
            self.vca_radio.setChecked(True)
        else:
            self.m_radio.setChecked(True)

    def get_type(self):
        if self.lra_radio.isChecked():
            return "LRA"
        elif self.vca_radio.isChecked():
            return "VCA"
        else:
            return "M"

class CreateBranchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Actuator Branch")
        layout = QVBoxLayout(self)

        self.num_actuators_input = QSpinBox()
        self.num_actuators_input.setMinimum(1)
        self.num_actuators_input.valueChanged.connect(self.update_max_counts)
        layout.addWidget(QLabel("Number of Actuators:"))
        layout.addWidget(self.num_actuators_input)

        self.lra_input = QSpinBox()
        self.lra_input.valueChanged.connect(self.check_total)
        layout.addWidget(QLabel("LRA Count:"))
        layout.addWidget(self.lra_input)

        self.vca_input = QSpinBox()
        self.vca_input.valueChanged.connect(self.check_total)
        layout.addWidget(QLabel("VCA Count:"))
        layout.addWidget(self.vca_input)

        self.m_input = QSpinBox()
        self.m_input.valueChanged.connect(self.check_total)
        layout.addWidget(QLabel("M Count:"))
        layout.addWidget(self.m_input)

        self.grid_pattern_input = QLineEdit()
        self.grid_pattern_input.textChanged.connect(self.validate_inputs)
        layout.addWidget(QLabel("Grid Pattern (e.g., 2x2, 3x3):"))
        layout.addWidget(self.grid_pattern_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.num_actuators_input.setValue(1)
        self.update_max_counts()
        self.validate_inputs()

    def update_max_counts(self):
        total = self.num_actuators_input.value()
        self.lra_input.setMaximum(total)
        self.vca_input.setMaximum(total)
        self.m_input.setMaximum(total)
        self.check_total()
        self.validate_inputs()

    def check_total(self):
        total = self.num_actuators_input.value()
        sum_counts = self.lra_input.value() + self.vca_input.value() + self.m_input.value()
        
        if sum_counts > total:
            diff = sum_counts - total
            if self.sender() == self.lra_input:
                self.lra_input.setValue(max(0, self.lra_input.value() - diff))
            elif self.sender() == self.vca_input:
                self.vca_input.setValue(max(0, self.vca_input.value() - diff))
            elif self.sender() == self.m_input:
                self.m_input.setValue(max(0, self.m_input.value() - diff))
            
            # Recalculate sum_counts after adjustment
            sum_counts = self.lra_input.value() + self.vca_input.value() + self.m_input.value()

        self.validate_inputs()

    def accept(self):
        if (self.lra_input.value() + self.vca_input.value() + self.m_input.value() == self.num_actuators_input.value() and
            self.validate_grid_pattern(self.grid_pattern_input.text())):
            super().accept()

    def validate_grid_pattern(self, pattern):
        if not pattern.strip():  # Allow empty pattern
            return True
        try:
            rows, cols = map(int, pattern.split('x'))
            return rows > 0 and cols > 0  # Just check if it's a valid grid format
        except ValueError:
            return False
        
    def validate_inputs(self):
        total = self.num_actuators_input.value()
        sum_counts = self.lra_input.value() + self.vca_input.value() + self.m_input.value()
        grid_pattern = self.grid_pattern_input.text().strip()
        
        counts_valid = sum_counts == total
        grid_valid = self.validate_grid_pattern(grid_pattern)
        
        is_valid = counts_valid and grid_valid
        
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(is_valid)


class Haptics_App(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi('layout.ui', self)
        self.resize(1500, 750)
        icon = QtGui.QIcon()
        icon_path = "resources/logo.jpg"

        if os.path.exists(icon_path):
            icon.addPixmap(QtGui.QPixmap(icon_path), QIcon.Mode.Normal, QIcon.State.Off)
            self.setWindowIcon(icon)
        else:
            print(f"Icon file not found at path: {icon_path}")

        self.threadpool = QtCore.QThreadPool()

        # Set main background color
        self.setStyleSheet("background-color: rgb(193, 205, 215);")
        self.widget_2.setStyleSheet("background-color: rgb(193, 205, 215);")

        # Initialize dictionaries to store signals
        self.custom_signals = {}  # Dictionary to store custom signals
        self.signal_templates = {}  # Dictionary to store provided signal templates
        self.imported_signals = {}  # Dictionary to store imported signals

        # Initialize the tree widget
        self.setup_tree_widget()

        # Add matplotlib canvas to the layout
        self.maincanvas = MplCanvas(self.ui.widget, width=5, height=1, dpi=100, app_reference=self)
        self.ui.gridLayout.addWidget(self.maincanvas, 0, 0, 1, 1)

        # Add ActuatorCanvas to the layout with a fixed height
        self.actuator_canvas = ActuatorCanvas(self.ui.widget_2)
        self.actuator_canvas.setFixedHeight(380)  # Set the fixed height here
        self.ui.gridLayout_5.addWidget(self.actuator_canvas, 0, 0, 1, 1)

        # Create a scene for the selection bar
        self.selection_scene = QGraphicsScene()

        # Create the selection bar view and add it to the layout
        self.selection_bar = SelectionBar(self.selection_scene)
        self.selection_view = SelectionBarView(self.selection_scene, self.ui.widget_2)
        self.selection_view.setFixedSize(100, 100)  # Set size and position as needed
        self.ui.gridLayout_5.addWidget(self.selection_view, 0, 0, 1, 1)  # Overlay on the actuator canvas

        # Connect clear button to clear_plot method
        self.ui.pushButton.clicked.connect(self.maincanvas.clear_plot)
        
        # Connect save button to save_current_signal method
        self.ui.pushButton_2.clicked.connect(self.save_current_signal)

        self.signal_counter = 1  # Counter for naming saved signals
        self.actionCreate_New_Chain.triggered.connect(self.create_actuator_branch)

        # Connect the import waveform action to the import_waveform method
        self.ui.actionImport_Waveform.triggered.connect(self.import_waveform)

        # Connect the actuator_added signal to the add_actuator_to_timeline slot
        self.actuator_canvas.actuator_added.connect(self.add_actuator_to_timeline)

        # Setup scroll area for timeline
        self.timeline_layout = QVBoxLayout(self.ui.scrollAreaWidgetContents)

        # Dictionary to store references to timeline widgets
        self.timeline_widgets = {}

        # Connect the properties_changed signal to the update_timeline_actuator slot
        self.actuator_canvas.properties_changed.connect(self.update_timeline_actuator)
        self.actuator_canvas.actuator_deleted.connect(self.remove_actuator_from_timeline)

    def add_actuator_to_timeline(self, new_id, actuator_type, color, x, y):
        # Create a new QWidget to represent the actuator in the timeline
        actuator_widget = QWidget()
        actuator_widget.setStyleSheet(f"background-color: {color};")
        actuator_layout = QHBoxLayout(actuator_widget)
        actuator_label = QLabel(f"{actuator_type} - {new_id}")
        actuator_layout.addWidget(actuator_label)
        
        # Add the new actuator widget to the timeline layout
        self.timeline_layout.addWidget(actuator_widget)

        # Store the reference to the timeline widget
        self.timeline_widgets[new_id] = (actuator_widget, actuator_label)

    def update_timeline_actuator(self, old_actuator_id, new_actuator_id, actuator_type, color):
        if old_actuator_id in self.timeline_widgets:
            actuator_widget, actuator_label = self.timeline_widgets.pop(old_actuator_id)
            actuator_widget.setStyleSheet(f"background-color: {color};")
            actuator_label.setText(f"{actuator_type} - {new_actuator_id}")

            # Store the updated reference with the new ID
            self.timeline_widgets[new_actuator_id] = (actuator_widget, actuator_label)
            
    def remove_actuator_from_timeline(self, actuator_id):
        if actuator_id in self.timeline_widgets:
            actuator_widget, actuator_label = self.timeline_widgets.pop(actuator_id)
            self.timeline_layout.removeWidget(actuator_widget)
            actuator_widget.deleteLater()  # Properly delete the widget

    def import_waveform(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Waveform", "", "JSON Files (*.json);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    data = json.load(file)
                    print(f"JSON Data: {json.dumps(data, indent=2)}")  # Debugging print statement
                    # Assuming the waveform data is under 'value0' and is a list of y-values
                    waveform = self.extract_waveform(data)
                    if waveform is not None:
                        data["data"] = waveform.tolist()
                        self.add_imported_waveform(file_path, data)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import waveform: {e}")

    def add_imported_waveform(self, file_path, waveform_data):
        imports_item = None
        # Find or create the Imports item
        for i in range(self.ui.treeWidget.topLevelItemCount()):
            top_item = self.ui.treeWidget.topLevelItem(i)
            if top_item.text(0) == "Imported Signals":
                imports_item = top_item
                break
        if imports_item is None:
            imports_item = QTreeWidgetItem(self.ui.treeWidget)
            imports_item.setText(0, "Imported Signals")
            imports_item.setToolTip(0, "Imported Signals")

        waveform_name = os.path.basename(file_path)
        child = QTreeWidgetItem(imports_item)
        child.setText(0, waveform_name)
        child.setToolTip(0, waveform_name)
        self.imported_signals[waveform_name] = waveform_data
        child.setFlags(child.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)  # Make the item editable
        child.setData(0, QtCore.Qt.ItemDataRole.UserRole, waveform_name)  # Store the original name

    # No normalization (the one to use ****)
    # def extract_waveform(self, data):
    #     try:
    #         # Extract gain and use it to generate a sine waveform
    #         gain = data["value0"]["m_ptr"]["ptr_wrapper"]["data"]["m_model"]["IOscillator"]["x"]["gain"]
    #         # Generate a simple sine wave using the gain value
    #         t = np.linspace(0, 1, 500)  # Adjust the number of points as needed
    #         waveform = gain * np.sin(2 * np.pi * t)
    #         print(f"Waveform length: {len(waveform)}")  # Debugging print statement
    #         return waveform
    #     except KeyError as e:
    #         print(f"KeyError: {e}")
    #         return None
        
    def extract_waveform(self, data):
        try:
            # Extract gain and use it to generate a sine waveform
            gain = data["value0"]["m_ptr"]["ptr_wrapper"]["data"]["m_model"]["IOscillator"]["x"]["gain"]
            
            # Generate a simple sine wave using the gain value
            t = np.linspace(0, 1, 500)  # Adjust the number of points as needed
            waveform = gain * np.sin(2 * np.pi * t)
            
            # Normalize the waveform from -500 to 500 range to -1 to 1
            max_val = 500
            min_val = -500
            normalized_waveform = 2 * (waveform - min_val) / (max_val - min_val) - 1
            
            print(f"Normalized Waveform length: {len(normalized_waveform)}")  # Debugging print statement
            return normalized_waveform
        except KeyError as e:
            print(f"KeyError: {e}")
            return None


    def create_actuator_branch(self):
        dialog = CreateBranchDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            num_actuators = dialog.num_actuators_input.value()
            lra_count = dialog.lra_input.value()
            vca_count = dialog.vca_input.value()
            m_count = dialog.m_input.value()
            grid_pattern = dialog.grid_pattern_input.text()

            self.actuator_canvas.create_actuator_branch(
                num_actuators, lra_count, vca_count, m_count, grid_pattern)

    def setup_tree_widget(self):
        tree = self.ui.treeWidget
        tree.setHeaderHidden(True)
        tree.setStyleSheet("""
            QTreeWidget {
                background-color: rgb(134, 150, 167);
                color: rgb(240, 235, 229);
            }
            QToolTip {
                color: rgb(134, 150, 167);  /* Text color */
                background-color: rgba(0, 0, 0, 128);  /* Black background with transparency */
                font-weight: bold;  /* Bold text */
            }
        """)
        tree.setDragEnabled(True)
        tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tree.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
        tree.setToolTipDuration(2000)  # Set tooltip duration to 2 seconds

        # Create top-level items
        oscillators = QTreeWidgetItem(tree)
        oscillators.setText(0, "Oscillators")
        oscillators.setToolTip(0, "Oscillators")  # Set tooltip

        envelopes = QTreeWidgetItem(tree)
        envelopes.setText(0, "Envelopes")
        envelopes.setToolTip(0, "Envelopes")  # Set tooltip

        self.customizes = QTreeWidgetItem(tree)
        self.customizes.setText(0, "Customized Signals")
        self.customizes.setToolTip(0, "Customized Signals")  # Set tooltip

        self.imports = QTreeWidgetItem(tree)
        self.imports.setText(0, "Imported Signals")
        self.imports.setToolTip(0, "Imported Signals")  # Set tooltip

        # Add child items to "Oscillators"
        osc_items = ["Sine", "Square", "Saw", "Triangle", "Chirp", "FM", "PWM", "Noise"]
        for item in osc_items:
            child = QTreeWidgetItem(oscillators)
            child.setText(0, item)
            child.setToolTip(0, item)  # Set tooltip
            self.signal_templates[item] = self.generate_signal(item)

        # Add child items to "Envelopes"
        env_items = ["Envelope", "Keyed Envelope", "ASR", "ADSR", "Exponential Decay", "PolyBezier", "Signal Envelope"]
        for item in env_items:
            child = QTreeWidgetItem(envelopes)
            child.setText(0, item)
            child.setToolTip(0, item)  # Set tooltip
            self.signal_templates[item] = self.generate_signal(item)

        # Expand all items by default
        tree.expandAll()

        # Connect tree widget item selection to the plotting function
        tree.itemClicked.connect(self.on_tree_item_clicked)

        # Connect the itemChanged signal to handle renaming
        tree.itemChanged.connect(self.on_tree_item_changed)

        # Enable context menu
        tree.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        tree.customContextMenuRequested.connect(self.on_custom_context_menu)

    @pyqtSlot(QTreeWidgetItem, int)
    def on_tree_item_clicked(self, item, column):
        signal_type = item.text(column)
        if signal_type in self.custom_signals:  # Check if it's a custom signal
            custom_signal = self.custom_signals.get(signal_type)
            if custom_signal is not None:
                self.maincanvas.add_signal(custom_signal, combine=False)
        elif signal_type in self.signal_templates:  # Check if it's a provided signal template
            template_signal = self.signal_templates.get(signal_type)
            if template_signal is not None:
                self.maincanvas.add_signal(template_signal, combine=False)
        elif signal_type in self.imported_signals:  # Check if it's an imported signal
            imported_signal = self.imported_signals.get(signal_type)
            if imported_signal is not None:
                self.maincanvas.add_signal(imported_signal, combine=False)
        else:
            self.add_signal(signal_type, combine=False)  # Show the signal itself when clicked

    def generate_signal(self, signal_type):
        base_signal = {
            "value0": {
                "gain": 1.0,
                "bias": 0.0,
                "m_ptr": {
                    "polymorphic_id": 2147483649,
                    "polymorphic_name": f"tact::Signal::Model<tact::{signal_type}>",
                    "ptr_wrapper": {
                        "valid": 1,
                        "data": {
                            "Concept": {},
                            "m_model": {
                                "IOscillator": {
                                    "x": {
                                        "gain": 628.3185307179587,
                                        "bias": 0.0,
                                        "m_ptr": {
                                            "polymorphic_id": 2147483650,
                                            "polymorphic_name": "tact::Signal::Model<tact::Time>",
                                            "ptr_wrapper": {
                                                "valid": 1,
                                                "data": {
                                                    "Concept": {},
                                                    "m_model": {}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "data": []
        }

        t = np.linspace(0, 1, 500).tolist()  # Convert numpy array to list
        if signal_type == "Sine":
            base_signal["data"] = np.sin(2 * np.pi * 10 * np.array(t)).tolist()
        elif signal_type == "Square":
            base_signal["data"] = np.sign(np.sin(2 * np.pi * 10 * np.array(t))).tolist()
        elif signal_type == "Saw":
            base_signal["data"] = (2 * (np.array(t) - np.floor(np.array(t) + 0.5))).tolist()
        elif signal_type == "Triangle":
            base_signal["data"] = (2 * np.abs(2 * (np.array(t) - np.floor(np.array(t) + 0.5))) - 1).tolist()
        elif signal_type == "Chirp":
            base_signal["data"] = (np.sin(2 * np.pi * np.array(t)**2)).tolist()
        elif signal_type == "FM":
            base_signal["data"] = (np.sin(2 * np.pi * (10 * np.array(t) + np.sin(2 * np.pi * 0.5 * np.array(t))))).tolist()
        elif signal_type == "PWM":
            base_signal["data"] = (np.where(np.sin(2 * np.pi * 10 * np.array(t)) >= 0, 1, -1)).tolist()
        elif signal_type == "Noise":
            base_signal["data"] = np.random.normal(0, 1, len(t)).tolist()
        elif signal_type == "Envelope":
            base_signal["data"] = (np.linspace(0, 1, 500) * np.sin(2 * np.pi * 5 * np.array(t))).tolist()
        elif signal_type == "Keyed Envelope":
            base_signal["data"] = (np.sin(2 * np.pi * 5 * np.array(t)) * np.exp(-3 * np.array(t))).tolist()
        elif signal_type == "ASR":
            base_signal["data"] = (np.piecewise(np.array(t), [np.array(t) < 0.3, np.array(t) >= 0.3], [lambda t: 3.33 * t, 1])).tolist()
        elif signal_type == "ADSR":
            base_signal["data"] = (np.piecewise(np.array(t), [np.array(t) < 0.1, np.array(t) < 0.2, np.array(t) < 0.5, np.array(t) < 0.7, np.array(t) >= 0.7], [lambda t: 10 * t, lambda t: 1 - 5 * (t - 0.1), 0.5, lambda t: 0.5 - 0.25 * (t - 0.5), 0.25])).tolist()
        elif signal_type == "Exponential Decay":
            base_signal["data"] = (np.exp(-5 * np.array(t))).tolist()
        elif signal_type == "PolyBezier":
            base_signal["data"] = (np.array(t)**3 - 3 * np.array(t)**2 + 3 * np.array(t)).tolist()
        elif signal_type == "Signal Envelope":
            base_signal["data"] = (np.abs(np.sin(2 * np.pi * 3 * np.array(t)))).tolist()
        elif signal_type in self.custom_signals:  # Check if it's a custom signal
            base_signal["data"] = self.custom_signals.get(signal_type, {"data": np.zeros_like(t).tolist()})["data"]
        else:
            base_signal["data"] = np.zeros_like(t).tolist()

        return base_signal

    def add_signal(self, signal_type, combine):
        new_signal = self.generate_signal(signal_type)
        print(new_signal)
        self.maincanvas.add_signal(new_signal, combine=combine)

    def signal_exists(self, signal):
        for existing_signal in self.custom_signals.values():
            if np.array_equal(existing_signal, signal):
                return True
        for existing_signal in self.signal_templates.values():
            if np.array_equal(existing_signal, signal):
                return True
        return False

    def save_current_signal(self):
        if self.maincanvas.current_signal is not None:
            signal_data = {
                "value0": {
                    "gain": 1.0,
                    "bias": 0.0,
                    "m_ptr": {
                        "polymorphic_id": 2147483649,
                        "polymorphic_name": f"tact::Signal::Model<tact::Custom>",
                        "ptr_wrapper": {
                            "valid": 1,
                            "data": {
                                "Concept": {},
                                "m_model": {
                                    "IOscillator": {
                                        "x": {
                                            "gain": 628.3185307179587,
                                            "bias": 0.0,
                                            "m_ptr": {
                                                "polymorphic_id": 2147483650,
                                                "polymorphic_name": "tact::Signal::Model<tact::Time>",
                                                "ptr_wrapper": {
                                                    "valid": 1,
                                                    "data": {
                                                        "Concept": {},
                                                        "m_model": {}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "data": self.maincanvas.current_signal.tolist()
            }
            if self.signal_exists(signal_data):
                QMessageBox.information(self, "Reminder", "Signal Already Exist!", QMessageBox.StandardButton.Ok)
            else:
                signal_name = f"Signal {self.signal_counter}"
                self.signal_counter += 1
                child = QTreeWidgetItem(self.customizes)
                child.setText(0, signal_name)
                child.setToolTip(0, signal_name)  # Set tooltip
                child.setFlags(child.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)  # Make the item editable
                child.setData(0, QtCore.Qt.ItemDataRole.UserRole, signal_name)  # Store the original name
                self.customizes.addChild(child)
                self.custom_signals[signal_name] = signal_data  # Save the signal data

    @pyqtSlot(QTreeWidgetItem, int)
    def on_tree_item_changed(self, item, column):
        old_name = item.data(column, QtCore.Qt.ItemDataRole.UserRole)
        new_name = item.text(column)
        if item.parent() == self.customizes and old_name in self.custom_signals:
            self.custom_signals[new_name] = self.custom_signals.pop(old_name)
            item.setData(column, QtCore.Qt.ItemDataRole.UserRole, new_name)
            item.setToolTip(0, new_name)  # Update tooltip
        elif item.parent() and item.parent().text(0) == "Imported Signals" and old_name in self.imported_signals:
            self.imported_signals[new_name] = self.imported_signals.pop(old_name)
            item.setData(column, QtCore.Qt.ItemDataRole.UserRole, new_name)
            item.setToolTip(0, new_name)  # Update tooltip

    def delete_tree_item(self, item):
        signal_name = item.text(0)
        if item.parent() == self.customizes:
            if signal_name in self.custom_signals:
                del self.custom_signals[signal_name]
            index = self.customizes.indexOfChild(item)
            if index != -1:
                self.customizes.takeChild(index)
        elif item.parent() and item.parent().text(0) == "Imported Signals":
            if signal_name in self.imported_signals:
                del self.imported_signals[signal_name]
            index = item.parent().indexOfChild(item)
            if index != -1:
                item.parent().takeChild(index)
                
    @pyqtSlot(QtCore.QPoint)
    def on_custom_context_menu(self, point):
        item = self.ui.treeWidget.itemAt(point)
        if item:
            menu = QtWidgets.QMenu(self)
            delete_action = menu.addAction("Delete")
            rename_action = menu.addAction("Rename")

            action = menu.exec(self.ui.treeWidget.mapToGlobal(point))

            if action == delete_action:
                self.delete_tree_item(item)
            elif action == rename_action:
                self.ui.treeWidget.editItem(item)

    def delete_custom_signal(self, item):
        signal_name = item.text(0)
        if signal_name in self.custom_signals:
            del self.custom_signals[signal_name]
        index = self.customizes.indexOfChild(item)
        if index != -1:
            self.customizes.takeChild(index)


class Worker(QtCore.QRunnable):
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        self.function(*self.args, **self.kwargs)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = Haptics_App()
    mainWindow.show()
    sys.exit(app.exec())
