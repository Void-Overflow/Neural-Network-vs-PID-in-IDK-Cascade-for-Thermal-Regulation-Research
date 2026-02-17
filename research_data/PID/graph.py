import pandas as pd
import matplotlib.pyplot as plt
import glob

# Auto-find your raw_data_*.csv files (only the ones you listed)
files = ['raw_data_1.csv', 'raw_data_2.csv', 'raw_data_3.csv', 'raw_data_4.csv', 'raw_data_5.csv', 'raw_data_6.csv', 'raw_data_7.csv']

# Create figure with subplots (one per trial)
fig, axs = plt.subplots(len(files), 1, figsize=(12, 3.5 * len(files)), sharex=True)
fig.suptitle('Temperature vs Time – PID Trials (All 45 min)', fontsize=16, fontweight='bold')

for i, file in enumerate(files):
    df = pd.read_csv(file)
    
    # Convert timestamp to relative minutes
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Time (min)'] = (df['Timestamp'] - df['Timestamp'].iloc[0]).dt.total_seconds() / 60.0
    
    # Plot temperature
    axs[i].plot(df['Time (min)'], df['Temperature (C)'], 
                color='#1f77b4', linewidth=2, label=f'Trial {file.split("_")[2].split(".")[0]}')
    
    # Styling
    axs[i].set_ylabel('Temperature (°C)', fontsize=12)
    axs[i].grid(True, alpha=0.3)
    axs[i].legend(fontsize=11)
    axs[i].set_ylim(15, 30)  # Matches your data range
    axs[i].tick_params(axis='y', labelsize=10)

# Final touches
axs[-1].set_xlabel('Time (min)', fontsize=12)
plt.tight_layout(rect=[0, 0, 1, 0.96])  # Leave space for suptitle
plt.savefig('pid_temp_vs_time_all_trials.png', dpi=300, bbox_inches='tight')
print("✅ Graph saved as 'pid_temp_vs_time_all_trials.png' – open it for full view!")
plt.show()