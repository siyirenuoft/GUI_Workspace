import matplotlib.pyplot as plt
from collections import deque
import time
import threading

class VerificationPlotter:
    def __init__(self, target_address=0):
        self.target_address = target_address
        self.command_queue = deque(maxlen=1000)  # Store the last 1000 commands
        self.plotting_thread = threading.Thread(target=self.plot_duty, daemon=True)
        self.plotting_thread.start()

    def receive_command(self, addr, duty, freq, start_stop):
        if addr == self.target_address:
            self.command_queue.append((time.time(), duty))

    def plot_duty(self):
        plt.ion()
        fig, ax = plt.subplots()
        times = deque(maxlen=1000)
        duties = deque(maxlen=1000)

        while True:
            if self.command_queue:
                current_time, duty = self.command_queue.popleft()
                times.append(current_time)
                duties.append(duty)

                ax.clear()
                ax.plot(times, duties, label=f'Address {self.target_address}')
                ax.set_xlabel('Time (s)')
                ax.set_ylabel('Duty')
                ax.set_title(f'Duty over Time for Address {self.target_address}')
                ax.legend()
                plt.draw()
                plt.pause(0.01)  # Pause to allow real-time updates

    def start(self):
        plt.show(block=True)

if __name__ == "__main__":
    plotter = VerificationPlotter(target_address=0)
    plotter.start()
