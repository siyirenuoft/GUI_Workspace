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
        self.axes.plot(x, y, color=spine_color)
        
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

    def add_signal(self, new_signal, combine=False):
        if combine and self.current_signal is not None:
            # Ensure both signals are of the same data type before adding
            self.current_signal = self.current_signal.astype(np.float64)
            new_signal = new_signal.astype(np.float64)
            self.current_signal += new_signal
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
        self.app_reference.add_signal(signal_type, combine=True)  # Use app_reference with combine=True

# Define the ACTUATOR_CONFIG dictionary
ACTUATOR_CONFIG = {
    "LRA": {
        "text_vertical_offset": 0,
        "text_horizontal_offset": 0,
        "font_size_factor": 0.4,
        "min_font_size": 8,
        "max_font_size": 16
    },
    "VCA": {
        "text_vertical_offset": 0,
        "text_horizontal_offset": 0,
        "font_size_factor": 0.4,
        "min_font_size": 8,
        "max_font_size": 16
    },
    "M": {
        "text_vertical_offset": 0,
        "text_horizontal_offset": 0,
        "font_size_factor": 0.4,
        "min_font_size": 8,
        "max_font_size": 16
    }
}

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
        return QRectF(-self.size / 2, -self.size / 2, self.size, self.size)

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
        orig_pos = self.pos()
        super().mouseMoveEvent(event)
        if not self.scene().sceneRect().contains(self.sceneBoundingRect()):
            self.setPos(orig_pos)
    
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

