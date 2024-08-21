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
import pickle

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QTreeWidgetItem, QDialog
from PyQt6.QtCore import Qt, pyqtSlot, QPoint
from PyQt6.QtGui import QPen, QColor, QBrush, QFont
from PyQt6.QtCore import pyqtSignal

def to_subscript(text):
    subscript_map = str.maketrans('0123456789', '₀₁₂₃₄₅₆₇₈₉')
    return text.translate(subscript_map)

class DesignSaver:
    def __init__(self, actuator_canvas, timeline_canvases, mpl_canvas, app_reference):
        self.actuator_canvas = actuator_canvas
        self.timeline_canvases = timeline_canvases
        self.mpl_canvas = mpl_canvas
        self.app_reference = app_reference

    def save_design(self):
        file_name, _ = QFileDialog.getSaveFileName(None, "Save As", "", "Design Files (*.dsgn)")
        if file_name:
            try:
                design_data = self.collect_design_data()
                with open(file_name, 'wb') as file:
                    pickle.dump(design_data, file)
                QMessageBox.information(None, "Success", "Design saved successfully!")
            except Exception as e:
                QMessageBox.warning(None, "Error", f"Failed to save design: {str(e)}")
    
    def load_design(self):
        file_name, _ = QFileDialog.getOpenFileName(None, "Open Design", "", "Design Files (*.dsgn)")
        if file_name:
            try:
                with open(file_name, 'rb') as file:
                    design_data = pickle.load(file)
                self.apply_design_data(design_data)
                QMessageBox.information(None, "Success", "Design loaded successfully!")
            except Exception as e:
                QMessageBox.warning(None, "Error", f"Failed to load design: {str(e)}")

    def collect_design_data(self):
        # Collect data from Actuator Canvas
        actuator_data = []
        for actuator in self.actuator_canvas.actuators:
            actuator_data.append({
                'id': actuator.id,
                'type': actuator.actuator_type,
                'color': actuator.color.name(),
                'position': (actuator.pos().x(), actuator.pos().y()),
                'predecessor': actuator.predecessor,
                'successor': actuator.successor
            })
        
        # Collect data from Timeline Canvas
        #print("Timeline Signals:", self.timeline_canvas['signals'])
        timeline_data = []
        for actuator_id, timeline_canvas in self.timeline_canvases.items():
            for signal in timeline_canvas.signals:
                timeline_data.append({
                    'actuator_id': actuator_id,  # Include actuator ID to link the signal to its actuator
                    'type': signal["type"],
                    'start_time': signal["start_time"],
                    'stop_time': signal["stop_time"],
                    'data': signal["data"],
                    'parameters': signal["parameters"]
                })
        
        # Collect data from MplCanvas (Imported signals)
        mpl_data = []
        for signal_name, signal_data in self.app_reference.imported_signals.items():
            mpl_data.append({
                'name': signal_name,
                'data': signal_data
            })
        
        # Combine all data into a dictionary
        design_data = {
            'actuators': actuator_data,
            'timeline': timeline_data,
            'mpl_signals': mpl_data
        }
        return design_data

    def apply_design_data(self, design_data):
        # Clear existing canvases
        self.actuator_canvas.clear_canvas()
        for actuator_id, timeline_canvas in self.timeline_canvases.items():
            timeline_canvas.signals.clear()
        self.mpl_canvas.clear_plot()
        
        # Restore actuators
        for actuator_info in design_data['actuators']:
            x, y = actuator_info['position']
            self.actuator_canvas.add_actuator(x, y, new_id=actuator_info['id'], 
                                              actuator_type=actuator_info['type'], 
                                              predecessor=actuator_info['predecessor'], 
                                              successor=actuator_info['successor'])
        
        # Restore timeline signals
        for signal_info in design_data['timeline']:
            # You may need to determine which timeline_canvas this signal belongs to, possibly based on actuator_id
            corresponding_timeline_canvas = self.timeline_canvases[signal_info['actuator_id']]
            corresponding_timeline_canvas.record_signal(signal_info['type'], signal_info['data'], 
                                                        signal_info['start_time'], signal_info['stop_time'], 
                                                        signal_info['parameters'])
        
        # Restore imported signals in MplCanvas
        for signal_info in design_data['mpl_signals']:
            self.app_reference.imported_signals[signal_info['name']] = signal_info['data']
        
        # Redraw the canvases
        self.actuator_canvas.redraw_all_lines()
        self.mpl_canvas.plot([], [])  # Redraw the MplCanvas

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
        self.app_reference.first_signal_drop = 0
        self.plot([], [])
        print(self.app_reference.first_signal_drop)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        item = event.source().selectedItems()[0]
        signal_type = item.text(0)

        # Initialize customized_signal to None
        customized_signal = None

        # Check if the dropped signal is an imported one
        if signal_type in self.app_reference.imported_signals:
            customized_signal = self.app_reference.imported_signals[signal_type]
            self.add_signal(customized_signal, combine=True)

        # Check if the signal is a customized one
        elif signal_type in self.app_reference.custom_signals:
            customized_signal = self.app_reference.custom_signals[signal_type]
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

        # If a customized signal was created or retrieved, add it to the plot
        if customized_signal:
            self.add_signal(customized_signal, combine=True)
        
        self.app_reference.first_signal_drop += 1
        print("drop",self.app_reference.first_signal_drop)


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
    QColor(158, 175, 163),  # Dark Sea Green
    QColor(194, 166, 159),  # Pale Taupe
    QColor(194, 178, 128),  # Khaki
    QColor(145, 141, 18),  # Khaki
    QColor(150, 143, 132),  # Dark Gray
    QColor(175, 167, 191),  # Thistle
    QColor(144, 175, 197),  # Cadet Blue
    QColor(151, 102, 102),  
    QColor(227, 140, 122),
    QColor(103, 98, 172),
    QColor(33, 104, 80),
    QColor(183, 87, 116),
    QColor(119, 80, 29),
    QColor(172, 94, 169),
    QColor(81, 146, 58),
    QColor(21, 45, 138),
    QColor(206, 21, 39),
    QColor(199, 90, 18),
    QColor(100, 199, 187),
    QColor(209, 139, 0),
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
        """Redraw all lines connecting actuators and check for topology conflicts."""
        # Remove all existing lines and arrowheads except for the scale line and text
        for item in self.scene.items():
            if isinstance(item, (QGraphicsLineItem, QGraphicsPolygonItem)) and item != self.scale_line and item != self.scale_text:
                self.scene.removeItem(item)

        # Iterate through all actuators and draw lines when both conditions are met
        for actuator in self.actuators:
            # Check if an actuator's predecessor and successor are the same
            if (actuator.predecessor == actuator.successor) and (actuator.predecessor is not None):
                self.generate_same_predecessor_successor_warning(actuator.id)
                continue  # Skip drawing the line for this actuator

            # Check for topology conflicts
            if actuator.predecessor:
                predecessor_actuator = self.get_actuator_by_id(actuator.predecessor)
                if predecessor_actuator:
                    # Check if the predecessor lists the current actuator as its successor
                    if predecessor_actuator.successor != actuator.id:
                        self.generate_topology_conflict_warning(actuator.id, predecessor_actuator.id)
                        continue  # Skip drawing the line if there's a conflict
                else:
                    # Predecessor does not exist, issue a warning
                    print(f"Warning: Actuator {actuator.id} references a non-existent predecessor {actuator.predecessor}.")
                    continue  # Skip drawing if predecessor is invalid

            # Check if actuator has a successor and if both conditions are satisfied
            if actuator.successor:
                successor_actuator = self.get_actuator_by_id(actuator.successor)
                if successor_actuator:
                    # Check if the successor lists the current actuator as its predecessor
                    if successor_actuator.predecessor != actuator.id:
                        self.generate_topology_conflict_warning(actuator.id, successor_actuator.id)
                        continue  # Skip drawing the line if there's a conflict
                else:
                    # Successor does not exist, issue a warning
                    print(f"Warning: Actuator {actuator.id} references a non-existent successor {actuator.successor}.")
                    continue  # Skip drawing if successor is invalid

            # Condition to draw the line: Check if both predecessor and successor match the requirements
            if actuator.predecessor:
                predecessor_actuator = self.get_actuator_by_id(actuator.predecessor)
                if predecessor_actuator and predecessor_actuator.successor == actuator.id:
                    # Draw the line from predecessor to current actuator
                    line = QLineF(predecessor_actuator.pos(), actuator.pos())
                    line_item = self.scene.addLine(line, QPen(Qt.GlobalColor.black, 2))
                    line_item.setZValue(-1)  # Ensure the line is behind the actuators
                    self.draw_arrowhead(line)

            # Draw the arrow connecting to the successor
            if actuator.successor:
                successor_actuator = self.get_actuator_by_id(actuator.successor)
                if successor_actuator and successor_actuator.predecessor == actuator.id:
                    line = QLineF(actuator.pos(), successor_actuator.pos())
                    line_item = self.scene.addLine(line, QPen(Qt.GlobalColor.black, 2))
                    line_item.setZValue(-1)  # Ensure the line is behind the actuators
                    self.draw_arrowhead(line)

    def generate_topology_conflict_warning(self, actuator_id_1, actuator_id_2):
        """Generate a warning message for a topology conflict between two actuators."""
        message = (
            f"Topology Conflict Detected!<br>"
            f"Actuator '<b>{actuator_id_1}</b>' claims its successor is '<b>{actuator_id_2}</b>', but "
            f"'<b>{actuator_id_2}</b>' does not recognize '<b>{actuator_id_1}</b>' as its predecessor.<br>"
            "Please check the configuration."
        )
        QMessageBox.warning(self, "Topology Conflict", message)
        print(message)  # Optional: Also print the message to the console for debugging

    def generate_same_predecessor_successor_warning(self, actuator_id):
        """Generate a warning message for an actuator with the same predecessor and successor."""
        message = (
            f"Topology Error Detected!<br>"
            f"Actuator '<b>{actuator_id}</b>' has the <b>same</b> predecessor and successor, which is not allowed.<br>"
            "Please check the configuration."
        )
        QMessageBox.warning(self, "Configuration Error", message)
        print(message)  # Optional: Also print the message to the console for debugging



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
        # Generate a new ID if not provided
        if new_id is None:
            new_id = self.generate_next_id()
        
        # Determine the branch (e.g., A for A.1)
        branch = new_id.split('.')[0]
        if branch not in self.branch_colors:
            if self.color_index < len(COLOR_LIST):
                self.branch_colors[branch] = COLOR_LIST[self.color_index]
                self.color_index += 1
            else:
                self.branch_colors[branch] = generate_contrasting_color(list(self.branch_colors.values()))

        color = self.branch_colors[branch]

        # Automatically determine predecessor if not provided
        if predecessor is None or successor is None:
            predecessor, successor = self.get_predecessor_successor(new_id)

        # Create and add the new actuator
        actuator = Actuator(x, y, self.actuator_size, color, actuator_type, new_id, predecessor, successor)
        self.scene.addItem(actuator)
        self.actuators.append(actuator)
        actuator.setZValue(0)  # Ensure actuator is above the lines

        # Update predecessor's successor to the newly added actuator
        if predecessor:
            pred_actuator = self.get_actuator_by_id(predecessor)
            if pred_actuator:
                pred_actuator.successor = new_id  # Update the predecessor's successor to the new actuator
                pred_actuator.update()

                # Draw a line from the predecessor to the newly added actuator
                line = QLineF(pred_actuator.pos(), actuator.pos())
                line_item = self.scene.addLine(line, QPen(Qt.GlobalColor.black, 2))
                line_item.setZValue(-1)  # Ensure the line is behind the actuators
                self.draw_arrowhead(line)  # Draw the arrowhead

        # Draw an arrow connecting to the successor (if applicable)
        if successor:
            for act in self.actuators:
                if act.id == successor:
                    line = QLineF(actuator.pos(), act.pos())
                    line_item = self.scene.addLine(line, QPen(Qt.GlobalColor.black, 2))
                    line_item.setZValue(-1)  # Ensure the line is behind the actuators
                    self.draw_arrowhead(line)
                    break

        actuator.update()  # Update the new actuator to reflect changes

        # Emit signal indicating the actuator has been added
        self.actuator_added.emit(new_id, actuator_type, color.name(), x, y)


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
        while True:
            if dialog.exec() == QDialog.DialogCode.Accepted:
                old_id = actuator.id
                new_id = dialog.id_input.text()

                # Check for ID conflicts
                if any(act.id == new_id and act != actuator for act in self.actuators):
                    # Show a warning message if there's a conflict
                    QMessageBox.warning(self, "ID Conflict Detected", f"Actuator ID '{new_id}' already exists. Please choose a different ID.")
                    continue  # Reopen the dialog for the user to change the ID
                
                actuator.id = new_id
                
                # Update color if branch has changed
                old_branch = old_id.split('.')[0]
                new_branch = new_id.split('.')[0]
                if old_branch != new_branch:
                    if actuator.predecessor:
                        print("pred", actuator.predecessor)
                        predecessor_actuator = self.get_actuator_by_id(actuator.predecessor)
                        if predecessor_actuator:
                            predecessor_actuator.successor = None
                        
                    if actuator.successor:
                        print("succ", actuator.successor)
                        successor_actuator = self.get_actuator_by_id(actuator.successor)
                        if successor_actuator:
                            successor_actuator.predecessor = None

                    if new_branch not in self.branch_colors:
                        if self.color_index < len(COLOR_LIST):
                            self.branch_colors[new_branch] = COLOR_LIST[self.color_index]
                            self.color_index += 1
                        else:
                            self.branch_colors[new_branch] = generate_contrasting_color(list(self.branch_colors.values()))
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
                
                if old_branch != new_branch:
                    actuator.predecessor = None
                    actuator.successor = None
                
                actuator.update()
                
                # Update other actuators if necessary
                self.update_related_actuators(old_id, new_id)

                self.properties_changed.emit(old_id, new_id, new_type, actuator.color.name())

                # Update plotter immediately
                self.haptics_app.update_timeline_actuator(old_id, new_id, new_type, actuator.color.name())

                self.redraw_all_lines()  # Trigger a redraw of all lines

                break  # Exit the loop if everything is fine

            else:
                break  # Exit if the dialog is canceled



    def update_related_actuators(self, old_id, new_id):
        for act in self.actuators:
            if act.predecessor == old_id:
                act.predecessor = new_id
            if act.successor == old_id:
                act.successor = new_id
            act.update()

    def remove_actuator(self, actuator):
        """Remove an actuator and update its predecessor and successor appropriately."""
        if actuator.predecessor or actuator.successor:
            predecessor_actuator = self.get_actuator_by_id(actuator.predecessor) if actuator.predecessor else None
            successor_actuator = self.get_actuator_by_id(actuator.successor) if actuator.successor else None

            # Handle the case of A-B-C, where B is being deleted
            if predecessor_actuator and successor_actuator:
                # Update A's successor to be C
                predecessor_actuator.successor = successor_actuator.id
                predecessor_actuator.update()

                # Update C's predecessor to be A
                successor_actuator.predecessor = predecessor_actuator.id
                successor_actuator.update()

            elif predecessor_actuator:
                # If there is only a predecessor (no successor), just remove the successor reference from A
                predecessor_actuator.successor = None
                predecessor_actuator.update()

            elif successor_actuator:
                # If there is only a successor (no predecessor), just remove the predecessor reference from C
                successor_actuator.predecessor = None
                successor_actuator.update()

        # Ensure that both predecessors and successors are unique after deletion
        #self.ensure_unique_connections()

        # Remove the actuator from the scene
        self.actuators.remove(actuator)
        self.scene.removeItem(actuator)
        self.actuator_deleted.emit(actuator.id)  # Emit the deletion signal

        # Redraw all lines after deletion
        self.redraw_all_lines()

    # def ensure_unique_connections(self):
    #     """Ensure all actuators have unique predecessors and successors."""
    #     seen_predecessors = set()
    #     seen_successors = set()

    #     for actuator in self.actuators:
    #         if actuator.predecessor in seen_predecessors:
    #             actuator.predecessor = None  # Clear the duplicate predecessor
    #             actuator.update()

    #         if actuator.successor in seen_successors:
    #             actuator.successor = None  # Clear the duplicate successor
    #             actuator.update()

    #         # Track unique predecessors and successors
    #         if actuator.predecessor:
    #             seen_predecessors.add(actuator.predecessor)
    #         if actuator.successor:
    #             seen_successors.add(actuator.successor)

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
        self.axes = self.fig.add_axes([0.1, 0.15, 0.8, 0.8])  # Use add_axes to create a single plot
        self.axes.set_facecolor(color)
        
        # Set spine color and customize appearance
        spine_color = to_rgba((240/255, 235/255, 229/255))
        self.axes.spines['bottom'].set_color(spine_color)
        self.axes.spines['top'].set_color(spine_color)
        self.axes.spines['right'].set_color(spine_color)
        self.axes.spines['left'].set_color(spine_color)
        self.axes.tick_params(axis='x', colors=spine_color, labelsize=8)
        self.axes.tick_params(axis='y', colors=spine_color, labelsize=8)
        self.axes.set_ylabel('Amplitude', fontsize=9.5, color=spine_color)
        self.set_custom_xlabel('Time (s)', fontsize=9.5, color=spine_color)
        
        super(TimelineCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.setStyleSheet(f"background-color: rgba({int(color[0]*255)}, {int(color[1]*255)}, {int(color[2]*255)}, 0);")
        self.setAcceptDrops(True)
        
        self.signals = []  # List to store each signal's data along with their parameters

        # Variables to track dragging
        self._dragging = False
        self._last_mouse_x = None

        # dragggg
        self.signal_duration = 0  # Store the signal duration

    # dragggg
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.signal_duration > 10:
            self._dragging = True
            self._last_mouse_x = event.position().x()
    # dragggg
    def mouseMoveEvent(self, event):
        if self._dragging and self.signal_duration > 10:
            dx = event.position().x() - self._last_mouse_x
            self._last_mouse_x = event.position().x()
            xmin, xmax = self.axes.get_xlim()
            delta_x = dx * (xmax - xmin) / self.fig.get_size_inches()[0] / self.fig.dpi
            # Limit dragging to the signal duration
            if xmin - delta_x >= 0 and xmax - delta_x <= self.signal_duration:
                self.axes.set_xlim(xmin - delta_x, xmax - delta_x)
                self.draw()
    # dragggg
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False

    def check_overlap(self, new_start_time, new_stop_time):
        for signal in self.signals:
            if not (new_stop_time <= signal["start_time"] or new_start_time >= signal["stop_time"]):
                return True
        return False

    def handle_overlap(self, new_start_time, new_stop_time, signal_type, signal_data, parameters):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Time Range Overlap")
        msg_box.setText(f"The time range overlaps with an existing signal.")
        msg_box.setInformativeText("Would you like to replace the overlapping region or reset the time range of the new signal?")

        replace_button = msg_box.addButton("Replace", QMessageBox.ButtonRole.YesRole)
        reset_button = msg_box.addButton("Reset", QMessageBox.ButtonRole.NoRole)

        msg_box.exec()

        if msg_box.clickedButton() == replace_button:
            self.replace_overlap(new_start_time, new_stop_time, signal_data, signal_type, parameters)
        else:
            # Adjust the previous signal to keep non-overlapping parts
            self.adjust_previous_signals(new_start_time, new_stop_time)

            # Prompt the user to set a new time range for the new signal
            start_time, stop_time = self.show_time_input_dialog(signal_type)
            if start_time is not None and stop_time is not None and stop_time > start_time:
                if self.check_overlap(start_time, stop_time):
                    self.handle_overlap(start_time, stop_time, signal_type, signal_data)
                else:
                    self.record_signal(signal_type, signal_data, start_time, stop_time, None)


    def replace_overlap(self, new_start_time, new_stop_time, new_signal_data, new_signal_type, new_signal_parameters):
        adjusted_signals = []

        for signal in self.signals:
            if signal["start_time"] < new_start_time < signal["stop_time"]:
                # Case: The new signal overlaps the end of this signal
                if new_stop_time < signal["stop_time"]:
                    # Trim the end of the original signal and keep the non-overlapping part
                    signal_part = {
                        "type": signal["type"],
                        "data": signal["data"][:int((new_start_time - signal["start_time"]) * 500)],
                        "start_time": signal["start_time"],
                        "stop_time": new_start_time,
                        "parameters": signal["parameters"]
                    }
                    adjusted_signals.append(signal_part)
                else:
                    # Remove the overlapping portion of the original signal
                    signal["stop_time"] = new_start_time
                    signal["data"] = signal["data"][:int((new_start_time - signal["start_time"]) * 500)]
                    adjusted_signals.append(signal)

            elif signal["start_time"] < new_stop_time < signal["stop_time"]:
                # Case: The new signal overlaps the start of this signal
                signal["start_time"] = new_stop_time
                signal["data"] = signal["data"][int((new_stop_time - signal["start_time"]) * 500):]
                adjusted_signals.append(signal)

            elif new_start_time <= signal["start_time"] and new_stop_time >= signal["stop_time"]:
                # Case: The new signal completely overlaps this signal, so the original signal is removed

                continue
            else:
                # No overlap, keep the signal as is
                adjusted_signals.append(signal)

        # Add the new signal as well
        adjusted_signals.append({
            "type": new_signal_type,
            "data": new_signal_data,
            "start_time": new_start_time,
            "stop_time": new_stop_time,
            "parameters": new_signal_parameters
        })

        print(adjusted_signals)

        self.signals = adjusted_signals
        self.plot_all_signals()  # Update the plot with the modified signals


    def adjust_previous_signals(self, new_start_time, new_stop_time):
        adjusted_signals = []
        for signal in self.signals:
            if signal["start_time"] < new_start_time < signal["stop_time"]:
                # Case: The new signal overlaps the end of this signal
                if new_stop_time < signal["stop_time"]:
                    # Trim the end of the original signal and keep the non-overlapping part
                    signal_part = {
                        "type": signal["type"],
                        "data": signal["data"][:int((new_start_time - signal["start_time"]) * 500)],
                        "start_time": signal["start_time"],
                        "stop_time": new_start_time,
                        "parameters": signal["parameters"]
                    }
                    adjusted_signals.append(signal_part)
                else:
                    # Remove the overlapping portion of the original signal
                    signal["stop_time"] = new_start_time
                    signal["data"] = signal["data"][:int((new_start_time - signal["start_time"]) * 500)]
                    adjusted_signals.append(signal)
            elif signal["start_time"] < new_stop_time < signal["stop_time"]:
                # Case: The new signal overlaps the start of this signal
                signal["start_time"] = new_stop_time
                signal["data"] = signal["data"][int((new_stop_time - signal["start_time"]) * 500):]
                adjusted_signals.append(signal)
            elif signal["start_time"] < new_start_time and signal["stop_time"] > new_stop_time:
                # Case: The new signal completely overlaps this signal
                signal_part1 = {
                    "type": signal["type"],
                    "data": signal["data"][:int((new_start_time - signal["start_time"]) * 500)],
                    "start_time": signal["start_time"],
                    "stop_time": new_start_time,
                    "parameters": signal["parameters"]
                }
                signal_part2 = {
                    "type": signal["type"],
                    "data": signal["data"][int((new_stop_time - signal["start_time"]) * 500):],
                    "start_time": new_stop_time,
                    "stop_time": signal["stop_time"],
                    "parameters": signal["parameters"]
                }
                adjusted_signals.extend([signal_part1, signal_part2])
            else:
                # No overlap, keep the signal as is
                adjusted_signals.append(signal)

        self.signals = adjusted_signals


    def set_custom_xlabel(self, xlabel, fontsize=9.5, color='black'):
        self.axes.set_xlabel('')  # Remove default xlabel
        self.axes.annotate(xlabel, xy=(1.01, -0.01), xycoords='axes fraction', fontsize=fontsize, color=color, ha='left', va='center')

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        # Get the dragged signal type
        item = event.source().selectedItems()[0]
        signal_type = item.text(0)

        # Determine if the signal is customized or imported
        if signal_type in self.app_reference.custom_signals or signal_type in self.app_reference.imported_signals:
            signal_data = self.get_signal_data(signal_type)
            if signal_data:
                start_time, stop_time = self.show_time_input_dialog(signal_type)
                if start_time is not None and stop_time is not None and stop_time > start_time:
                    if self.check_overlap(start_time, stop_time):
                        self.handle_overlap(start_time, stop_time, signal_type, signal_data, parameters)
                    else:
                        self.record_signal(signal_type, signal_data, start_time, stop_time, None)
        else:
            parameters = self.prompt_signal_parameters(signal_type)
            if parameters is not None:
                start_time, stop_time = self.show_time_input_dialog(signal_type)
                if start_time is not None and stop_time is not None and stop_time > start_time:
                    signal_data = self.generate_signal_data(signal_type, parameters)
                    if self.check_overlap(start_time, stop_time):
                        self.handle_overlap(start_time, stop_time, signal_type, signal_data, parameters)
                    else:
                        self.record_signal(signal_type, signal_data, start_time, stop_time, parameters)

        # After recording the new signal, update the plot
        if self.signals:
            self.plot_all_signals()

        self.app_reference.actuator_signals[self.app_reference.current_actuator] = self.signals
        self.app_reference.update_actuator_text()


    def prompt_signal_parameters(self, signal_type):
        # This method prompts the user to modify the signal parameters using a dialog.
        if signal_type in ["Sine", "Square", "Saw", "Triangle", "Chirp", "FM", "PWM", "Noise"]:
            dialog = OscillatorDialog(signal_type, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                return dialog.get_config()
        elif signal_type in ["Envelope", "Keyed Envelope", "ASR", "ADSR", "Exponential Decay", "PolyBezier", "Signal Envelope"]:
            dialog = EnvelopeDialog(signal_type, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                return dialog.get_config()
        return None

    def record_signal(self, signal_type, signal_data, start_time, stop_time, parameters):
        # Record the signal data and its parameters into the signals list
        self.signals.append({
            "type": signal_type,
            "data": signal_data,
            "start_time": start_time,
            "stop_time": stop_time,
            "parameters": parameters
        })

    def plot_all_signals(self):
        if not self.signals:
            # If no signals recorded, render a default plot with 10 seconds of 0 amplitude
            default_duration = 10  # seconds
            t = np.linspace(0, default_duration, 500 * default_duration)
            signal_data = np.zeros_like(t)
            self.plot_signal_data(t, signal_data)
            return

        # Determine the max stop time across all recorded signals
        max_stop_time = max([signal["stop_time"] for signal in self.signals])

        # dragggg
        # Store the signal duration for use in dragging functionality
        self.signal_duration = max_stop_time

        # Initialize an empty array of zeros for the full duration
        total_samples = int(max_stop_time * 500)
        combined_signal = np.zeros(total_samples)

        # Fill in the combined signal with each recorded signal's data
        for signal in self.signals:
            start_sample = int(signal["start_time"] * 500)
            stop_sample = int(signal["stop_time"] * 500)
            signal_duration = stop_sample - start_sample
            # Adjust the signal_data to fit the required duration (stretch or truncate as needed)
            if len(signal["data"]) > 0:
                signal_data = np.tile(signal["data"], int(np.ceil(signal_duration / len(signal["data"]))))[:signal_duration]
            else:
                # Handle the case where signal["data"] is empty
                # You can either skip this signal or generate a default signal.
                print(f"Warning: signal data is empty for signal {signal['type']}.")
                signal_data = np.zeros(signal_duration)  # Fallback to an empty signal for this duration

            combined_signal[start_sample:stop_sample] = signal_data

        # Generate time array for the x-axis
        t = np.linspace(0, max_stop_time, total_samples)
        self.plot_signal_data(t, combined_signal)

    def plot_signal_data(self, t, signal_data):
        # Clear the current plot and plot the new signal
        self.axes.clear()
        # Set spine color and customize appearance
        spine_color = to_rgba((240/255, 235/255, 229/255))
        self.axes.spines['bottom'].set_color(spine_color)
        self.axes.spines['top'].set_color(spine_color)
        self.axes.spines['right'].set_color(spine_color)
        self.axes.spines['left'].set_color(spine_color)
        self.axes.tick_params(axis='x', colors=spine_color, labelsize=8)
        self.axes.tick_params(axis='y', colors=spine_color, labelsize=8)
        self.axes.set_ylabel('Amplitude', fontsize=9.5, color=spine_color)
        self.set_custom_xlabel('Time (s)', fontsize=9.5, color=spine_color)

        # Plot the signal data
        self.axes.plot(t, signal_data, color=spine_color)

        # dragggg
        # Check if the signal is longer than 10 seconds
        if self.signal_duration > 10:
            self.axes.set_xlim(0, 10)  # Show only the first 10 seconds initially
      

        self.draw()

    def generate_signal_data(self, signal_type, parameters):
        # Generate the signal data based on the type and modified parameters
        
        if signal_type == "Sine":
            t = np.linspace(0, 1, 500)
            return np.sin(2 * np.pi * parameters["frequency"] * t).tolist()
        elif signal_type == "Square":
            t = np.linspace(0, 1, 500)
            return np.sign(np.sin(2 * np.pi * parameters["frequency"] * t)).tolist()
        elif signal_type == "Saw":
            t = np.linspace(0, 1, 500)
            return (2 * (t * parameters["frequency"] - np.floor(t * parameters["frequency"] + 0.5))).tolist()
        elif signal_type == "Triangle":
            t = np.linspace(0, 1, 500)
            return (2 * np.abs(2 * (t * parameters["frequency"] - np.floor(t * parameters["frequency"] + 0.5))) - 1).tolist()
        elif signal_type == "Chirp":
            t = np.linspace(0, 1, 500)
            return np.sin(2 * np.pi * (parameters["frequency"] * t + 0.5 * parameters["rate"] * t**2)).tolist()
        elif signal_type == "FM":
            t = np.linspace(0, 1, 500)
            return np.sin(2 * np.pi * (parameters["frequency"] * t + parameters["rate"] * np.sin(2 * np.pi * parameters["frequency"] * t))).tolist()
        elif signal_type == "PWM":
            t = np.linspace(0, 1, 500)
            return np.where(np.sin(2 * np.pi * parameters["frequency"] * t) >= 0, 1, -1).tolist()
        elif signal_type == "Noise":
            t = np.linspace(0, 1, 500)
            return np.random.normal(0, 1, len(t)).tolist()
        elif signal_type == "Envelope":
            duration = parameters["duration"]
            num_samples = int(duration * 500)
            t = np.linspace(0, duration, num_samples)
            return (parameters["amplitude"] * np.sin(2 * np.pi * 5 * t)).tolist()
        elif signal_type == "Keyed Envelope":
            duration = parameters["duration"]
            num_samples = int(duration * 500)
            t = np.linspace(0, duration, num_samples)
            return (parameters["amplitude"] * np.sin(2 * np.pi * 5 * t) * np.exp(-3 * t)).tolist()
        elif signal_type == "ASR":
            duration = parameters["duration"]
            num_samples = int(duration * 500)
            t = np.linspace(0, duration, num_samples)
            return np.piecewise(t, [t < 0.3 * duration, t >= 0.3 * duration],
                                [lambda t: parameters["amplitude"] * (t / (0.3 * duration)), parameters["amplitude"]]).tolist()
        elif signal_type == "ADSR":
            duration = parameters["duration"]
            num_samples = int(duration * 500)
            t = np.linspace(0, duration, num_samples)
            return np.piecewise(t, [t < 0.1 * duration, t < 0.2 * duration, t < 0.5 * duration, t < 0.7 * duration, t >= 0.7 * duration],
                                [lambda t: parameters["amplitude"] * (t / (0.1 * duration)),
                                lambda t: parameters["amplitude"] * (1 - 5 * (t - 0.1 * duration) / duration),
                                0.5 * parameters["amplitude"],
                                lambda t: 0.5 * parameters["amplitude"] - 0.25 * parameters["amplitude"] * (t - 0.5 * duration) / duration,
                                0.25 * parameters["amplitude"]]).tolist()
        elif signal_type == "Exponential Decay":
            duration = parameters["duration"]
            num_samples = int(duration * 500)
            t = np.linspace(0, duration, num_samples)
            return (parameters["amplitude"] * np.exp(-5 * t / parameters["duration"])).tolist()
        elif signal_type == "PolyBezier":
            duration = parameters["duration"]
            num_samples = int(duration * 500)
            t = np.linspace(0, duration, num_samples)
            return (parameters["amplitude"] * (t ** 3 - 3 * t ** 2 + 3 * t)).tolist()
        elif signal_type == "Signal Envelope":
            duration = parameters["duration"]
            num_samples = int(duration * 500)
            t = np.linspace(0, duration, num_samples)
            return (parameters["amplitude"] * np.abs(np.sin(2 * np.pi * 3 * t))).tolist()
        return np.zeros_like(t).tolist()

    def get_signal_data(self, signal_type):
        # Retrieve signal data based on signal_type
        if signal_type in self.app_reference.custom_signals:
            return self.app_reference.custom_signals[signal_type]["data"]
        elif signal_type in self.app_reference.imported_signals:
            return self.app_reference.imported_signals[signal_type]["data"]
        return None

    def show_time_input_dialog(self, signal_type):
        dialog = TimeInputDialog(signal_type)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            start_time = dialog.start_time_input.value()
            stop_time = dialog.stop_time_input.value()
            return start_time, stop_time
        return None, None


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

        self.statusBar().showMessage("Welcome to Haptics App")

        # Add a flag to track the first signal drop
        self.first_signal_drop = 0
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

        # Add a dictionary to store signals for each actuator
        self.actuator_signals = {}

        # Initialize timeline_canvases as an empty dictionary
        self.timeline_canvases = {}

        # Instantiate DesignSaver
        self.design_saver = DesignSaver(self.actuator_canvas, self.timeline_canvases, self.maincanvas, self)

        # Connect the "Save As..." action to the save_design method
        self.ui.actionSave_New_Design.triggered.connect(self.design_saver.save_design)

        self.ui.actionStart_New_Design.triggered.connect(self.design_saver.load_design)

    def update_actuator_text(self):
        # Find the global largest stop time across all actuators
        all_stop_times = []
        for signals in self.actuator_signals.values():
            all_stop_times.extend([signal["stop_time"] for signal in signals])

        if all_stop_times:
            global_total_time = max(all_stop_times)
        else:
            global_total_time = 1  # Avoid division by zero in the width calculation

        # Update the visual timeline for each actuator widget
        for actuator_id, (actuator_widget, actuator_label) in self.timeline_widgets.items():
            if actuator_id in self.actuator_signals:
                signals = self.actuator_signals[actuator_id]

                # Remove all existing signal widgets from the actuator widget layout, but keep the ID and type
                # Assuming the first widget in the layout is the actuator label (ID and type)
                for i in reversed(range(1, actuator_widget.layout().count())):  # Start from index 1 to avoid removing the ID label
                    item = actuator_widget.layout().takeAt(i)
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
                    else:
                        del item  # Remove spacers

                # Set up the layout for the actuator widget if not already done
                if not actuator_widget.layout():
                    layout = QtWidgets.QHBoxLayout()
                    actuator_widget.setLayout(layout)
                    layout.setContentsMargins(0, 0, 0, 0)
                    layout.setSpacing(5)  # Add spacing between the ID/Type and the signals

                # Ensure the ID/Type label stays in the first position
                if actuator_label.parent() is None:
                    actuator_widget.layout().insertWidget(0, actuator_label)  # Add ID/Type label at the beginning

                # Create a container for the timeline and signal widgets
                timeline_container = QtWidgets.QWidget(actuator_widget)
                timeline_container.setStyleSheet("background-color: transparent;")
                timeline_container.setFixedHeight(30)  # Slightly taller than the signal widgets to create the layering effect
                timeline_layout = QtWidgets.QHBoxLayout(timeline_container)
                timeline_layout.setContentsMargins(0, 0, 0, 0)
                timeline_layout.setSpacing(0)

                # Calculate the width of the actuator widget based on the global total time
                widget_width = actuator_widget.size().width()

                # Track the last stop time to insert gaps
                last_stop_time = 0

                # Sort signals by start time
                signals.sort(key=lambda signal: signal["start_time"])

                for signal in signals:
                    # Calculate the relative width of the signal widget based on its duration
                    signal_duration = signal["stop_time"] - signal["start_time"]
                    signal_width_ratio = signal_duration / global_total_time
                    signal_width = int(signal_width_ratio * widget_width)

                    # Calculate the relative starting position of the signal widget
                    signal_start_ratio = signal["start_time"] / global_total_time
                    signal_start_position = int(signal_start_ratio * widget_width)

                    # If there is a gap between the last signal's stop time and this signal's start time, add a spacer
                    if signal["start_time"] > last_stop_time:
                        gap_duration = signal["start_time"] - last_stop_time
                        gap_width_ratio = gap_duration / global_total_time
                        gap_width = int(gap_width_ratio * widget_width)

                        # Add a spacer to represent the gap
                        spacer = QtWidgets.QSpacerItem(gap_width, 30, QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Minimum)
                        timeline_layout.addItem(spacer)

                    # Create the signal widget, making it smaller vertically and with rounded corners
                    signal_widget = QtWidgets.QLabel(f'{signal["type"]} ({", ".join([f"{k}: {v}" for k, v in (signal["parameters"] or {}).items()])})')
                    signal_widget.setFixedSize(signal_width, 30)  # Set smaller height for the signal widget
                    signal_widget.setStyleSheet("""
                        background-color: rgba(100, 150, 250, 150); 
                        color: white; 
                        border-radius: 7px;
                        padding: 3px;
                    """)

                    # Add the signal widget to the layout
                    timeline_layout.addWidget(signal_widget)

                    # Update the last stop time
                    last_stop_time = signal["stop_time"]

                # Add a stretch to fill the remaining space
                timeline_layout.addStretch()

                # Add the timeline container to the actuator widget after the ID and type
                actuator_widget.layout().addWidget(timeline_container)


    def connect_actuator_signals(self, actuator_id, actuator_type, color, x, y):
        actuator = self.actuator_canvas.get_actuator_by_id(actuator_id)
        if actuator:
            actuator.signal_handler.clicked.connect(self.on_actuator_clicked)
            actuator.signal_handler.properties_changed.connect(self.update_plotter)


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

        # Store the TimelineCanvas in the dictionary
        self.timeline_canvases[actuator_id] = self.timeline_canvas

        # Retrieve and plot the signal data for this actuator
        # Retrieve and plot the signal data for this actuator
        if actuator_id in self.actuator_signals:
            self.timeline_canvas.signals = self.actuator_signals[actuator_id]
            self.timeline_canvas.plot_all_signals()

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
        self.actuator_signals.clear()  # Clear the stored signals

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
    


    def add_actuator_to_timeline(self, new_id, actuator_type, color, x, y):
        # Convert the color to a suitable format for the stylesheet
        color_rgb = QColor(color).getRgbF()[:3]
        color_style = f"background-color: rgba({int(color_rgb[0]*255)}, {int(color_rgb[1]*255)}, {int(color_rgb[2]*255)}, 255);"

        # Create a placeholder widget instead of TimelineCanvas
        actuator_widget = QWidget(parent=self.ui.scrollAreaWidgetContents)
        actuator_widget.setStyleSheet(color_style)  # Apply the background color

        # Add a simple label to represent the actuator in the timeline area
        actuator_layout = QHBoxLayout(actuator_widget)
        actuator_label = QLabel(f"{actuator_type} - {new_id}")
        actuator_label.setStyleSheet("color: white;")  # Ensure text is visible
        actuator_layout.addWidget(actuator_label)
        
        # Add the widget to the timeline layout
        self.timeline_layout.addWidget(actuator_widget)
        self.timeline_widgets[new_id] = (actuator_widget, actuator_label)


    def update_timeline_actuator(self, old_actuator_id, new_actuator_id, actuator_type, color):
        if old_actuator_id in self.timeline_widgets:
            actuator_widget, actuator_label = self.timeline_widgets.pop(old_actuator_id)
            
            # Convert the color to a suitable format for the stylesheet
            color_rgb = QColor(color).getRgbF()[:3]
            color_style = f"background-color: rgba({int(color_rgb[0]*255)}, {int(color_rgb[1]*255)}, {int(color_rgb[2]*255)}, 255);"
            
            # Update the widget's background color
            actuator_widget.setStyleSheet(color_style)
            
            # Update the label text
            actuator_label.setText(f"{actuator_type} - {new_actuator_id}")
            
            # Store the updated reference with the new ID
            self.timeline_widgets[new_actuator_id] = (actuator_widget, actuator_label)
            
            # Update the actuator_signals dictionary to reflect the ID change
            if old_actuator_id in self.actuator_signals:
                self.actuator_signals[new_actuator_id] = self.actuator_signals.pop(old_actuator_id)

            # Immediately update the plotter to reflect the changes
            self.update_plotter(new_actuator_id, actuator_type, color)



   
            
    def remove_actuator_from_timeline(self, actuator_id):
        if actuator_id in self.timeline_widgets:
            actuator_widget, actuator_label = self.timeline_widgets.pop(actuator_id)
            self.timeline_layout.removeWidget(actuator_widget)
            actuator_widget.deleteLater()  # Properly delete the widget
        
        # Remove the associated signal data
        if actuator_id in self.actuator_signals:
            del self.actuator_signals[actuator_id]


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


        # Disable drag by default
        tree.setDragEnabled(False)

        # Connect to itemPressed to control dragging behavior
        tree.itemPressed.connect(self.on_tree_item_pressed)
        
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

    def on_tree_item_pressed(self, item, column):
        # Enable dragging only if the item is a child item (i.e., it has a parent)
        if item.parent() is not None:
            self.ui.treeWidget.setDragEnabled(True)
        else:
            self.ui.treeWidget.setDragEnabled(False)

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
        print("start save")
        print("save",self.first_signal_drop)
        # Check if the first signal has been saved
        if self.first_signal_drop == 1:
            print("first signal")
            # Always prompt "Signal already exists" for the first signal and do not save it
            QMessageBox.information(self, "Reminder", "Signal already exists!", QMessageBox.StandardButton.Ok)
            # self.first_signal_drop = False  # Set the flag to False after the first attempt
            return  # Do not proceed with saving the signal

        # Continue with saving for subsequent signals
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
                QMessageBox.information(self, "Reminder", "Signal already exists!", QMessageBox.StandardButton.Ok)
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
