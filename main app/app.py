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

def to_subscript(text):
    subscript_map = str.maketrans('0123456789', '₀₁₂₃₄₅₆₇₈₉')
    return text.translate(subscript_map)

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

    def mousePressEvent(self, event):
        pass  # Disable mouse press event handling

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
        
        if self.current_signal is None:
            self.current_signal = new_signal
        else:
            # If signals have different lengths, repeat the shorter one to match the longer one
            if len(self.current_signal) > len(new_signal):
                repeat_factor = len(self.current_signal) // len(new_signal) + 1
                new_signal = np.tile(new_signal, repeat_factor)[:len(self.current_signal)]
            elif len(self.current_signal) < len(new_signal):
                repeat_factor = len(new_signal) // len(self.current_signal) + 1
                self.current_signal = np.tile(self.current_signal, repeat_factor)[:len(new_signal)]
            
            if combine:
                self.current_signal = self.current_signal + new_signal
            else:
                self.current_signal = new_signal

        t = np.linspace(0, 1, len(self.current_signal)) * (len(self.current_signal) / 500)  # Adjust t for correct duration
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

        # Determine if the dropped signal is imported
        if signal_type in self.app_reference.imported_signals:
            customized_signal = self.app_reference.imported_signals[signal_type]
            self.add_signal(customized_signal, combine=True)
        else:
            parameters = {}  # Dictionary to store parameters

            # Handle oscillators
            if signal_type in ["Sine", "Square", "Saw", "Triangle", "Chirp", "FM", "PWM", "Noise"]:
                dialog = OscillatorDialog(signal_type, self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    config = dialog.get_config()
                    parameters = config  # Store the parameters
                    customized_signal = self.generate_custom_oscillator_json(signal_type, config["frequency"], config["rate"])
                    self.app_reference.update_status_bar(signal_type, parameters)  # Update the status bar

            # Handle envelopes
            elif signal_type in ["Envelope", "Keyed Envelope", "ASR", "ADSR", "Exponential Decay", "PolyBezier", "Signal Envelope"]:
                dialog = EnvelopeDialog(signal_type, self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    config = dialog.get_config()
                    parameters = config  # Store the parameters
                    customized_signal = self.generate_custom_envelope_json(signal_type, config["duration"], config["amplitude"])
                    self.app_reference.update_status_bar(signal_type, parameters)  # Update the status bar

            # If a customized signal was created, add it to the plot
            if customized_signal:
                self.add_signal(customized_signal, combine=True)

    def generate_custom_envelope_json(self, signal_type, duration, amplitude):
        num_samples = int(duration * 500)  # Adjust the number of samples to match the duration
        t = np.linspace(0, duration, num_samples)
        # t = np.linspace(0, duration, 500)  # Ensure that the time vector spans the entire duration

        if signal_type == "Envelope":
            data = (amplitude * np.sin(2 * np.pi * 5 * t)).tolist()
        elif signal_type == "Keyed Envelope":
            data = (amplitude * np.sin(2 * np.pi * 5 * t) * np.exp(-3 * t)).tolist()
        elif signal_type == "ASR":
            data = np.piecewise(t, [t < 0.3 * duration, t >= 0.3 * duration],
                                [lambda t: amplitude * (t / (0.3 * duration)), amplitude]).tolist()
        elif signal_type == "ADSR":
            data = np.piecewise(t, [t < 0.1 * duration, t < 0.2 * duration, t < 0.5 * duration, t < 0.7 * duration, t >= 0.7 * duration],
                                [lambda t: amplitude * (t / (0.1 * duration)),
                                lambda t: amplitude * (1 - 5 * (t - 0.1 * duration) / duration),
                                0.5 * amplitude,
                                lambda t: 0.5 * amplitude - 0.25 * amplitude * (t - 0.5 * duration) / duration,
                                0.25 * amplitude]).tolist()
        elif signal_type == "Exponential Decay":
            data = (amplitude * np.exp(-5 * t / duration)).tolist()  # Scale the decay based on duration
        elif signal_type == "PolyBezier":
            data = (amplitude * (t ** 3 - 3 * t ** 2 + 3 * t)).tolist()
        elif signal_type == "Signal Envelope":
            data = (amplitude * np.abs(np.sin(2 * np.pi * 3 * t))).tolist()
        else:
            data = np.zeros_like(t).tolist()

        return {
            "value0": {
                "gain": amplitude,
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
                                        "gain": 1.0,
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
            "data": data
        }


    def generate_custom_oscillator_json(self, signal_type, frequency, rate):
        t = np.linspace(0, 1, 500)
        if signal_type == "Sine":
            data = np.sin(2 * np.pi * frequency * t + rate * t).tolist()
        elif signal_type == "Square":
            data = np.sign(np.sin(2 * np.pi * frequency * t)).tolist()
        elif signal_type == "Saw":
            data = (2 * (t * frequency - np.floor(t * frequency + 0.5))).tolist()
        elif signal_type == "Triangle":
            data = (2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1).tolist()
        elif signal_type == "Chirp":
            data = np.sin(2 * np.pi * (frequency * t + 0.5 * rate * t**2)).tolist()
        elif signal_type == "FM":
            data = np.sin(2 * np.pi * (frequency * t + rate * np.sin(2 * np.pi * frequency * t))).tolist()
        elif signal_type == "PWM":
            data = np.where(np.sin(2 * np.pi * frequency * t) >= 0, 1, -1).tolist()
        elif signal_type == "Noise":
            data = np.random.normal(0, 1, len(t)).tolist()
        else:
            data = np.zeros_like(t).tolist()  # Default for unsupported types

        return {
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
                                        "gain": frequency * 2 * np.pi,
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
            "data": data
        }


class PreviewCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=1, dpi=100, app_reference=None):
        self.app_reference = app_reference  # Reference to Haptics_App
        bg_color = (134/255, 150/255, 167/255)  # Same background color as MplCanvas
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor=bg_color)
        self.axes = self.fig.add_axes([0.1, 0.1, 0.8, 0.8])  # Use add_axes to create a single plot
        self.axes.set_facecolor(bg_color)

        # Convert RGB to rgba using matplotlib.colors.to_rgba
        spine_color = to_rgba((240/255, 235/255, 229/255))

        # Hide x-axis and y-axis labels, ticks, and tick labels
        self.axes.xaxis.set_visible(False)
        self.axes.yaxis.set_visible(False)

        # Set spine colors (canvas border)
        spine_color = to_rgba((240/255, 235/255, 229/255))
        for spine in self.axes.spines.values():
            spine.set_color(spine_color)
            spine.set_linewidth(1)  # Set border width

        # # Move x-axis label to the right side
        # self.set_custom_xlabel('Time (s)', fontsize=9.5, color=spine_color)  # Custom method for xlabel

        super(PreviewCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.setStyleSheet("background-color: rgb(134, 150, 167); color: spine_color;")
        self.fig.tight_layout()

        # Initialize the canvas size to match layout.ui
        # self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

    def plot_default_signal(self, signal_data):
        self.axes.clear()

        # Define the color for the signal line
        spine_color = to_rgba((240/255, 235/255, 229/255))

        if signal_data is not None and "data" in signal_data:
            t = np.linspace(0, 1, len(signal_data["data"]))
            self.axes.plot(t, signal_data["data"], color=spine_color)  # Use spine_color for the line
        else:
            # Clear the plot if signal_data is None or invalid
            self.axes.clear()
        self.draw()

    def mousePressEvent(self, event):
        pass  # Disable mouse press event handling

    def dragEnterEvent(self, event):
        event.ignore()  # Disable drag event

    def dropEvent(self, event):
        event.ignore()  # Disable drop event

class OscillatorDialog(QDialog):
    def __init__(self, signal_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Customize {signal_type} Signal")
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        self.frequency_input = QDoubleSpinBox()
        self.frequency_input.setRange(0, 1000)  # Adjust range as needed
        self.frequency_input.setValue(10)  # Default value
        form_layout.addRow("Frequency (Hz):", self.frequency_input)
        
        self.rate_input = QDoubleSpinBox()
        self.rate_input.setRange(0, 1000)  # Adjust range as needed
        self.rate_input.setValue(1)  # Default value
        form_layout.addRow("Rate:", self.rate_input)
        
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_config(self):
        return {
            "frequency": self.frequency_input.value(),
            "rate": self.rate_input.value()
        }

class EnvelopeDialog(QDialog):
    def __init__(self, signal_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Customize {signal_type} Signal")
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()

        # Configure the duration input
        self.duration_input = QDoubleSpinBox()
        self.duration_input.setRange(0, 1000)  # Set a reasonable upper limit for duration
        self.duration_input.setValue(1)  # Default value
        self.duration_input.setDecimals(2)  # Allow up to two decimal places
        self.duration_input.setSingleStep(0.1)  # Increment in 0.1s steps
        form_layout.addRow("Duration (s):", self.duration_input)

        # Configure the amplitude input
        self.amplitude_input = QDoubleSpinBox()
        self.amplitude_input.setRange(-1000, 1000)  # Allow amplitude to be any value between -10 and 10
        self.amplitude_input.setValue(1)  # Default value
        self.amplitude_input.setDecimals(2)  # Allow up to two decimal places
        self.amplitude_input.setSingleStep(0.1)  # Increment in 0.1 steps
        form_layout.addRow("Amplitude:", self.amplitude_input)
        
        layout.addLayout(form_layout)
        
        # OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_config(self):
        return {
            "duration": self.duration_input.value(),
            "amplitude": self.amplitude_input.value()
        }

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

class ActuatorSignalHandler(QObject):
    clicked = pyqtSignal(str)  # Signal to indicate actuator is clicked
    properties_changed = pyqtSignal(str, str, str)  # Signal to indicate properties change: id, type, color


    def __init__(self, actuator_id, parent=None):
        super().__init__(parent)
        self.actuator_id = actuator_id


class Actuator(QGraphicsItem):
    # properties_changed = pyqtSignal(str, str, str)  # Signal to indicate properties change: id, type, color
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

        # Create a signal handler for this actuator
        self.signal_handler = ActuatorSignalHandler(self.id)

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
            (QColor(0, 255, 255), "Cyan"),
            (QColor(225,127,147), "bbPink")
        ]
        for qcolor, name in colors:
            if qcolor == color:
                return name
        return "Unknown"

    def boundingRect(self):
        return QRectF(-self.size/2, -self.size/2, self.size, self.size)

    def paint(self, painter, option, widget):
        # Clear any previous drawing to avoid overlap
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))

        # Draw the actuator shape based on its type (without the highlight)
        if self.actuator_type == "LRA":
            painter.drawEllipse(self.boundingRect())
        elif self.actuator_type == "VCA":
            painter.drawRect(self.boundingRect())
        else:  # "M"
            painter.drawRoundedRect(self.boundingRect(), 5, 5)

        # Now, only draw the highlight rim if the item is selected
        if self.isSelected():
            highlight_pen = QPen(QColor(225, 20, 146), 3)  # Thicker rim for highlighting
            painter.setPen(highlight_pen)
            
            # Draw the highlight rim (slightly larger than the original shape)
            if self.actuator_type == "LRA":
                painter.drawEllipse(self.boundingRect().adjusted(-2, -2, 2, 2))  # Slightly larger for the rim
            elif self.actuator_type == "VCA":
                painter.drawRect(self.boundingRect().adjusted(-2, -2, 2, 2))
            else:  # "M"
                painter.drawRoundedRect(self.boundingRect().adjusted(-2, -2, 2, 2), 5, 5)

        # Set font size
        font = painter.font()
        font.setPointSizeF(self.calculate_font_size())
        painter.setFont(font)

        # Convert the ID to the desired format
        if '.' in self.id:
            main_id, sub_id = self.id.split('.')
            formatted_id = main_id + to_subscript(sub_id)
        else:
            formatted_id = self.id  # Handle cases where ID does not contain a '.'

        # Calculate text position
        rect = self.boundingRect()
        text_rect = QRectF(rect.left() + self.text_horizontal_offset,
                        rect.top() + self.text_vertical_offset,
                        rect.width(),
                        rect.height())

        # Draw text
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, formatted_id)


    def hoverEnterEvent(self, event):
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def hoverLeaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.signal_handler.clicked.emit(self.id)  # Emit the signal with the actuator's ID
        super().mousePressEvent(event)
        

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

        # Get the ActuatorCanvas view and its canvas rectangle
        canvas = self.scene().views()[0]
        canvas_rect = canvas.canvas_rect

        # Calculate the bounding box of all selected items
        selected_items = self.scene().selectedItems()
        if not selected_items:
            return

        bounding_rect = QRectF()
        for item in selected_items:
            bounding_rect = bounding_rect.united(item.mapRectToScene(item.boundingRect()))

        # Calculate the delta movement from the original position
        delta = event.scenePos() - event.lastScenePos()

        # Check if the bounding box after movement will be within the canvas limits
        if bounding_rect.left() + delta.x() < canvas_rect.left():
            delta.setX(canvas_rect.left() - bounding_rect.left())
        if bounding_rect.right() + delta.x() > canvas_rect.right():
            delta.setX(canvas_rect.right() - bounding_rect.right())
        if bounding_rect.top() + delta.y() < canvas_rect.top():
            delta.setY(canvas_rect.top() - bounding_rect.top())
        if bounding_rect.bottom() + delta.y() > canvas_rect.bottom():
            delta.setY(canvas_rect.bottom() - bounding_rect.bottom())

        # Apply the adjusted movement to all selected items
        for item in selected_items:
            item.moveBy(delta.x(), delta.y())

        # Trigger a full repaint of the canvas during dragging
        self.update()  # Force repaint of the canvas
        canvas.update()  # Ensure the view is updated

        # Trigger a redraw of all lines
        canvas.redraw_all_lines()

    
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
        self.signal_handler.properties_changed.emit(self.id, self.actuator_type, self.color.name())

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
    no_actuator_selected = pyqtSignal()

    def __init__(self, parent=None, app_reference=None):
        super().__init__(parent)
        self.haptics_app = app_reference  # Store the reference to the Haptics_App instance

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

        self.scene.selectionChanged.connect(self.handle_selection_change)

    def handle_selection_change(self):
        # Force an update on the scene to repaint the actuators
        for item in self.scene.selectedItems():
            item.update()  # Ensure selected items are redrawn
        
        # Update the entire scene to clear any artifacts
        self.scene.update()


    def draw_arrowhead(self, line, ratio=0.55):
        # Calculate the midpoint of the line
        midpoint = QPointF((line.p1().x() + ratio * (line.p2().x() - line.p1().x())), 
                            (line.p1().y() + ratio * (line.p2().y() - line.p1().y())))

        # Size of the arrowhead
        arrow_size = 5

        # Create a simple triangle for the arrowhead
        arrow_head = QPolygonF()
        arrow_head.append(QPointF(0, 0))  # The tip of the arrow
        arrow_head.append(QPointF(-arrow_size, arrow_size/2))
        arrow_head.append(QPointF(-arrow_size, -arrow_size/2))

        # Calculate the angle of the line
        angle = line.angle()

        # Rotate the arrowhead to match the direction of the line
        transform = QTransform()
        transform.translate(midpoint.x(), midpoint.y())  # Move the arrowhead to the midpoint
        transform.rotate(-angle)  # Rotate it according to the line's angle

        # Apply the transformation to the arrowhead
        arrow_head = transform.map(arrow_head)

        # Draw the arrowhead
        arrow_item = self.scene.addPolygon(arrow_head, QPen(Qt.GlobalColor.black), QBrush(Qt.GlobalColor.black))
        arrow_item.setZValue(-1)  # Ensure the arrowhead is behind the actuators



    def redraw_all_lines(self):
        """Redraw all lines connecting actuators."""
        # Remove all existing lines and arrowheads except for the scale line and text
        for item in self.scene.items():
            if isinstance(item, (QGraphicsLineItem, QGraphicsPolygonItem)) and item != self.scale_line and item != self.scale_text:
                self.scene.removeItem(item)

        # Redraw lines based on current actuator positions
        for actuator in self.actuators:
            if actuator.predecessor:
                predecessor = self.get_actuator_by_id(actuator.predecessor)
                if predecessor:
                    line = QLineF(predecessor.pos(), actuator.pos())
                    line_item = self.scene.addLine(line, QPen(Qt.GlobalColor.black, 2))
                    line_item.setZValue(-1)  # Ensure the line is behind the actuators

                    # Draw the arrowhead
                    self.draw_arrowhead(line)

            if actuator.successor:
                successor = self.get_actuator_by_id(actuator.successor)
                if successor:
                    line = QLineF(actuator.pos(), successor.pos())
                    line_item = self.scene.addLine(line, QPen(Qt.GlobalColor.black, 2))
                    line_item.setZValue(-1)  # Ensure the line is behind the actuators

                    # Draw the arrowhead
                    self.draw_arrowhead(line)

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

        # Set the Z-value of the actuator higher than the lines
        actuator.setZValue(0)

        # Emit signal when an actuator is added
        self.actuator_added.emit(new_id, actuator_type, color.name(), x, y)

        # Draw an arrow connecting to the predecessor
        if predecessor:
            for act in self.actuators:
                if act.id == predecessor:
                    line = QLineF(act.pos(), actuator.pos())
                    line_item = self.scene.addLine(line, QPen(Qt.GlobalColor.black, 2))
                    line_item.setZValue(-1)  # Ensure the line is behind the actuators

                    # Draw the arrowhead
                    self.draw_arrowhead(line)
                    break

        if successor:
            for act in self.actuators:
                if act.id == successor:
                    line = QLineF(actuator.pos(), act.pos())
                    line_item = self.scene.addLine(line, QPen(Qt.GlobalColor.black, 2))
                    line_item.setZValue(-1)  # Ensure the line is behind the actuators

                    # Draw the arrowhead
                    self.draw_arrowhead(line)
                    break

        actuator.update()


    def get_actuator_by_id(self, actuator_id):
        """Retrieve an actuator by its ID."""
        for actuator in self.actuators:
            if actuator.id == actuator_id:
                return actuator
        return None

    def is_drop_allowed(self, pos):
        return self.canvas_rect.contains(pos)


    def update_canvas_visuals(self):
        # Remove the old white rectangle if it exists
        if self.white_rect_item:
            self.scene.removeItem(self.white_rect_item)
            self.white_rect_item = None

        # Add the new white rectangle
        self.white_rect_item = self.scene.addRect(self.canvas_rect, QPen(Qt.GlobalColor.black), QBrush(QColor(240, 235, 229)))
        self.white_rect_item.setZValue(-999)

        # Add the new scale line and text only if they don't exist
        if not self.scale_line:
            self.scale_line = self.scene.addLine(self.canvas_rect.left() + 10, self.canvas_rect.bottom() - 10,
                                                self.canvas_rect.left() + 110, self.canvas_rect.bottom() - 10,
                                                QPen(Qt.GlobalColor.black, 2))
            self.scale_line.setZValue(1000)

        if not self.scale_text:
            self.scale_text = self.scene.addText("100 mm")
            text_rect = self.scale_text.boundingRect()
            self.scale_text.setPos(self.canvas_rect.left() + 50 - text_rect.width() / 2, self.canvas_rect.bottom() - 15 - text_rect.height())
            self.scale_text.setDefaultTextColor(Qt.GlobalColor.black)  # Set text color to black
            self.scale_text.setZValue(1000)




    def update_scale_position(self):
        if self.scale_line and self.scale_text:
            self.scale_line.setLine(self.canvas_rect.left() + 10, self.canvas_rect.bottom() - 10,
                                    self.canvas_rect.left() + 110, self.canvas_rect.bottom() - 10)
            text_rect = self.scale_text.boundingRect()
            self.scale_text.setPos(self.canvas_rect.left() + 50 - text_rect.width() / 2, self.canvas_rect.bottom() - 15 - text_rect.height())

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())

        if event.button() == Qt.MouseButton.LeftButton:
            if isinstance(item, Actuator):  # Left-click on an actuator
                self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                item.signal_handler.clicked.emit(item.id)  # Emit the signal with the actuator's ID from the Actuator
                super().mousePressEvent(event)
            else:
                self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
                self.no_actuator_selected.emit()  # Emit the signal when no actuator is selected
                super().mousePressEvent(event)

        elif event.button() == Qt.MouseButton.MiddleButton:  # Enable panning with middle mouse button
            self.panning = True
            self.last_pan_point = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()

        elif event.button() == Qt.MouseButton.RightButton:  # Context menu for right-click
            if isinstance(item, Actuator):
                self.show_context_menu(item, event.pos())
            else:
                self.no_actuator_selected.emit()
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
            selected_items = self.scene.selectedItems()
            if selected_items:
                for item in selected_items:
                    if isinstance(item, Actuator):
                        self.remove_actuator(item)
            else:
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

            # Update plotter immediately
            self.haptics_app.update_timeline_actuator(old_id, new_id, new_type, actuator.color.name())

            self.redraw_all_lines() # Trigger a redraw of all lines


    def update_related_actuators(self, old_id, new_id):
        for act in self.actuators:
            if act.predecessor == old_id:
                act.predecessor = new_id
            if act.successor == old_id:
                act.successor = new_id
            act.update()

    def remove_actuator(self, actuator):
        selected_items = self.scene.selectedItems()

        if selected_items:
            for item in selected_items:
                if isinstance(item, Actuator):
                    # Ensure the item is still part of the scene
                    if item.scene() == self.scene:
                        matching_actuators = [a for a in self.actuators if a.id == item.id]
                        if matching_actuators:
                            self.actuators.remove(matching_actuators[0])
                        self.scene.removeItem(item)
                        self.actuator_deleted.emit(item.id)  # Emit the deletion signal
                        # Remove from plotter immediately
                        self.haptics_app.remove_actuator_from_timeline(item.id)
        else:
            # Ensure the actuator is still part of the scene
            if actuator.scene() == self.scene:
                matching_actuators = [a for a in self.actuators if a.id == actuator.id]
                if matching_actuators:
                    self.actuators.remove(matching_actuators[0])
                self.scene.removeItem(actuator)
                self.actuator_deleted.emit(actuator.id)  # Emit the deletion signal
                # Remove from plotter immediately
                self.haptics_app.remove_actuator_from_timeline(actuator.id)

        self.redraw_all_lines()  # Trigger a redraw of all lines




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

    def clear_lines_except_scale(self):
        # Remove all lines and arrows except the scale line and scale text
        for item in self.scene.items():
            if isinstance(item, QGraphicsLineItem) and item != self.scale_line:
                self.scene.removeItem(item)
            elif isinstance(item, QGraphicsPolygonItem):  # Assuming arrows are polygons
                self.scene.removeItem(item)
            elif isinstance(item, QGraphicsTextItem) and item != self.scale_text:
                self.scene.removeItem(item)



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

