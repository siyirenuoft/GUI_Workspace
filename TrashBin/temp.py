import numpy as np
import matplotlib.pyplot as plt

def generate_pwm_signal(frequency, duty_cycle, duration, sampling_rate=44100):
    # Time array
    t = np.linspace(0, duration, int(sampling_rate * duration))
    
    # Calculate the period of the PWM signal
    period = 1 / frequency
    
    # Generate the PWM signal
    pwm_signal = ((t % period) < (duty_cycle / 100) * period).astype(float)
    
    return t, pwm_signal

# Example usage
frequency = 5.0      # Frequency in Hz
duty_cycle = 20.0    # Duty cycle in percentage (0 to 100)
duration = 2.0       # Duration in seconds

# Generate the PWM signal
t, pwm_signal = generate_pwm_signal(frequency=frequency, duty_cycle=duty_cycle, duration=duration)

# Plotting the waveform to visualize it
plt.figure(figsize=(10, 4))
plt.plot(t, pwm_signal, color='blue')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')
plt.title(f'PWM Signal - Frequency: {frequency} Hz, Duty Cycle: {duty_cycle}%')
plt.ylim(-0.1, 1.1)  # Set y-axis limits for better visualization
plt.grid(True)
plt.show()
