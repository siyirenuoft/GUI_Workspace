import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

def generate_chirp_waveform(data, num_points=1000, sampling_rate=1000):
    # Extract top-level gain and bias
    current_level = data.get('value0', {})
    gain = current_level.get('gain', 1.0)
    bias = current_level.get('bias', 0.0)
    
    # Time array
    t = np.linspace(0, num_points / sampling_rate, num_points)
    
    # Extract the nested structure for the chirp
    oscillator = current_level.get('m_ptr', {}).get('ptr_wrapper', {}).get('data', {}).get('m_model', {}).get('IOscillator', {})
    x_component = oscillator.get('x', {})
    
    # Extract frequency modulation parameters
    lhs = x_component.get('m_ptr', {}).get('ptr_wrapper', {}).get('data', {}).get('m_model', {}).get('IOperator', {}).get('lhs', {})
    f0 = lhs.get('gain', 1) / (2 * np.pi)  # Start frequency in Hz
    chirp_rate = lhs.get('bias', 628.3185307179587) / (2 * np.pi)  # Chirp rate in Hz/s
    print("lhs",lhs)
    print("f0",f0)
    print("chirp_rate",chirp_rate)

    # Calculate the end frequency based on chirp rate
    f1 = f0 + chirp_rate * t[-1]
    
    # Generate the chirp waveform
    waveform = gain * signal.chirp(t, f0=f0, f1=f1, t1=t[-1], method='linear') + bias
    
    return t, waveform

# Example JSON data for the chirp signal
json_data = {
    "value0": {
        "gain": 1.0,
        "bias": 0.0,
        "m_ptr": {
            "polymorphic_id": 2147483649,
            "polymorphic_name": "tact::Signal::Model<tact::Sine>",
            "ptr_wrapper": {
                "valid": 1,
                "data": {
                    "Concept": {},
                    "m_model": {
                        "IOscillator": {
                            "x": {
                                "gain": 1.0,
                                "bias": 0.0,
                                "m_ptr": {
                                    "polymorphic_id": 2147483650,
                                    "polymorphic_name": "tact::Signal::Model<tact::Product>",
                                    "ptr_wrapper": {
                                        "valid": 1,
                                        "data": {
                                            "Concept": {},
                                            "m_model": {
                                                "IOperator": {
                                                    "lhs": {
                                                        "gain": 314.1592653589793,  # Angular frequency (rad/s)
                                                        "bias": 628.3185307179587,  # Chirp rate (rad/s^2)
                                                        "m_ptr": {
                                                            "polymorphic_id": 2147483651,
                                                            "polymorphic_name": "tact::Signal::Model<tact::Time>",
                                                            "ptr_wrapper": {
                                                                "valid": 1,
                                                                "data": {
                                                                    "Concept": {},
                                                                    "m_model": {}
                                                                }
                                                            }
                                                        }
                                                    },
                                                    "rhs": {
                                                        "gain": 1.0,
                                                        "bias": 0.0,
                                                        "m_ptr": {
                                                            "polymorphic_id": 3,
                                                            "ptr_wrapper": {
                                                                "valid": 1,
                                                                "data": {
                                                                    "Concept": {},
                                                                    "m_model": {}
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

# Generate the waveform
t, waveform = generate_chirp_waveform(json_data)

# Plotting the waveform to visualize it
plt.figure(figsize=(10, 4))
plt.plot(t, waveform, color='red')
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')
plt.title('Chirp Signal')
plt.grid(True)
plt.show()