class TimelineCanvas(FigureCanvas):

    def __init__(self, parent=None, width=8, height=2, dpi=100, color=(134/255, 150/255, 167/255), label="", app_reference=None):
        self.app_reference = app_reference  # Reference to Haptics_App
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor=color)
        # self.axes = self.fig.add_subplot(111)
        self.axes = self.fig.add_axes([0.1, 0.15, 0.8, 0.8])  # Use add_axes to create a single plot
        self.axes.set_facecolor(color)

        
        # Set y-axis to only show the 0 value
    
        self.axes.spines['top'].set_visible(True)
        self.axes.spines['right'].set_visible(True)
        self.axes.spines['left'].set_visible(True)  # Show left spine
        self.axes.spines['bottom'].set_visible(True)  # Show bottom spine
        
        # Set spine color
        spine_color = to_rgba((240/255, 235/255, 229/255))  # Custom color for the border

        self.axes.tick_params(axis='x', colors=spine_color, labelsize=8)  # Adjust tick label size here
        self.axes.tick_params(axis='y', colors=spine_color, labelsize=8)  # Adjust tick label size here
        self.axes.spines['bottom'].set_color(spine_color)
        self.axes.spines['top'].set_color(spine_color)
        self.axes.spines['right'].set_color(spine_color)
        self.axes.spines['left'].set_color(spine_color)
        self.axes.set_ylabel('Amplitude', fontsize=9.5, color=spine_color)  # Adjust font size here

        # Move x-axis label to the right side
        self.set_custom_xlabel('Time (s)', fontsize=9.5, color=spine_color)  # Custom method for xlabel


        super(TimelineCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.setStyleSheet(f"background-color: rgba({int(color[0]*255)}, {int(color[1]*255)}, {int(color[2]*255)}, 0);")
        self.setAcceptDrops(True)
        
        # Set the x-axis limits to [0, total_time]
        self.update_x_axis_limits()

        self.signals = {}  # Dictionary to store signal data with time ranges

    def set_custom_xlabel(self, xlabel, fontsize=9.5, color='black'):
        self.axes.set_xlabel('')  # Remove default xlabel
        self.axes.annotate(xlabel, xy=(1.01, -0.01), xycoords='axes fraction', fontsize=fontsize,
                           color=color, ha='left', va='center')

    def update_x_axis_limits(self):
        if self.app_reference.total_time is not None:
            self.axes.set_xlim(0, self.app_reference.total_time)
            self.draw()

    def update_canvas(self, color, label):
        self.fig.set_facecolor(color)
        self.axes.set_facecolor(color)
        self.setStyleSheet(f"background-color: rgba({int(color[0]*255)}, {int(color[1]*255)}, {int(color[2]*255)}, 0);")
        self.update_x_axis_limits()  # Ensure x-axis limits are updated
        self.draw()

    

    def plot_signal(self, signal_type, start_time, stop_time):
        signal_data = self.get_signal_data(signal_type)
        if signal_data is not None:
            # Ensure stop_time does not exceed total_time
            stop_time = min(stop_time, self.app_reference.total_time)
            
            # Generate time array
            total_points = 500
            t = np.linspace(0, self.app_reference.total_time, total_points)
            
            # Create y array, setting values outside the range to 0
            if not hasattr(self, 'y_data'):
                self.y_data = np.zeros_like(t)  # Initialize y_data only once
            new_y = np.zeros_like(t)
            
            start_index = int((start_time / self.app_reference.total_time) * total_points)
            stop_index = int((stop_time / self.app_reference.total_time) * total_points)
            
            new_y[start_index:stop_index] = signal_data[:stop_index - start_index]

            # Check for conflicts
            conflict = None
            for i in range(start_index, stop_index):
                if self.y_data[i] != 0 and new_y[i] != 0:
                    conflict_start = t[i]
                    while i < stop_index and self.y_data[i] != 0 and new_y[i] != 0:
                        i += 1
                    conflict_stop = t[i-1]
                    conflict = (conflict_start, conflict_stop)
                    break

            if conflict:
                action = self.show_conflict_dialog(conflict, start_time, stop_time)
                if action == 'Replace':
                    self.y_data[start_index:stop_index] = new_y[start_index:stop_index]
                elif action == 'Reset':
                    # Re-trigger the time input dialog for the user to reset the time range
                    new_start_time, new_stop_time = self.show_time_input_dialog(signal_type)
                    if new_start_time is not None and new_stop_time is not None:
                        self.plot_signal(signal_type, new_start_time, new_stop_time)  # Recursively call plot_signal
                    return
                else:
                    return
            else:
                self.y_data[start_index:stop_index] = new_y[start_index:stop_index]
            
            self.axes.clear()  # Clear previous plots


            self.axes.spines['top'].set_visible(True)
            self.axes.spines['right'].set_visible(True)
            self.axes.spines['left'].set_visible(True)  # Show left spine
            self.axes.spines['bottom'].set_visible(True)  # Show bottom spine

            # Set spine color
            spine_color = to_rgba((240/255, 235/255, 229/255))  # Custom color for the border
            self.axes.spines['left'].set_color(spine_color)
            self.axes.spines['bottom'].set_color(spine_color)
            self.axes.spines['top'].set_color(spine_color)
            self.axes.spines['right'].set_color(spine_color)
            
            # Set x and y labels
            self.set_custom_xlabel('Time (s)', fontsize=9.5, color=spine_color)  # Custom method for xlabel
            self.axes.set_ylabel('Amplitude', fontsize=9.5, color=spine_color)  # Adjust font size here
            
            self.axes.tick_params(axis='x', colors=spine_color, labelsize=8)  # Adjust tick label size here
            self.axes.tick_params(axis='y', colors=spine_color, labelsize=8)  # Adjust tick label size here
            

            self.axes.plot(t, self.y_data, color=spine_color)

     
            self.axes.set_xlim(0, self.app_reference.total_time if self.app_reference.total_time else 10)  # Example: use total_time or default
            # self.axes.set_ylim(-1, 1)  # Example: setting y-axis range

            self.draw()



    def check_time_conflict(self, start_time, stop_time):
        for existing_start, existing_stop in self.signals.keys():
            if not (stop_time <= existing_start or start_time >= existing_stop):
                return (existing_start, existing_stop)
        return None

    def show_conflict_dialog(self, conflict, start_time, stop_time):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Time Conflict Detected")
        # msg_box.setText(f"The time range {start_time}s to {stop_time}s conflicts with an existing signal from {conflict[0]}s to {conflict[1]}s.")
        msg_box.setText(f"The time range {start_time}s to {stop_time}s conflicts with an existing signal.")
        msg_box.setInformativeText("Do you want to replace the conflicting signal or reset the time range of the new signal?")
        
        # Apply the custom stylesheet
        msg_box.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: black; }
            QPushButton { 
                background-color: white; 
                color: black; 
                border: 1px solid black; 
                padding: 5px; 
            }
            QPushButton:hover { 
                background-color: gray; 
            }
        """)

        replace_button = msg_box.addButton("Replace", QMessageBox.ButtonRole.YesRole)
        reset_button = msg_box.addButton("Reset", QMessageBox.ButtonRole.NoRole)
        msg_box.exec()

        if msg_box.clickedButton() == replace_button:
            return 'Replace'
        else:
            return 'Reset'


    def replace_signal_in_range(self, start_time, stop_time, new_signal_data):
        # Replace the conflicting part of the signal
        self.remove_signal_in_range(start_time, stop_time)
        self.add_signal_to_plot(start_time, stop_time, new_signal_data)

    def reset_time_range(self, start_time, stop_time):
        # Adjust the time range to avoid conflict
        existing_times = sorted(self.signals.keys())
        for existing_start, existing_stop in existing_times:
            if start_time < existing_stop <= stop_time:
                start_time = existing_stop
            elif start_time <= existing_start < stop_time:
                stop_time = existing_start
        return start_time, stop_time

    def add_signal_to_plot(self, start_time, stop_time, signal_data):
        total_points = 500
        t = np.linspace(0, self.app_reference.total_time, total_points)
        y = np.zeros_like(t)
        start_index = int((start_time / self.app_reference.total_time) * total_points)
        stop_index = int((stop_time / self.app_reference.total_time) * total_points)
        y[start_index:stop_index] = signal_data[:stop_index - start_index]

        if len(self.signals) > 0:
            current_y = self.axes.lines[0].get_ydata()
            current_y[start_index:stop_index] = y[start_index:stop_index]
            self.axes.lines[0].set_ydata(current_y)
        else:
            self.axes.plot(t, y)

        self.signals[(start_time, stop_time)] = signal_data
        self.draw()

    def remove_signal_in_range(self, start_time, stop_time):
        for (existing_start, existing_stop), _ in list(self.signals.items()):
            if not (stop_time <= existing_start or start_time >= existing_stop):
                del self.signals[(existing_start, existing_stop)]

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        item = event.source().selectedItems()[0]
        signal_type = item.text(0)

        # Check if total time is set
        if self.app_reference.total_time is None:
            # If total time is not set, prompt the user to set it up
            self.app_reference.setup_total_time()
            # If the user cancels setting the total time, ignore the drop event
            if self.app_reference.total_time is None:
                return

        start_time, stop_time = self.show_time_input_dialog(signal_type)
        
        if start_time is not None and stop_time is not None:
            # Check if the start time or stop time exceeds the total time
            if start_time > self.app_reference.total_time or stop_time > self.app_reference.total_time:
                # Show a warning message with custom style
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Time Exceeds Total Time")
                
                msg_box.setText(f"Total time is only {self.app_reference.total_time} seconds. Please don't exceed the range or reset your total time.")
                msg_box.setIcon(QMessageBox.Icon.Warning)
                
                # Apply the custom stylesheet
                msg_box.setStyleSheet("""
                    QMessageBox { background-color: white; }
                    QLabel { color: black; }
                    QPushButton { 
                        background-color: white; 
                        color: black; 
                        border: 1px solid black; 
                        padding: 5px; 
                    }
                    QPushButton:hover { 
                        background-color: gray; 
                    }
                """)
                
                msg_box.exec()
                return  # Stop further processing

            self.plot_signal(signal_type, start_time, stop_time)




    def show_time_input_dialog(self, signal_type):
        dialog = TimeInputDialog(signal_type)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            start_time = dialog.start_time_input.value()
            stop_time = dialog.stop_time_input.value()
            return start_time, stop_time
        return None, None

    def get_signal_data(self, signal_type):
        # Retrieve signal data based on signal_type
        if signal_type in self.app_reference.custom_signals:
            signal_data = self.app_reference.custom_signals[signal_type]["data"]
        elif signal_type in self.app_reference.signal_templates:
            signal_data = self.app_reference.signal_templates[signal_type]["data"]
        elif signal_type in self.app_reference.imported_signals:
            signal_data = self.app_reference.imported_signals[signal_type]["data"]
        else:
            signal_data = None
        return signal_data

    def show_time_input_dialog(self, signal_type):
        while True:
            dialog = TimeInputDialog(signal_type)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                start_time = dialog.start_time_input.value()
                stop_time = dialog.stop_time_input.value()
                if start_time >= stop_time:
                    msg_box = QMessageBox(self)
                    msg_box.setWindowTitle("Invalid Time Range")
                    msg_box.setText("Start time must be smaller than stop time.")
                    msg_box.setIcon(QMessageBox.Icon.Warning)
                    
                    # Set the background to black, text to white, and button style
                    msg_box.setStyleSheet("""
                        QMessageBox { background-color: white; }
                        QLabel { color: black; }
                        QPushButton { 
                            background-color: white; 
                            color: black; 
                            border: 1px solid black; 
                            padding: 5px; 
                        }
                        QPushButton:hover { 
                            background-color: gray; 
                        }
                    """)
                    msg_box.exec()
                else:
                    return start_time, stop_time
            else:
                return None, None
    
    def remove_data_beyond_time(self, total_time):
        total_points = 500
        t = np.linspace(0, self.app_reference.total_time, total_points)

        # Find the index where the time exceeds the new total_time
        cut_off_index = int((total_time / self.app_reference.total_time) * total_points)

        # Set the y-data beyond this index to zero
        if hasattr(self, 'y_data'):
            self.y_data[cut_off_index:] = 0
            self.axes.clear()
            self.axes.plot(t, self.y_data)
            self.draw()

    def add_zero_signal_for_new_range(self, old_total_time, new_total_time):
        total_points = 500
        t = np.linspace(0, self.app_reference.total_time, total_points)
        
        if hasattr(self, 'y_data'):
            start_index = int((old_total_time / self.app_reference.total_time) * total_points)
            stop_index = int((new_total_time / self.app_reference.total_time) * total_points)
            
            # Extend y_data with zeros
            self.y_data[start_index:stop_index] = 0
            self.axes.clear()
            self.axes.plot(t, self.y_data)
            self.draw()

class TimeInputDialog(QDialog):
    def __init__(self, signal_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Input Time Range")

        layout = QVBoxLayout(self)
        
        signal_label = QLabel(f"Signal Type: {signal_type}")
        
        layout.addWidget(signal_label)
        
        form_layout = QFormLayout()
        
        self.start_time_input = QDoubleSpinBox()
        self.start_time_input.setRange(0, 1000)  # Adjust range as needed
        form_layout.addRow("Start Time (s):", self.start_time_input)
        
        self.stop_time_input = QDoubleSpinBox()
        self.stop_time_input.setRange(0, 1000)  # Adjust range as needed
        form_layout.addRow("Stop Time (s):", self.stop_time_input)
        
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

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

class Haptics_App(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # Get the absolute path to the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Construct the absolute path to the layout.ui file
        ui_file_path = os.path.join(current_dir, 'layout.ui')

        # Load the UI file
        self.ui = uic.loadUi(ui_file_path, self)
 
        self.resize(1500, 750)
        icon = QtGui.QIcon()
        icon_path = "resources/logo.jpg"

        self.ui.pushButton_5.clicked.connect(self.setup_total_time)
        self.statusBar().showMessage("Welcome to Haptics App")

        # Add a flag to track the first signal drop
        self.first_signal_drop = True
        self.total_time = None

        if os.path.exists(icon_path):
            icon.addPixmap(QtGui.QPixmap(icon_path), QIcon.Mode.Normal, QIcon.State.Off)
            self.setWindowIcon(icon)
        else:
            print(f"Icon file not found at path: {icon_path}")

        self.threadpool = QtCore.QThreadPool()

        # Set main background color
        self.setStyleSheet("background-color: rgb(193, 205, 215);")
        self.widget_2.setStyleSheet("background-color: rgb(193, 205, 215);")
        self.widget_3.setStyleSheet("background-color: rgb(134, 150, 167);")


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
        self.actuator_canvas = ActuatorCanvas(self.ui.widget_2,app_reference=self)
        self.actuator_canvas.setFixedHeight(380)  # Set the fixed height here
        self.ui.gridLayout_5.addWidget(self.actuator_canvas, 0, 0, 1, 1)

        # Create a scene for the selection bar
        self.selection_scene = QGraphicsScene()

        # Create the selection bar view and add it to the layout
        self.selection_bar = SelectionBar(self.selection_scene)
        self.selection_view = SelectionBarView(self.selection_scene, self.ui.widget_2)
        self.selection_view.setFixedSize(100, 100)  # Set size and position as needed
        self.ui.gridLayout_5.addWidget(self.selection_view, 0, 0, 1, 1)  # Overlay on the actuator canvas

        # Enable scroll bars for the timeline canvas
        self.ui.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.ui.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Connect clear button to clear_plot method
        self.ui.pushButton.clicked.connect(self.maincanvas.clear_plot)
        
        # Connect save button to save_current_signal method
        self.ui.pushButton_2.clicked.connect(self.save_current_signal)

        # Connect save button to save_current_signal method
        self.ui.pushButton_3.clicked.connect(self.clear_canvas_and_timeline)

        # Connect "Adjust Size" button to adjust_canvas_size method
        self.pushButton_4.clicked.connect(self.adjust_canvas_size)

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

        # Create the PreviewCanvas and add it to widget_3
        self.preview_canvas = PreviewCanvas(self.ui.widget_3, width=5, height=0.4, dpi=100)
        self.preview_canvas.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

        # Create a layout for widget_3 if not already present
        layout = QtWidgets.QVBoxLayout(self.ui.widget_3)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove any margins
        layout.setSpacing(0)  # Remove spacing between the canvas and the widget edges

        # Add the PreviewCanvas to widget_3's layout
        layout.addWidget(self.preview_canvas)

        # Create a layout for widget_3 if not already present
        self.ui.widget_3.setLayout(QtWidgets.QVBoxLayout())
        
        # Add the PreviewCanvas to widget_3's layout
        self.ui.widget_3.layout().addWidget(self.preview_canvas)

        # Ensure the tree widget itemClicked event is connected to update the preview
        self.ui.treeWidget.itemClicked.connect(self.on_tree_item_clicked)

        self.current_actuator = None  # Attribute to track the current actuator

        self.actuator_canvas.actuator_added.connect(self.connect_actuator_signals)

        # Connect the no_actuator_selected signal to the switch_to_main_canvas slot
        self.actuator_canvas.no_actuator_selected.connect(self.switch_to_main_canvas)


    def connect_actuator_signals(self, actuator_id, actuator_type, color, x, y):
        actuator = self.actuator_canvas.get_actuator_by_id(actuator_id)
        if actuator:
            actuator.signal_handler.clicked.connect(self.on_actuator_clicked)
            actuator.signal_handler.properties_changed.connect(self.update_plotter)


    def on_actuator_clicked(self, actuator_id):
        # When an actuator is clicked, switch to the TimelineCanvas
        if self.current_actuator != actuator_id:
            self.current_actuator = actuator_id
            self.switch_to_timeline_canvas(actuator_id)
            # Retrieve the actuator's type and color
            actuator = self.actuator_canvas.get_actuator_by_id(actuator_id)
            if actuator:
                # Immediately update the plotter to reflect the clicked actuator
                self.update_plotter(actuator_id, actuator.actuator_type, actuator.color.name())


    def update_plotter(self, actuator_id, actuator_type, color):
        if self.current_actuator == actuator_id:
            self.switch_to_timeline_canvas(actuator_id)  # Update the plotter to reflect changes


    def switch_to_timeline_canvas(self, actuator_id):
        # Clear the current layout
        self.ui.gridLayout.removeWidget(self.maincanvas)
        self.maincanvas.setParent(None)  # Detach MplCanvas from its parent

        # Create and add the TimelineCanvas
        color_rgb = self.actuator_canvas.branch_colors[actuator_id.split('.')[0]].getRgbF()[:3]
        self.timeline_canvas = TimelineCanvas(self.ui.widget, color=color_rgb, label=f"Timeline for {actuator_id}", app_reference=self)
        self.ui.gridLayout.addWidget(self.timeline_canvas, 0, 0, 1, 1)

    def switch_to_main_canvas(self):
        # Check if already on MplCanvas, no need to switch if it is
        if self.ui.gridLayout.indexOf(self.maincanvas) != -1:
            return

        # Remove the current widget (TimelineCanvas)
        if hasattr(self, 'timeline_canvas'):
            self.ui.gridLayout.removeWidget(self.timeline_canvas)
            self.timeline_canvas.setParent(None)

        # Add the MplCanvas back to the layout
        self.ui.gridLayout.addWidget(self.maincanvas, 0, 0, 1, 1)
        self.current_actuator = None  # Reset current actuator tracking

    def mousePressEvent(self, event):
        # If clicked on blank space, switch back to MplCanvas
        if self.current_actuator and not self.actuator_canvas.itemAt(event.pos()):
            self.current_actuator = None
            self.switch_to_main_canvas()
        super().mousePressEvent(event)

    def update_status_bar(self, signal_type, parameters):
        # Format the parameters into a readable string
        param_str = ', '.join([f'{key}: {value}' for key, value in parameters.items()])
        # Display the signal type and parameters in the status bar
        self.statusBar().showMessage(f"Current Signal: {signal_type} | Parameters: {param_str}")


    def clear_canvas_and_timeline(self):
        # Prompt a warning to the user
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Clear Actuator and Timeline Data")
        msg_box.setText("Are you sure you want to clear all the actuators and corresponding timeline data?")
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        # Apply the custom stylesheet for the message box
        msg_box.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: black; }
            QPushButton { 
                background-color: white; 
                color: black; 
                border: 1px solid black; 
                padding: 5px; 
            }
            QPushButton:hover { 
                background-color: gray; 
            }
        """)

        result = msg_box.exec()

        if result == QMessageBox.StandardButton.Yes:
            # If user confirms, clear the canvas and timeline
            self.actuator_canvas.clear_lines_except_scale()  # Clear lines, not the scale line
            self.actuator_canvas.clear_canvas()  # Clear actuators
            self.clear_timeline_canvas()  # Clear timeline
            self.reset_color_management()
        else:
            # If user cancels, do nothing
            return
    

    def clear_timeline_canvas(self):
        # Clear the timeline layout
        while self.timeline_layout.count() > 0:
            item = self.timeline_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.timeline_widgets.clear()

    def reset_color_management(self):
        # Reset color management stuff
        self.actuator_canvas.branch_colors.clear()
        self.actuator_canvas.color_index = 0

    def adjust_canvas_size(self):
        dialog = CanvasSizeDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                width = int(dialog.width_input.text())
                height = int(dialog.height_input.text())
                self.actuator_canvas.set_canvas_size(width, height)
            except ValueError:
                print("Invalid input. Please enter valid integer values for width and height.")
    
    def setup_total_time(self):
        msg_box = QInputDialog(self)
        msg_box.setWindowTitle("Set up total time")
        msg_box.setLabelText("Enter total time (in seconds):")
        msg_box.setInputMode(QInputDialog.InputMode.DoubleInput)
        msg_box.setDoubleDecimals(2)
        msg_box.setDoubleMinimum(0)
        if self.total_time is not None:
            msg_box.setDoubleValue(self.total_time)

        # Set the custom stylesheet
        msg_box.setStyleSheet("""
            QInputDialog { background-color: white; }
            QLabel { color: black; }
            QPushButton { 
                background-color: white; 
                color: black; 
                border: 1px solid black; 
                padding: 5px; 
            }
            QPushButton:hover { 
                background-color: gray; 
            }
        """)

        if msg_box.exec() == QDialog.DialogCode.Accepted:
            new_total_time = msg_box.doubleValue()

            if self.total_time is None:
                # If total_time is None, simply set it to the new value without any checks
                self.total_time = new_total_time
            elif new_total_time < self.total_time:
                # Warn the user about potential data loss
                warning_box = QMessageBox(self)
                warning_box.setWindowTitle("Warning")
                warning_box.setText(f"The setting total time is less than the current total time ({self.total_time}s). "
                                    "This may cause data loss. Do you still want to proceed?")
                warning_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                warning_box.setStyleSheet("""
                    QMessageBox { background-color: white; }
                    QLabel { color: black; }
                    QPushButton { 
                        background-color: white; 
                        color: black; 
                        border: 1px solid black; 
                        padding: 5px; 
                    }
                    QPushButton:hover { 
                        background-color: gray; 
                    }
                """)
                result = warning_box.exec()

                if result == QMessageBox.StandardButton.Yes:
                    self.total_time = new_total_time
                    self.remove_data_beyond_total_time()
                else:
                    return  # Do nothing if the user clicks 'No'

            elif new_total_time > self.total_time:
                old_total_time = self.total_time
                self.total_time = new_total_time
                self.add_zero_signal_for_new_time_range(old_total_time)
            else:
                self.total_time = new_total_time

            self.update_all_timeline_x_axis_limits()  # Update all timeline x-axes
            self.statusBar().showMessage(f"Total time set to {self.total_time} seconds")
        else:
            self.statusBar().showMessage("Total time not set. Please set the total time using the 'Set Total Time' button.")

    def remove_data_beyond_total_time(self):
        for _, (timeline_widget, _) in self.timeline_widgets.items():
            timeline_widget.remove_data_beyond_time(self.total_time)

    def add_zero_signal_for_new_time_range(self, old_total_time):
        for _, (timeline_widget, _) in self.timeline_widgets.items():
            timeline_widget.add_zero_signal_for_new_range(old_total_time, self.total_time)


    def update_all_timeline_x_axis_limits(self):
        for _, (timeline_widget, _) in self.timeline_widgets.items():
            timeline_widget.update_x_axis_limits()

    def add_actuator_to_timeline(self, new_id, actuator_type, color, x, y):
        color_rgb = QColor(color).getRgbF()[:3]
        actuator_widget = TimelineCanvas(parent=self.ui.scrollAreaWidgetContents, color=color_rgb, label=f"{actuator_type} - {new_id}", app_reference=self)
        
        # Ensure the same x and y axis labels are used across all timeline widgets
        actuator_widget.axes.set_xlabel("Time (s)", fontsize=9.5)
        actuator_widget.axes.set_ylabel("Amplitude", fontsize=9.5)
        
        # Optionally, set the x-axis limits if required
        actuator_widget.axes.set_xlim(0, self.total_time if self.total_time else 10)  # Example: total_time or default to 10 seconds
        actuator_widget.axes.set_ylim(-1, 1)  # Example: setting y-axis range
        
        actuator_layout = QHBoxLayout(actuator_widget)
        actuator_label = QLabel(f"{actuator_type} - {new_id}")
        actuator_layout.addWidget(actuator_label)
        
        self.timeline_layout.addWidget(actuator_widget)
        self.timeline_widgets[new_id] = (actuator_widget, actuator_label)


    def update_timeline_actuator(self, old_actuator_id, new_actuator_id, actuator_type, color):
        if old_actuator_id in self.timeline_widgets:
            actuator_widget, actuator_label = self.timeline_widgets.pop(old_actuator_id)
            
            # Update the canvas color
            color_rgb = QColor(color).getRgbF()[:3]
            actuator_widget.update_canvas(color=color_rgb, label=f"{actuator_type} - {new_actuator_id}")
            
            # Update the widget background color
            actuator_widget.setStyleSheet(f"background-color: rgba({int(color_rgb[0]*255)}, {int(color_rgb[1]*255)}, {int(color_rgb[2]*255)}, 0);")
            
            # Update the label
            actuator_label.setText(f"{actuator_type} - {new_actuator_id}")
            
            # Store the updated reference with the new ID
            self.timeline_widgets[new_actuator_id] = (actuator_widget, actuator_label)

            # Immediately update the plotter to reflect the changes
            self.update_plotter(new_actuator_id, actuator_type, color)


            
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
        if item is None or not isinstance(item, QTreeWidgetItem):
            return  # Exit if the clicked item is None or not a valid item
        
        signal_type = item.text(column)
        if signal_type in self.custom_signals:  # Check if it's a custom signal
            custom_signal = self.custom_signals.get(signal_type)
            if custom_signal is not None:
                self.preview_canvas.plot_default_signal(custom_signal)
        elif signal_type in self.signal_templates:  # Check if it's a provided signal template
            template_signal = self.signal_templates.get(signal_type)
            if template_signal is not None:
                self.preview_canvas.plot_default_signal(template_signal)
        elif signal_type in self.imported_signals:  # Check if it's an imported signal
            imported_signal = self.imported_signals.get(signal_type)
            if imported_signal is not None:
                self.preview_canvas.plot_default_signal(imported_signal)
        else:
            self.preview_canvas.plot_default_signal(None)  # Clear the preview canvas if no valid signal is found


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
