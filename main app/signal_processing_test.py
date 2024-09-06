import numpy as np
from scipy.signal import stft, hilbert
from scipy.fft import fft, fftfreq

DOMINANT_CUTOFF = 110


def signal_segmentation(self, product_signal, sampling_rate):
    # Perform STFT on the signal to get the high frequency components
    frequencies, times, Zxx = stft(product_signal, fs=sampling_rate, nperseg=int(sampling_rate))
    
    # Find the dominant frequency over all segments
    max_freq = np.argmax(np.abs(Zxx), axis=0)
    dominant_frequency = np.median(frequencies[max_freq])  # Use median for stability
    
    # Check if the dominant frequency is below the threshold (100 Hz)
    if dominant_frequency < 100:
        high_freq_signal = np.zeros(len(times))  # Set high frequency signal to zero
        low_freq_signal = np.abs(np.array(product_signal))  # Leave the low-frequency signal as the original
    else:
        # Perform Hilbert transform on the signal to get the low-frequency components
        high_freq_signal = np.full(len(times), dominant_frequency)  # Set constant frequency if above threshold
        
        analytic_signal = hilbert(product_signal)
        amplitude_envelope = np.abs(analytic_signal)
        
        # Perform FFT on the envelope to get frequency components
        fft_envelope = fft(amplitude_envelope)
        fft_freq_env = fftfreq(len(fft_envelope), 1 / sampling_rate)
        
        # Filter out frequency components above 100 Hz and ifft back to time domain
        fft_envelope_filtered = fft_envelope.copy()
        fft_envelope_filtered[(fft_freq_env > 100)] = 0
        fft_envelope_filtered[(fft_freq_env < -100)] = 0
        filtered_signal = np.real(np.fft.ifft(fft_envelope_filtered))
        
        # Processed low-frequency signal
        low_freq_signal = filtered_signal

    return high_freq_signal, low_freq_signal

if __name__ == '__main__':
    import numpy as np
    import matplotlib.pyplot as plt

    # Parameters
    sampling_rate = 44100  # Sampling frequency
    t = np.linspace(0, 1, sampling_rate)  # 1-second duration
    sin_10hz = np.sin(2 * np.pi * 10 * t)  # 10 Hz sine wave
    sin_200hz = np.sin(2 * np.pi * 300 * t)  # 200 Hz sine wave

    # Product of the two sine waves
    product_signal = sin_10hz * sin_200hz

    # Call the segmentation function
    high_freq_signal, low_freq_signal = signal_segmentation(None, product_signal, sampling_rate)

    # Plotting the signals
    plt.figure(figsize=(10, 6))
    plt.subplot(3, 1, 1)
    plt.plot(t, product_signal)
    plt.title("Original Product Signal (10 Hz * 200 Hz)")
    plt.subplot(3, 1, 2)
    plt.plot(high_freq_signal)
    plt.title("High-Frequency Signal")
    plt.subplot(3, 1, 3)
    plt.plot(low_freq_signal)
    plt.title("Low-Frequency Signal")
    plt.tight_layout()
    plt.show()
