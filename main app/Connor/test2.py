import sys
import csv
from PyQt6.QtGui import QAction, QColor, QPen, QPainter, QBrush, QWheelEvent
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMenuBar, QFileDialog, 
                             QVBoxLayout, QWidget, QDialog, QLineEdit, QPushButton, QLabel,
                             QGraphicsView, QGraphicsScene, QGraphicsItem, QMenu, QFormLayout,
                             QComboBox, QHBoxLayout, QCheckBox, QGraphicsRectItem, QSlider,
                             QButtonGroup, QRadioButton, QSpinBox, QDialogButtonBox)
from PyQt6.QtCore import Qt, QRectF, QPointF
import pyqtgraph as pg
import numpy as np
import random


ACTUATOR_CONFIG = {
    "LRA": {
        "text_vertical_offset": -1,
        "text_horizontal_offset": 0.5,
        "font_size_factor": 0.9,
        "min_font_size": 6,
        "max_font_size": 12
    },
    "VCA": {
        "text_vertical_offset": -1,
        "text_horizontal_offset": 0.5,
        "font_size_factor": 0.9,
        "min_font_size": 6,
        "max_font_size": 12
    },
    "M": {
        "text_vertical_offset": -1,
        "text_horizontal_offset": 0.5,
        "font_size_factor": 0.9,
        "min_font_size": 6,
        "max_font_size": 12
    }
}

# Predefined color list for actuators (20 colors)
COLOR_LIST = [
    QColor(255, 0, 0),  # Red
    QColor(0, 255, 0),  # Green
    QColor(0, 0, 255),  # Blue
    QColor(255, 255, 0),  # Yellow
    QColor(255, 0, 255),  # Magenta
    QColor(0, 255, 255),  # Cyan
    QColor(128, 0, 0),  # Maroon
    QColor(128, 128, 0),  # Olive
    QColor(0, 128, 0),  # Dark Green
    QColor(128, 0, 128),  # Purple
    QColor(0, 128, 128),  # Teal
    QColor(0, 0, 128),  # Navy
    QColor(192, 192, 192),  # Silver
    QColor(128, 128, 128),  # Gray
    QColor(255, 165, 0),  # Orange
    QColor(255, 20, 147),  # Deep Pink
    QColor(75, 0, 130),  # Indigo
    QColor(173, 255, 47),  # Green Yellow
    QColor(0, 255, 127),  # Spring Green
    QColor(70, 130, 180)  # Steel Blue
]

# Function to generate a contrasting color
def generate_contrasting_color(existing_colors):
    while True:
        new_color = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        contrast = all(abs(new_color.red() - color.red()) + abs(new_color.green() - color.green()) + abs(new_color.blue() - color.blue()) > 200 for color in existing_colors)
        if contrast:
            return new_color


class Actuator(QGraphicsItem):
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
            icon = Actuator(0, 0, 20, QColor(255, 255, 255), act_type, act_type)
            icon.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            icon.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
            icon.setPos(0, i * 30)
            self.selection_icons.append(icon)
            self.scene.addItem(icon)

    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(Qt.GlobalColor.gray))
        painter.drawRect(self.boundingRect())

class ActuatorCanvas(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHints(QPainter.RenderHint.Antialiasing)

        self.actuators = []
        self.branch_colors = {}
        self.color_index = 0  # Index for the color list

        self.setBackgroundBrush(QBrush(Qt.GlobalColor.lightGray))
        self.setSceneRect(-1000, -1000, 2000, 2000)  # Large scene to allow panning
        
        self.canvas_rect = QRectF(0, 0, 400, 300)
        self.white_rect_item = None
        self.scale_line = None
        self.scale_text = None
        self.update_canvas_visuals()

        self.setMouseTracking(True)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        self.panning = False
        self.last_pan_point = QPointF()
        self.actuator_size = 20

        self.selection_bar = SelectionBar(self.scene)
        self.scene.addItem(self.selection_bar)


    def is_drop_allowed(self, pos):
        return self.canvas_rect.contains(pos)


    def update_canvas_visuals(self):
        if self.white_rect_item:
            self.scene.removeItem(self.white_rect_item)
        
        self.white_rect_item = self.scene.addRect(self.canvas_rect, QPen(Qt.GlobalColor.black), QBrush(Qt.GlobalColor.white))
        self.white_rect_item.setZValue(-999)

        if self.scale_line:
            self.scene.removeItem(self.scale_line)
        if self.scale_text:
            self.scene.removeItem(self.scale_text)

        self.scale_line = self.scene.addLine(self.canvas_rect.left() + 10, self.canvas_rect.bottom() - 10,
                                             self.canvas_rect.left() + 110, self.canvas_rect.bottom() - 10,
                                             QPen(Qt.GlobalColor.black, 2))
        self.scale_text = self.scene.addText("100 mm")
        self.scale_text.setPos(self.canvas_rect.left() + 50, self.canvas_rect.bottom() - 5)
        self.scale_line.setZValue(1000)
        self.scale_text.setZValue(1000)

    def update_scale_position(self):
        if self.scale_line and self.scale_text:
            self.scale_line.setLine(self.canvas_rect.left() + 10, self.canvas_rect.bottom() - 10,
                                    self.canvas_rect.left() + 110, self.canvas_rect.bottom() - 10)
            self.scale_text.setPos(self.canvas_rect.left() + 50, self.canvas_rect.bottom() - 5)

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, Actuator) and item in self.selection_bar.selection_icons:
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

        # Update the predecessor's successor
        if predecessor:
            for act in self.actuators:
                if act.id == predecessor:
                    act.successor = new_id
                    break

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

class CanvasSizeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adjust Canvas Size")
        self.layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        self.width_input = QLineEdit()
        self.height_input = QLineEdit()
        form_layout.addRow("Width (mm):", self.width_input)
        form_layout.addRow("Height (mm):", self.height_input)

        self.layout.addLayout(form_layout)

        button = QPushButton("OK")
        button.clicked.connect(self.accept)
        self.layout.addWidget(button)


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

        # Add new menu item
        create_branch_action = QAction("Create Actuator Branch", self)
        create_branch_action.triggered.connect(self.create_actuator_branch)
        file_menu.addAction(create_branch_action)

    def new_workspace(self):
        self.parent().actuator_canvas.clear_canvas()

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
    
    def create_actuator_branch(self):
        dialog = CreateBranchDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            num_actuators = dialog.num_actuators_input.value()
            lra_count = dialog.lra_input.value()
            vca_count = dialog.vca_input.value()
            m_count = dialog.m_input.value()
            grid_pattern = dialog.grid_pattern_input.text()

            self.parent().actuator_canvas.create_actuator_branch(
                num_actuators, lra_count, vca_count, m_count, grid_pattern)



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

        self.adjust_canvas_button = QPushButton("Adjust Canvas Size")
        self.adjust_canvas_button.clicked.connect(self.adjust_canvas_size)
        self.layout.addWidget(self.adjust_canvas_button)

        self.multitrack_editor = QWidget()
        self.layout.addWidget(self.multitrack_editor)

    def update_waveform(self, data):
        self.waveform_canvas.update_plot(data)

    def adjust_canvas_size(self):
        dialog = CanvasSizeDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                width = int(dialog.width_input.text())
                height = int(dialog.height_input.text())
                self.actuator_canvas.set_canvas_size(width, height)
            except ValueError:
                print("Invalid input. Please enter valid integer values for width and height.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())