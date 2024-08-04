from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt

class WaveformCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.waveform = None

    def displayWaveform(self, waveform):
        self.waveform = waveform
        self.update()

    def paintEvent(self, event):
        if self.waveform is None:
            return

        painter = QPainter(self)
        pen = QPen(Qt.black, 2, Qt.SolidLine)
        painter.setPen(pen)
        
        width = self.width()
        height = self.height()
        num_samples = len(self.waveform.data)
        
        max_magnitude = max(self.waveform.data)
        min_magnitude = min(self.waveform.data)
        
        for i in range(1, num_samples):
            x1 = int((i - 1) * width / num_samples)
            y1 = int(height - ((self.waveform.data[i - 1] - min_magnitude) / (max_magnitude - min_magnitude) * height))
            x2 = int(i * width / num_samples)
            y2 = int(height - ((self.waveform.data[i] - min_magnitude) / (max_magnitude - min_magnitude) * height))
            painter.drawLine(x1, y1, x2, y2)
