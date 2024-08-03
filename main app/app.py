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


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.axes.set_facecolor((0.94,0.94,0.94))
        super(MplCanvas, self).__init__(fig)
        fig.tight_layout()

class Haptics_App(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi('layout.ui', self)
        self.resize(1500, 900)
        icon = QtGui.QIcon()
        icon_path = "resources/logo.jpg"
        
        if os.path.exists(icon_path):
            icon.addPixmap(QtGui.QPixmap(icon_path), QIcon.Mode.Normal, QIcon.State.Off)
            self.setWindowIcon(icon)
        else:
            print(f"Icon file not found at path: {icon_path}")

        self.threadpool = QtCore.QThreadPool()




# www.pyshine.com
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
