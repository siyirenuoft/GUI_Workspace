import csv
from models.waveform import Waveform

def load_waveform(file_path, sampling_frequency):
    data = []
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) > 0:  # Check if the row is not empty
                try:
                    data.append(float(row[0]))
                except ValueError:
                    print(f"Skipping invalid data: {row}")
    return Waveform(data, sampling_frequency)
