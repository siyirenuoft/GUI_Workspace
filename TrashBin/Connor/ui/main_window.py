from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog, QVBoxLayout, QWidget, QInputDialog
from PyQt5.QtCore import Qt
from ui.waveform_canvas import WaveformCanvas
from controllers.file_loader import load_waveform

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Haptics Pattern Design App")

        self.initUI()

    def initUI(self):
        self.createMenuBar()
        self.createCentralWidget()

    def createMenuBar(self):
        menubar = self.menuBar()
        
        fileMenu = menubar.addMenu('File')
        
        newWorkspaceAction = QAction('New Workspace', self)
        fileMenu.addAction(newWorkspaceAction)
        
        loadFileAction = QAction('Load File', self)
        loadFileAction.triggered.connect(self.loadFile)
        fileMenu.addAction(loadFileAction)

    def createCentralWidget(self):
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)
        self.layout = QVBoxLayout(self.centralWidget)

        self.waveformCanvas = WaveformCanvas(self)
        self.layout.addWidget(self.waveformCanvas)

    def loadFile(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Load Waveform CSV", "", "CSV Files (*.csv)", options=options)
        if fileName:
            samplingFrequency, ok = QInputDialog.getInt(self, 'Sampling Frequency', 'Enter the sampling frequency:')
            if ok:
                waveform = load_waveform(fileName, samplingFrequency)
                self.waveformCanvas.displayWaveform(waveform)
