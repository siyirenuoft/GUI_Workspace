import re
import matplotlib.pyplot as plt


# Adjusted data parsing function to handle varying formats
def parse_data(file_path):
    commands = {}
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if "Sending command:" in line:
                # Regex to capture the address and duty values
                match = re.search(r"Addr (\d+), Duty (\d+)", line)
                if match:
                    addr = f"Addr {match.group(1)}"
                    duty = int(match.group(2))
                    if addr not in commands:
                        commands[addr] = []
                    commands[addr].append(duty)
    return commands

# Plotting function
def plot_data(commands):
    plt.figure(figsize=(10, 6))
    
    for addr, duties in commands.items():
        plt.plot(duties, label=f'{addr}')
    
    plt.xlabel('Command Sequence')
    plt.ylabel('Duty Cycle')
    plt.title('Duty Cycle for Different Addresses')
    plt.legend()
    plt.grid(True)
    plt.show()

# Parse the data and plot
commands = parse_data('data2.txt')
plot_data(commands)