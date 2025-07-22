#research_logger.py

import time
import os
import csv
import statistics
import board
import busio
from adafruit_ina219 import INA219
from datetime import datetime

class ResearchLogger:
    def __init__(self, trial_name="PID", baseline_temp=16.0, log_interval=1.0, duration_minutes=45):
        self.trial_name = trial_name
        self.baseline_temp = baseline_temp
        self.log_interval = log_interval
        self.duration_seconds = duration_minutes * 60
        self.temp_history = []
        self.latencies = []
        self.power_history = []
        self.duty_history = []
        self.power_window = []
        
        i2c = busio.I2C(board.SCL, board.SDA)
        self.ina = INA219(i2c)

        base_folder = "research_data"

        if trial_name.startswith("IDK_"):
            self.folder_path = os.path.join(base_folder, "IDK_CASCADE", trial_name)
        else:
            self.folder_path = os.path.join(base_folder, trial_name)

        os.makedirs(self.folder_path, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.raw_data_path = os.path.join(self.folder_path, f"raw_data_{timestamp}.csv")
        self.summary_path = os.path.join(self.folder_path, f"summary_{timestamp}.csv")

        with open(self.raw_data_path, "w", newline='') as f:
            writer = csv.writer(f)
            if trial_name.startswith("IDK_"):
                writer.writerow(["Timestamp", "Temperature (C)", "Duty Cycle (%)", "Latency (ms)", "Power (W)", "Model", "Confidence (%)"])
            else:
                writer.writerow(["Timestamp", "Temperature (C)", "Duty Cycle (%)", "Latency (ms)", "Power (W)"])

        self.start_time = time.time()

    def log(self, temperature, duty_cycle, confidence=None, model=None):
        if self.should_stop():
            return False

        log_start = time.time()

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        try:
            power = self.ina.power
        except Exception as e:
            print(f"[INA219] Power read failed: {e}")
            power = 0.0
        self.power_window.append(power)
        if len(self.power_window) > 10:
            self.power_window.pop(0)

        avg_power = sum(self.power_window) / len(self.power_window)
        latency = (time.time() - log_start) * 1000  # ms

        # Save to lists
        self.temp_history.append(temperature)
        self.latencies.append(latency)
        self.power_history.append(avg_power)
        self.duty_history.append(duty_cycle)

        # Append to CSV
        with open(self.raw_data_path, "a", newline='') as f:
            writer = csv.writer(f)
            if trial_name.startswith("IDK_") and confidence is not None and model is not None:
                writer.writerow([
                    timestamp,
                    round(temperature, 2),
                    round(duty_cycle, 2),
                    round(latency, 3),
                    round(avg_power, 3),
                    model,
                    round(confidence, 3),
                ])

            else:
                writer.writerow([
                    timestamp,
                    round(temperature, 2),
                    round(duty_cycle, 2),
                    round(latency, 3),
                    round(avg_power, 3)
                ])

        return True

    def should_stop(self):
        return (time.time() - self.start_time) >= self.duration_seconds

    def summarize(self, stages=None):
        total_time = time.time() - self.start_time
        std_temp = statistics.stdev(self.temp_history) if len(self.temp_history) > 1 else 0
        avg_latency = statistics.mean(self.latencies) if self.latencies else 0
        avg_power = statistics.mean(self.power_history) if self.power_history else 0
        avg_duty = statistics.mean(self.duty_history) if self.duty_history else 0

        try:
            efficiency_score = 1 / (std_temp * avg_latency * avg_power)
        except ZeroDivisionError:
            efficiency_score = float('inf')

        with open(self.summary_path, "w", newline='') as f:
            writer = csv.writer(f)
            if self.trial_name.startswith("IDK_") and stages is not None:
                 writer.writerow([
                    "Baseline Temp (°C)",
                    "Trial Duration (min)",
                    "Std Dev (Temp)",
                    "Avg Latency (ms)",
                    "Avg Power (W)",
                    "Avg Duty (%)",
                    "# PID",
                    "# NN1(fast)",
                    "# NN2(slow)",
                    "Efficiency Score"
                ])
                writer.writerow([
                    round(self.baseline_temp, 2),
                    round(total_time / 60, 2),
                    round(std_temp, 3),
                    round(avg_latency, 3),
                    round(avg_power, 3),
                    round(avg_duty, 3),
                    stages["PID"],
                    stages["NN_FAST"],
                    stages["NN_SLOW"],
                    round(efficiency_score, 6)
                ])

            else:
                writer.writerow([
                    "Baseline Temp (°C)",
                    "Trial Duration (min)",
                    "Std Dev (Temp)",
                    "Avg Latency (ms)",
                    "Avg Power (W)",
                    "Avg Duty (%)",
                    "Efficiency Score"
                ])
                writer.writerow([
                    round(self.baseline_temp, 2),
                    round(total_time / 60, 2),
                    round(std_temp, 3),
                    round(avg_latency, 3),
                    round(avg_power, 3),
                    round(avg_duty, 3),
                    round(efficiency_score, 6)
                ])

        print(f"\nTrial '{self.trial_name}' complete.")
        print(f"Summary saved to: {self.summary_path}")

