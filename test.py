import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import hilbert, square

# Constants
sample_rate = 44100
duration = 1  # second
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

# First half: 5Hz Sine wave * 200Hz Sine wave
sine_5hz = np.sin(2 * np.pi * 5 * t[:int(sample_rate // 2)])
sine_200hz = np.sin(2 * np.pi * 200 * t[:int(sample_rate // 2)])
first_half = sine_5hz * sine_200hz

# Second half: 10Hz Sine wave * 100Hz Square wave
sine_10hz = np.sin(2 * np.pi * 10 * t[int(sample_rate // 2):])
square_100hz = square(2 * np.pi * 100 * t[int(sample_rate // 2):])
second_half = sine_10hz * square_100hz

# Full signal
signal = np.concatenate((first_half, second_half))

# Perform Hilbert transform
analytic_signal = hilbert(signal)
amplitude_envelope = np.abs(analytic_signal)

from scipy.fftpack import fft

# Perform FFT on the Hilbert-transformed data
fft_result = fft(amplitude_envelope)
fft_magnitude = np.abs(fft_result)

# Set up the plot
fig, axs = plt.subplots(4, 1, figsize=(12, 12))

# Original signal
axs[0].plot(t, signal)
axs[0].set_title("Original Signal")
axs[0].set_xlabel("Time [s]")
axs[0].set_ylabel("Amplitude")
axs[0].grid(True)

# Hilbert Transformed signal
axs[1].plot(t, amplitude_envelope, color="orange")
axs[1].set_title("Hilbert Transformed Signal (Amplitude Envelope)")
axs[1].set_xlabel("Time [s]")
axs[1].set_ylabel("Amplitude")
axs[1].grid(True)

# FFT of Hilbert-transformed signal
freqs = np.fft.fftfreq(len(fft_magnitude), 1/sample_rate)
axs[2].plot(freqs[:len(freqs)//2], fft_magnitude[:len(fft_magnitude)//2])
axs[2].set_title("FFT of Hilbert Transformed Signal")
axs[2].set_xlabel("Frequency [Hz]")
axs[2].set_xlim(0, 500)
axs[2].set_ylabel("Magnitude")
axs[2].grid(True)

# remove all components above 100 Hz, and ifft and plot again
fft_result[abs(freqs) > 100] = 0
filtered_signal = np.fft.ifft(fft_result)
plt.plot(t, filtered_signal)
plt.title("Filtered signal")
plt.xlabel("Time [s]")
plt.ylabel("Amplitude")
plt.grid(True)

plt.tight_layout()
plt.show()
