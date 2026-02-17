import pandas as pd
import numpy as np

# List of files to average
files = [f"summary_{i}.csv" for i in range(1, 8)]  # summary_1.csv to summary_7.csv

print("Reading and averaging 7 summary files...\n")

# We'll collect all the value rows
values_list = []

for file in files:
    try:
        df = pd.read_csv(file, header=None)  # no header row
        # Assume first row = headers, second row = values
        headers = df.iloc[0].values
        values = df.iloc[1].values
        values_list.append(values)
        print(f"Loaded: {file}")
    except FileNotFoundError:
        print(f"Warning: {file} not found → skipping")
    except Exception as e:
        print(f"Error reading {file}: {e}")

if not values_list:
    print("No files were successfully read. Exiting.")
    exit()

# Convert to numeric array (skip the first column if it's string, but yours is all numeric)
values_array = np.array(values_list, dtype=float)

# Compute mean for each column
averages = np.mean(values_array, axis=0)

# Create output DataFrame in the same format
output_df = pd.DataFrame([
    headers,
    [f"{v:.3f}" if i > 0 else f"{v:.1f}" for i, v in enumerate(averages)]
])

# Save
output_df.to_csv("overall_summary.csv", index=False, header=False)

print("\nDone!")
print("Created: overall_summary.csv")
print(f"Averaged {len(values_list)} files successfully.")
print("Values (for quick check):")
print("Baseline Temp (°C)     :", averages[0])
print("Trial Duration (min)    :", averages[1])
print("Std Dev (Temp)          :", averages[2])
print("Avg Latency (ms)        :", averages[3])
print("Avg Power (W)           :", averages[4])
print("Avg Duty (%)            :", averages[5])
print("Efficiency Score        :", averages[6])