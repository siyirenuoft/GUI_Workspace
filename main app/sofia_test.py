import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("QTreeWidget")
        self.setGeometry(100, 100, 300, 400)
        
        tree = QTreeWidget(self)
        tree.setHeaderHidden(True)
        tree.setGeometry(10, 10, 280, 380)
        
        # Create top-level items
        oscillators = QTreeWidgetItem(tree)
        oscillators.setText(0, "Oscillators")
        
        envelopes = QTreeWidgetItem(tree)
        envelopes.setText(0, "Envelopes")
        
        # Add child items to "Oscillators"
        osc_items = ["Sine", "Square", "Saw", "Triangle", "Chirp", "FM", "PWM", "Noise"]
        for item in osc_items:
            child = QTreeWidgetItem(oscillators)
            child.setText(0, item)
        
        # Add child items to "Envelopes"
        env_items = ["Envelope", "Keyed Envelope", "ASR", "ADSR", "Exponential Decay", "PolyBezier", "Signal Envelope"]
        for item in env_items:
            child = QTreeWidgetItem(envelopes)
            child.setText(0, item)
        
        # Expand all items by default
        tree.expandAll()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
