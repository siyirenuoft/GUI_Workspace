import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq

# Generate the sine waves
# freq1 = 50  # 200 Hz
# freq2 = 200   # 100 Hz
# freq3 = 5   # 5 Hz
# # signal1 = np.sin(2 * np.pi * freq1 * t)
# signal1 = np.sign(np.sin(2 * np.pi * freq1 * t))
# signal2 = np.sin(2 * np.pi * freq2 * t)
# signal3 = np.sin(2 * np.pi * freq3 * t)
# # signal3 is square wave
# # signal3 = np.sign(np.sin(2 * np.pi * freq3 * t))

# Define the color palette
color_palette = {
    'tone': (191/255, 186/255, 156/255, 1),
    'gray': (142/255, 153/255, 171/255, 1),
    'gray_light': (226/255, 226/255, 234/255, 1),
    'red': (217/255, 93/255, 91/255, 1),
    'blue': (77/255, 143/255, 203/255, 1),
    'blue_light': (77/255, 143/255, 203/255, 0.5),
    'yellow': (232/255, 192/255, 71/255, 1),
    'yellow_light': (232/255, 192/255, 71/255, 0.5),
    'olive': (194/255, 191/255, 2/255, 1),
    'green': (87/255, 170/255, 62/255, 1),
    'green_light': (87/255, 170/255, 62/255, 0.5),
    'teal': (66/255, 180/255, 181/255, 1),
    'purple': (178/255, 113/255, 171/255, 1),
    'orange': (244/255, 143/255, 61/255, 1),
    'orange_light': (244/255, 143/255, 61/255, 0.8),
    'purple_dark': {165/255, 72/255, 145/255, 1},
    'purple_light': {183/255, 120/255, 179/255, 1},
    'skin_tone_1': {110/255, 80/255, 64/255, 1},
    'baby_blue': {164/255, 202/255, 230/255, 1},
    'baby_red': {233/255, 160/255, 165/255, 1},
    'baby_teal': {151/255, 206/255, 211/255, 1},
    'baby_gray': {166/255, 168/255, 169/255, 1},
}

# Product signal
# product_signal = signal1 * signal2 * signal3
wav_filename = 'sine5_sine200.wav'
# read the wav file, print the sampling rate and duration, extract the first second of the signal as product_signal
import soundfile as sf
signal, fs = sf.read(wav_filename)
print(f'Sampling rate: {fs} Hz')
print(f'Duration: {len(signal)/fs} seconds')

# Parameters
sampling_rate = fs  # in Hz
duration = 0.2  # in seconds
product_signal = signal[:int(fs*duration)]
t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)

# Plot the product signal
plt.figure(figsize=(6, 4))
plt.plot(t, product_signal, color=color_palette['teal'])
plt.title('Waveform Composition of 200Hz and 5Hz Sine Waves', font='Linux Biolinum G', fontsize=16)
plt.xlabel('Time [s]', font='Linux Biolinum G', fontsize=12)
plt.ylabel('Amplitude', font='Linux Biolinum G', fontsize=12)
plt.show()

# Perform FFT on the product signal
fft_signal = fft(product_signal)
fft_freq = fftfreq(len(fft_signal), 1 / sampling_rate)

# Plot the FFT result
# plt.figure(figsize=(10, 4))
# plt.plot(fft_freq, np.abs(fft_signal))
# plt.title('FFT of the Product Signal')
# plt.xlabel('Frequency [Hz]')
# plt.ylabel('Amplitude')
# plt.xlim(0, 500)  # Focus on low frequencies
# plt.show()


# perform MFCC on the product_signal, and plot the MFCC 
# downsample_rate = 200
# from python_speech_features import mfcc
# mfcc_features = mfcc(product_signal, samplerate=sampling_rate, winlen=1/sampling_rate, winstep=1/sampling_rate, nfft=240)
# plt.figure(figsize=(10, 4))
# plt.imshow(mfcc_features.T, aspect='auto', origin='lower')
# plt.title('MFCC of the Product Signal')
# plt.xlabel('Frame')
# plt.ylabel('MFCC Coefficients')
# plt.colorbar()
# plt.show()

from scipy.signal import stft

# Perform STFT on the signal
downsample_rate = 200
frequencies, times, Zxx = stft(product_signal, fs=sampling_rate, nperseg=int(sampling_rate/downsample_rate), noverlap=0)  # Use a window of 240 samples
# for each window, find the highest frequency component and mark it on the spectrogram. Set freq limit to 500 Hz
max_freq = np.argmax(np.abs(Zxx), axis=0)
max_freq = frequencies[max_freq]
print(len(max_freq), len(times), Zxx.shape)
print(max_freq)

# Plot the spectrogram
plt.figure(figsize=(6, 4))
plt.pcolormesh(times, frequencies, np.abs(Zxx), cmap='viridis', shading='gouraud')
plt.ylim(0, 500)  # Focus on low frequencies
plt.scatter(times, max_freq, s=8, color=color_palette['green'])
plt.title('STFT Spectrogram of the Waveform', font='Linux Biolinum G', fontsize=16)
plt.ylabel('Frequency [Hz]', font='Linux Biolinum G', fontsize=12)
plt.xlabel('Time [s]', font='Linux Biolinum G', fontsize=12)
plt.show()