class ActuatorCanvas(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHints(QPainter.RenderHint.Antialiasing)

        self.actuators = []
        self.branch_colors = {}

        # Set background color to rgb(134, 150, 167)
        self.setBackgroundBrush(QBrush(QColor(134, 150, 167)))
        self.scene.setBackgroundBrush(QBrush(QColor(134, 150, 167)))
        self.setSceneRect(-1000, -1000, 2000, 2000)  # Large scene to allow panning

        self.canvas_rect = QRectF(0, 0, 600, 400)
        self.colored_rect_item = None  # Changed to colored_rect_item
        self.scale_line = None
        self.scale_text = None
        self.update_canvas_visuals()

        self.setMouseTracking(True)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        self.panning = False
        self.last_pan_point = QPointF()
        self.actuator_size = 20

    def update_canvas_visuals(self):
        if self.colored_rect_item:
            self.scene.removeItem(self.colored_rect_item)
        
        # Set canvas color to a custom RGB value, e.g., (255, 0, 0) for red
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
        self.scale_text.setPos(self.canvas_rect.left() + 50, self.canvas_rect.bottom() - 5)
        self.scale_line.setZValue(1000)
        self.scale_text.setZValue(1000)

    def update_scale_position(self):
        if self.scale_line and self.scale_text:
            self.scale_line.setLine(self.canvas_rect.left() + 10, self.canvas_rect.bottom() - 10,
                                    self.canvas_rect.left() + 110, self.canvas_rect.bottom() - 10)
            self.scale_text.setPos(self.canvas_rect.left() + 50, self.canvas_rect.bottom() - 5)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = self.mapToScene(event.pos())
            if self.canvas_rect.contains(pos):
                item = self.itemAt(event.pos())
                if isinstance(item, Actuator):
                    super().mousePressEvent(event)
                else:
                    self.add_actuator(pos.x(), pos.y())
        elif event.button() == Qt.MouseButton.RightButton:
            item = self.itemAt(event.pos())
            if isinstance(item, Actuator):
                self.show_context_menu(item, event.pos())
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.panning = True
            self.last_pan_point = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.panning:
            delta = event.pos() - self.last_pan_point
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self.last_pan_point = event.pos()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

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
            self.branch_colors[branch] = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
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

        # Initialize the tree widget
        self.setup_tree_widget()

        # Add matplotlib canvas to the layout
        self.maincanvas = MplCanvas(self.ui.widget, width=5, height=1, dpi=100, app_reference=self)
        self.ui.gridLayout.addWidget(self.maincanvas, 0, 0, 1, 1)

        # Add ActuatorCanvas to the layout with a fixed height
        self.actuator_canvas = ActuatorCanvas(self.ui.widget_2)
        self.actuator_canvas.setFixedHeight(380)  # Set the fixed height here
        self.ui.gridLayout_5.addWidget(self.actuator_canvas, 0, 0, 1, 1)   

        # Connect clear button to clear_plot method
        self.ui.pushButton.clicked.connect(self.maincanvas.clear_plot)
        
        # Connect save button to save_current_signal method
        self.ui.pushButton_2.clicked.connect(self.save_current_signal)

        self.signal_counter = 1  # Counter for naming saved signals

    def setup_tree_widget(self):
        tree = self.ui.treeWidget
        tree.setHeaderHidden(True)
        tree.setStyleSheet("""
            QTreeWidget {
                background-color: rgb(134, 150, 167);
                color: rgb(240, 235, 229);
            }
            QTreeWidget::item {
                background-color: transparent;
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
        else:
            self.add_signal(signal_type, combine=False)  # Show the signal itself when clicked

    def generate_signal(self, signal_type):
        t = np.linspace(0, 1, 500)
        if signal_type == "Sine":
            return np.sin(2 * np.pi * 10 * t)
        elif signal_type == "Square":
            return np.sign(np.sin(2 * np.pi * 10 * t))
        elif signal_type == "Saw":
            return 2 * (t - np.floor(t + 0.5))
        elif signal_type == "Triangle":
            return 2 * np.abs(2 * (t - np.floor(t + 0.5))) - 1
        elif signal_type == "Chirp":
            return np.sin(2 * np.pi * t**2)
        elif signal_type == "FM":
            return np.sin(2 * np.pi * (10 * t + np.sin(2 * np.pi * 0.5 * t)))
        elif signal_type == "PWM":
            return np.where(np.sin(2 * np.pi * 10 * t) >= 0, 1, -1)
        elif signal_type == "Noise":
            return np.random.normal(0, 1, len(t))
        elif signal_type == "Envelope":
            return np.linspace(0, 1, 500) * np.sin(2 * np.pi * 5 * t)
        elif signal_type == "Keyed Envelope":
            return np.sin(2 * np.pi * 5 * t) * np.exp(-3 * t)
        elif signal_type == "ASR":
            return np.piecewise(t, [t < 0.3, t >= 0.3], [lambda t: 3.33 * t, 1])
        elif signal_type == "ADSR":
            return np.piecewise(t, [t < 0.1, t < 0.2, t < 0.5, t < 0.7, t >= 0.7], [lambda t: 10 * t, lambda t: 1 - 5 * (t - 0.1), 0.5, lambda t: 0.5 - 0.25 * (t - 0.5), 0.25])
        elif signal_type == "Exponential Decay":
            return np.exp(-5 * t)
        elif signal_type == "PolyBezier":
            return t**3 - 3 * t**2 + 3 * t
        elif signal_type == "Signal Envelope":
            return np.abs(np.sin(2 * np.pi * 3 * t))
        elif signal_type in self.custom_signals:  # Check if it's a custom signal
            return self.custom_signals.get(signal_type, np.zeros_like(t))
        else:
            return np.zeros_like(t)

    def add_signal(self, signal_type, combine):
        new_signal = self.generate_signal(signal_type)
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
            if self.signal_exists(self.maincanvas.current_signal):
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
                self.custom_signals[signal_name] = self.maincanvas.current_signal.copy()  # Save the signal data

    @pyqtSlot(QTreeWidgetItem, int)
    def on_tree_item_changed(self, item, column):
        old_name = item.data(column, QtCore.Qt.ItemDataRole.UserRole)
        new_name = item.text(column)
        if old_name and old_name in self.custom_signals:
            self.custom_signals[new_name] = self.custom_signals.pop(old_name)
            item.setData(column, QtCore.Qt.ItemDataRole.UserRole, new_name)
            item.setToolTip(0, new_name)  # Update tooltip

    @pyqtSlot(QtCore.QPoint)
    def on_custom_context_menu(self, point):
        item = self.ui.treeWidget.itemAt(point)
        if item and item.parent() == self.customizes:
            menu = QtWidgets.QMenu(self)
            delete_action = menu.addAction("Delete")
            rename_action = menu.addAction("Rename")

            action = menu.exec(self.ui.treeWidget.mapToGlobal(point))

            if action == delete_action:
                self.delete_custom_signal(item)
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
