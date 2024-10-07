from PyQt6.QtCore import QThread, QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from time import perf_counter

class TimelineTimer(QObject):
    # Signals to communicate with other components
    time_updated = pyqtSignal(float)  # Emitted every 5 ms with the updated current time

    def __init__(self):
        super().__init__()
        self.playing = False  # Indicates whether the timer is playing or paused
        self.current_time = 0.0  # Keeps track of the timeline's current time
        self.update_interval = 5  # 5 ms interval in milliseconds

        # Create a QTimer
        self.timer = QTimer()
        self.timer.setInterval(self.update_interval)
        self.timer.timeout.connect(self.update)
        self.timer.start()

    def update(self):
        """Update the current time and emit the time_updated signal."""
        if self.playing:
            print("timeline timer, ", perf_counter())
            self.current_time += self.update_interval / 1000.0  # Convert ms to seconds
            self.current_time = round(self.current_time, 6)
            self.time_updated.emit(self.current_time)

    def play(self):
        """Start progressing the timeline forward."""
        self.playing = True

    def pause(self):
        """Pause the timeline."""
        self.playing = False

    def reset(self):
        """Reset the timeline to the initial state."""
        self.playing = False
        self.current_time = 0.0

    def manual_update(self, current_time):
        """Manually update the timeline's current time."""
        self.playing = False
        self.current_time = current_time


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Timeline Timer Example")
        self.setGeometry(100, 100, 400, 200)

        # Create a thread
        self.thread = QThread()

        # Create timeline worker and move it to the thread
        self.timeline_worker = TimelineTimer()
        self.timeline_worker.moveToThread(self.thread)

        # Start the worker's timer when the thread starts
        # self.thread.started.connect(self.timeline_worker.start)
        self.timeline_worker.time_updated.connect(self.on_time_updated)

        # Start the thread
        self.thread.start()

        # Create play/pause buttons
        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Pause")

        self.play_button.clicked.connect(self.timeline_worker.play)
        self.pause_button.clicked.connect(self.timeline_worker.pause)

        # Set up layout
        layout = QVBoxLayout()
        layout.addWidget(self.play_button)
        layout.addWidget(self.pause_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def on_time_updated(self, current_time):
        print(f"Current Time: {current_time:.6f} s")

    def closeEvent(self, event):
        # Stop the timeline worker and the thread when the window is closed
        self.thread.quit()
        self.thread.wait()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
