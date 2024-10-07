from time import perf_counter
import time
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget

class TimelineTimer(QThread):
    # Signals to communicate with other components
    time_updated = pyqtSignal(float)  # Emitted every 5 ms with the updated current time

    def __init__(self):
        super().__init__()
        self.playing = False  # Indicates whether the timer is playing or paused
        self.current_time = 0.0  # Keeps track of the timeline's current time
        self.update_interval = 0.005  # 5 ms interval
        self.sleep_interval = 0.001 # 1 ms interval

    def run(self):
        last_update_time = perf_counter()
        print("Timer started")
        while True:
            now = perf_counter()
            if now - last_update_time >= self.update_interval:
                self.update()
                last_update_time = now
            # Ensure the thread sleeps for the correct amount of time
            time.sleep(self.sleep_interval)

    def update(self):
        """Update the current time and emit the time_updated signal."""
        if self.playing:
            self.current_time += self.update_interval
            self.time_updated.emit(self.current_time)

    def play(self):
        """Start progressing the timeline forward."""
        self.playing = True

    def pause(self):
        """Pause the timeline."""
        self.playing = False

    # plays till the end of the timeline
    def reset(self):
        """Reset the timeline to the initial state."""
        self.current_time = 0.0

    # if the user manually moves the slider, update the current time
    def manual_update(self, current_time):
        """Manually update the timeline's current time."""
        self.current_time = current_time



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Timeline Timer Example")
        self.setGeometry(100, 100, 400, 200)

        # Create timeline timer instance
        self.timeline_timer = TimelineTimer()
        self.timeline_timer.time_updated.connect(self.on_time_updated)
        self.timeline_timer.start()

        # Create play/pause buttons
        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Pause")

        self.play_button.clicked.connect(self.timeline_timer.play)
        self.pause_button.clicked.connect(self.timeline_timer.pause)

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
        # Stop the timeline timer when the window is closed
        self.timeline_timer.reset()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
