import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq
from scipy.signal import stft
from scipy.signal import hilbert

class signal_segmentation_api:
    def __init__(self):
        pass

    '''
    the function takes in a high sample rate produce signal, extract high frequency components using STFT, and extract low frequency components using Hilbert transform
    Input: product_signal, sample_rate, duration, downsample_rate
    Output: high_freq_signal, low_freq_signal
    '''
    def signal_segmentation(self, product_signal, sampling_rate, downsample_rate):
        # Perform STFT on the signal to get the high frequency components
        frequencies, times, Zxx = stft(product_signal, fs=sampling_rate, nperseg=int(sampling_rate/downsample_rate))
        max_freq = np.argmax(np.abs(Zxx), axis=0)
        max_freq = frequencies[max_freq]
        print(max_freq)
        high_freq_signal = max_freq

        # Perform Hilbert transform on the signal to get the low frequency components
        analytic_signal = hilbert(product_signal)
        amplitude_envelope = np.abs(analytic_signal)
        # Perform FFT on the envelope to get frequency components
        fft_envelope = fft(amplitude_envelope)
        fft_freq_env = fftfreq(len(fft_envelope), 1 / sampling_rate)
        # filter out frequency components above 100 Hz, and ifft back to time domain
        fft_envelope_filtered = fft_envelope.copy()
        fft_envelope_filtered[(fft_freq_env > downsample_rate//2)] = 0
        fft_envelope_filtered[(fft_freq_env < -downsample_rate//2)] = 0
        filtered_signal = np.real(np.fft.ifft(fft_envelope_filtered))
        # downsample to 200 samples/sec and plot the points together with the curve
        downsampled_filtered_signal = filtered_signal[::int(sampling_rate / downsample_rate)]
        low_freq_signal = downsampled_filtered_signal

        return high_freq_signal, low_freq_signal


# Example usage
if __name__ == '__main__':
    wav_filename = 'chirp5_sine200.wav'
    # read the wav file, print the sampling rate and duration, extract the first second of the signal as product_signal
    import soundfile as sf
    signal, fs = sf.read(wav_filename)
    print(f'Sampling rate: {fs} Hz')
    print(f'Duration: {len(signal)/fs} seconds')
    product_signal = signal[:fs]

    # Parameters
    sampling_rate = fs  # in Hz
    duration = 1  # in seconds
    t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)

    # Initialize the signal segmentation API
    signal_segmentation = signal_segmentation_api()

    # Perform signal segmentation
    downsample_rate = 200
    downsample_t = np.linspace(0, duration, downsample_rate, endpoint=False)
    high_freq_signal, low_freq_signal = signal_segmentation.signal_segmentation(product_signal, sampling_rate, downsample_rate)
    print(len(downsample_t), len(high_freq_signal), len(low_freq_signal))

    # Plot the high frequency signal
    plt.figure(figsize=(10, 4))
    plt.plot(downsample_t, high_freq_signal)
    plt.title('High Frequency Signal')
    plt.xlabel('Time [s]')
    plt.ylabel('Amplitude')
    plt.show()

    # Plot the low frequency signal
    plt.figure(figsize=(10, 4))
    plt.plot(downsample_t, low_freq_signal)
    plt.title('Low Frequency Signal')
    plt.xlabel('Time [s]')
    plt.ylabel('Amplitude')
    plt.show()