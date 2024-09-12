import re
import matplotlib.pyplot as plt

# Adjusted data parsing function to handle Time, Duty, and Frequency
def parse_data(file_path):
    commands = {"Time": {}, "Duty": {}, "Frequency": {}}
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if "Sending command:" in line:
                # Regex to capture the time, address, duty, and frequency values
                match = re.search(r"Time ([\d\.]+), Addr (\d+), Duty ([\-]?\d+), Freq (\d+), Start/Stop (\d+)", line)
                if match:
                    time = float(match.group(1))  # Capture the time value
                    addr = f"Addr {match.group(2)}"
                    duty = int(match.group(3))
                    freq = int(match.group(4))
                    
                    if addr not in commands["Time"]:
                        commands["Time"][addr] = []
                        commands["Duty"][addr] = []
                        commands["Frequency"][addr] = []
                    
                    commands["Time"][addr].append(time)
                    commands["Duty"][addr].append(duty)
                    commands["Frequency"][addr].append(freq)
    return commands

# Plotting function to display Duty and Frequency with respect to Time
def plot_data(commands):
    fig, axs = plt.subplots(2, 1, figsize=(10, 10))

    # Plot Duty with respect to Time
    for addr in commands["Duty"]:
        axs[0].plot(commands["Time"][addr], commands["Duty"][addr], label=f'{addr}')
    axs[0].set_xlabel('Time')
    axs[0].set_ylabel('Duty Cycle')
    axs[0].set_title('Duty Cycle over Time for Different Addresses')
    axs[0].legend()
    axs[0].grid(True)

    # Plot Frequency with respect to Time
    for addr in commands["Frequency"]:
        axs[1].plot(commands["Time"][addr], commands["Frequency"][addr], label=f'{addr}')
    axs[1].set_xlabel('Time')
    axs[1].set_ylabel('Frequency')
    axs[1].set_title('Frequency over Time for Different Addresses')
    axs[1].legend()
    axs[1].grid(True)

    plt.tight_layout()
    plt.show()

# Example of how to call it with your file
file_path = 'data2.txt'  # Replace with the path to your local file
commands = parse_data(file_path)
plot_data(commands)
