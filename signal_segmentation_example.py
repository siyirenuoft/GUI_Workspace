import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq

# Parameters
sampling_rate = 44100  # in Hz
duration = 1  # in seconds
t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)

# Generate the sine waves
freq1 = 50  # 200 Hz
freq2 = 200   # 100 Hz
freq3 = 5   # 5 Hz
# signal1 = np.sin(2 * np.pi * freq1 * t)
signal1 = np.sign(np.sin(2 * np.pi * freq1 * t))
signal2 = np.sin(2 * np.pi * freq2 * t)
signal3 = np.sin(2 * np.pi * freq3 * t)
# signal3 is square wave
# signal3 = np.sign(np.sin(2 * np.pi * freq3 * t))


# Product signal
product_signal = signal1 * signal2 * signal3

# Plot the product signal
plt.figure(figsize=(10, 4))
plt.plot(t, product_signal)
plt.title('Product Signal of 300Hz and 10Hz Sine Waves')
plt.xlabel('Time [s]')
plt.ylabel('Amplitude')
plt.show()

# Perform FFT on the product signal
fft_signal = fft(product_signal)
fft_freq = fftfreq(len(fft_signal), 1 / sampling_rate)

# Plot the FFT result
plt.figure(figsize=(10, 4))
plt.plot(fft_freq, np.abs(fft_signal))
plt.title('FFT of the Product Signal')
plt.xlabel('Frequency [Hz]')
plt.ylabel('Amplitude')
plt.xlim(0, 500)  # Focus on low frequencies
plt.show()

# Downsample the signal to 200 samples/sec
downsample_rate = 200
downsampled_t = np.linspace(0, duration, downsample_rate, endpoint=False)
# downsampled_signal = np.interp(downsampled_t, t, product_signal)
print(int(sampling_rate / downsample_rate))
downsampled_signal = product_signal[::int(sampling_rate / downsample_rate)][:-1]

# Plot the downsampled signal
plt.figure(figsize=(10, 4))
plt.stem(downsampled_t, downsampled_signal, use_line_collection=True)
plt.title('Downsampled Signal (200 samples/sec)')
plt.xlabel('Time [s]')
plt.ylabel('Amplitude')
plt.show()

# exit()

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import hilbert

# Sample signal already given as 'product_signal'
analytic_signal = hilbert(product_signal)
amplitude_envelope = np.abs(analytic_signal)


# Plot the envelope
plt.figure(figsize=(10, 4))
plt.plot(t, amplitude_envelope)
plt.title('Amplitude Envelope of the Product Signal')
plt.xlabel('Time [s]')
plt.ylabel('Amplitude')
plt.show()

# Perform FFT on the envelope to see the original 10 Hz frequency
fft_envelope = fft(amplitude_envelope)
fft_freq_env = fftfreq(len(fft_envelope), 1 / sampling_rate)
print(fft_freq_env)

# Plot the FFT of the envelope
plt.figure(figsize=(10, 4))
plt.plot(fft_freq_env[:len(fft_envelope)//2], np.abs(fft_envelope[:len(fft_envelope)//2]))
plt.title('FFT of the Amplitude Envelope')
plt.xlabel('Frequency [Hz]')
plt.ylabel('Amplitude')
plt.xlim(0, 500)  # Focus on low frequencies to see the 10 Hz
plt.show()


# filter out frequency components above 100 Hz, and ifft back to time domain
fft_envelope_filtered = fft_envelope.copy()
fft_envelope_filtered[(fft_freq_env > 100)] = 0
fft_envelope_filtered[(fft_freq_env < -100)] = 0
filtered_signal = np.real(np.fft.ifft(fft_envelope_filtered))

# plot
plt.figure(figsize=(10, 4))
plt.plot(t, filtered_signal)
plt.title('Filtered Signal (Below 100 Hz)')
plt.xlabel('Time [s]')
plt.ylabel('Amplitude')
plt.show()