# Downsample the signal to 200 samples/sec
downsample_rate = 200
downsampled_t = np.linspace(0, duration, int(duration * downsample_rate), endpoint=False)
# downsampled_signal = np.interp(downsampled_t, t, product_signal)
print(int(sampling_rate / downsample_rate))
downsampled_signal = product_signal[::int(sampling_rate / downsample_rate)]

# # Plot the downsampled signal
# plt.figure(figsize=(10, 4))
# print(len(downsampled_t), len(downsampled_signal))
# plt.stem(downsampled_t, downsampled_signal, use_line_collection=True)
# plt.title('Downsampled Signal (200 samples/sec)')
# plt.xlabel('Time [s]')
# plt.ylabel('Amplitude')
# plt.show()

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import hilbert

# Sample signal already given as 'product_signal'
analytic_signal = hilbert(product_signal)
amplitude_envelope = np.abs(analytic_signal)


# # Plot the envelope
# plt.figure(figsize=(10, 4))
# plt.plot(t, amplitude_envelope)
# plt.title('Amplitude Envelope of the Product Signal')
# plt.xlabel('Time [s]')
# plt.ylabel('Amplitude')
# plt.show()

# Perform FFT on the envelope to see the original 10 Hz frequency
fft_envelope = fft(amplitude_envelope)
fft_freq_env = fftfreq(len(fft_envelope), 1 / sampling_rate)

# # Plot the FFT of the envelope
# plt.figure(figsize=(10, 4))
# plt.plot(fft_freq_env[:len(fft_envelope)//2], np.abs(fft_envelope[:len(fft_envelope)//2]))
# plt.title('FFT of the Amplitude Envelope')
# plt.xlabel('Frequency [Hz]')
# plt.ylabel('Amplitude')
# plt.xlim(0, 500)  # Focus on low frequencies to see the 10 Hz
# plt.show()


# filter out frequency components above 100 Hz, and ifft back to time domain
fft_envelope_filtered = fft_envelope.copy()
fft_envelope_filtered[(fft_freq_env > 100)] = 0
fft_envelope_filtered[(fft_freq_env < -100)] = 0
filtered_signal = np.real(np.fft.ifft(fft_envelope_filtered))

# # plot
# plt.figure(figsize=(10, 4))
# plt.plot(t, filtered_signal)
# plt.title('Filtered Signal (Below 100 Hz)')
# plt.xlabel('Time [s]')
# plt.ylabel('Amplitude')
# plt.show()

# # downsample to 200 samples/sec and plot the points together with the curve
downsampled_filtered_signal = filtered_signal[::int(sampling_rate / downsample_rate)]
plt.figure(figsize=(6, 4))
plt.plot(t, filtered_signal, color=color_palette['gray'])
plt.plot(downsampled_t, downsampled_filtered_signal, 'o', color=color_palette['blue'])
plt.title('Waveform Envelope with Downsampled Points', font='Linux Biolinum G', fontsize=16)
plt.xlabel('Time [s]', font='Linux Biolinum G', fontsize=12)
plt.ylabel('Amplitude', font='Linux Biolinum G', fontsize=12)
plt.show()



# make a 1x3 horizontal subplots, plot the produce signal, the max_freq, and the downsampled_filtered_signal, use the same captions above
fig, axs = plt.subplots(1, 3, figsize=(18, 4))
axs[0].plot(t, product_signal, color=color_palette['teal'])
axs[0].set_title('Waveform Composition of 200Hz and 5Hz Sine Waves', font='Linux Biolinum G', fontsize=16)
axs[0].set_xlabel('Time [s]', font='Linux Biolinum G', fontsize=12)
axs[0].set_ylabel('Amplitude', font='Linux Biolinum G', fontsize=12)
axs[1].pcolormesh(times, frequencies, np.abs(Zxx), cmap='viridis', shading='gouraud')
axs[1].set_ylim(0, 500)  # Focus on low frequencies
axs[1].scatter(times, max_freq, s=8, color=color_palette['green'])
axs[1].set_title('STFT Spectrogram of the Waveform', font='Linux Biolinum G', fontsize=16)
axs[1].set_ylabel('Frequency [Hz]', font='Linux Biolinum G', fontsize=12)
axs[1].set_xlabel('Time [s]', font='Linux Biolinum G', fontsize=12)
# axs[1].colorbar(label='Magnitude')
axs[2].plot(t, filtered_signal, color=color_palette['gray'])
axs[2].plot(downsampled_t, downsampled_filtered_signal, 'o', color=color_palette['blue'])
axs[2].set_title('Waveform Envelope with Downsampled Points', font='Linux Biolinum G', fontsize=16)
axs[2].set_xlabel('Time [s]', font='Linux Biolinum G', fontsize=12)
axs[2].set_ylabel('Amplitude', font='Linux Biolinum G', fontsize=12)
plt.tight_layout()
plt.show()
