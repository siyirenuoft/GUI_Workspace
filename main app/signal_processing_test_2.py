import numpy as np
from scipy.signal import stft, hilbert, resample
from scipy.fft import fft, fftfreq


class signal_segmentation_api_2:
    def __init__(self):
        pass

    def signal_segmentation(self, product_signal, sampling_rate, downsample_rate, threshold=100):
        """Down sample and up sample version"""

        # Perform STFT on the signal to get the high-frequency components
        frequencies, times, Zxx = stft(product_signal, fs=sampling_rate, nperseg=2*int(sampling_rate/downsample_rate))
        max_freq = np.argmax(np.abs(Zxx), axis=0)
        high_freq_signal = frequencies[max_freq][:-1]

        # Perform Hilbert transform on the signal to get the low-frequency components
        analytic_signal = hilbert(product_signal)
        amplitude_envelope = np.abs(analytic_signal)

        # Perform FFT on the envelope to get frequency components
        fft_envelope = fft(amplitude_envelope)
        fft_freq_env = fftfreq(len(fft_envelope), 1 / sampling_rate)

        # Use median frequency instead of max to compare with the threshold
        median_frequency = np.median(high_freq_signal)
        print("Median", np.median(high_freq_signal))
        print("Max", np.max(high_freq_signal))
        print("Mean", np.mean(high_freq_signal))
        if median_frequency < threshold:
            # Set low frequency signal to the original and high frequency to zeros
            low_freq_signal = product_signal
            high_freq_signal = np.zeros_like(product_signal)
        else:
            # Filter out frequency components above downsample_rate/2 and IFFT back to time domain
            fft_envelope_filtered = fft_envelope.copy()
            fft_envelope_filtered[(fft_freq_env > downsample_rate//2)] = 0
            fft_envelope_filtered[(fft_freq_env < -downsample_rate//2)] = 0
            filtered_signal = np.real(np.fft.ifft(fft_envelope_filtered))

            # Clamp the low frequency signal between 0 and 1
            low_freq_signal = np.clip(filtered_signal, 0, 1)

            # Upsample both signals to match the original signal length using cubic interpolation
            high_freq_signal = np.interp(np.arange(len(product_signal)), np.linspace(0, len(product_signal)-1, len(high_freq_signal)), high_freq_signal)
            low_freq_signal = np.interp(np.arange(len(product_signal)), np.linspace(0, len(product_signal)-1, len(low_freq_signal)), low_freq_signal)

        return high_freq_signal, low_freq_signal


if __name__ == '__main__':
    
    # Test the function with a sample input signal
    import matplotlib.pyplot as plt

    sampling_rate = 44100
    downsample_rate = 200
    t = np.linspace(0, 1, sampling_rate, endpoint=False)
    # 10 Hz and 200 Hz sine wave product
    test_signal = np.sin(2 * np.pi * 10 * t) * np.sin(2 * np.pi * 300 * t)
    # test_signal = np.sin(2 * np.pi * (300 + (50 - 300) * t) * t) * np.sin(2 * np.pi * 10 * t)



    segmentation_instance = signal_segmentation_api_2()  # Replace with the actual instance of your class
    high_freq_signal, low_freq_signal = segmentation_instance.signal_segmentation(test_signal, sampling_rate, downsample_rate)

    # Plot the signals
    plt.figure(figsize=(12, 6))
    plt.subplot(3, 1, 1)
    plt.plot(t, test_signal)
    plt.title("Original Signal (10 Hz * 200 Hz)")
    plt.subplot(3, 1, 2)
    plt.plot(t, high_freq_signal)
    plt.title("High Frequency Signal (Resampled)")
    plt.subplot(3, 1, 3)
    plt.plot(t, low_freq_signal)
    plt.title("Low Frequency Signal (Resampled)")
    plt.tight_layout()
    plt.show()
