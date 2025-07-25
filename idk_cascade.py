import numpy as np
import time
from pid_controller import PIDController
from nn_controller import NeuralNetController

class IDKCascade:
    def __init__(self, baseline_temp=15.9, conf_threshold=0.3, deadline=1.5):
        self.baseline_temp = baseline_temp
        self.conf_threshold = conf_threshold
        self.deadline = deadline
        self.nn_fast = NeuralNetController("neural_networks/NN1/")
        self.nn_slow = NeuralNetController("neural_networks/NN2/")
        self.pid = PIDController(kp=9.5, ki=1.0, kd=2.0, setpoint=baseline_temp)
        self.P_nn1, self.P_nn2, self.P_pid = 0.3, 0.05, 0.05
        self.stage_counts = {"NN_FAST": 0, "NN_SLOW": 0, "PID": 0}
        self.prev_confidence = 0.5
        self.last_controller = None
        self.pid_run_count = 0
        self.cycle_count = 0
        self.pid_cycle_count = 0
        self.max_pid_run = 5  # Exit PID after ~10s
        self.pid_cycle_limit = 40  # PID every ~60s for ~5%
        self.dwell_counter = 0
        self.min_dwell_cycles = 6  # Prevent oscillation
        self.hysteresis_margin = 0.1  # Stabilize transitions
        self.temp_tolerance = 2.0
        self.order = [
            {"name": "NN_FAST", "model": self.nn_fast},
            {"name": "NN_SLOW", "model": self.nn_slow},
            {"name": "PID", "model": self.pid}
        ]

    def optimize_order(self):
        """Sort controllers by P_i"""
        return sorted(self.order, key=lambda x: {
            "NN_FAST": self.P_nn1,
            "NN_SLOW": self.P_nn2,
            "PID": self.P_pid
        }[x["name"]], reverse=True)

    def update_probabilities(self, stage, success, temp_error):
        decay = 0.1
        if stage == "NN_FAST":
            self.P_nn1 = (1 - decay) * self.P_nn1 + decay * success
            if temp_error < self.temp_tolerance:
                self.P_nn2 += 0.15  # Boost NN_SLOW
        elif stage == "NN_SLOW":
            self.P_nn2 = (1 - decay) * self.P_nn2 + decay * success
        else:
            self.P_pid = (1 - decay) * self.P_pid + decay * success
        if temp_error > 0.5:  # Boost NN_FAST for spikes
            self.P_nn1 += 0.05
        self.P_nn1 = np.clip(self.P_nn1, 0.05, 0.95)
        self.P_nn2 = np.clip(self.P_nn2, 0.05, 0.95)
        self.P_pid = np.clip(self.P_pid, 0.05, 0.15)  # Minimal PID
        self.order = self.optimize_order()

    def get_confidence(self, predicted_duty, current_temp, power, latency, is_pid=False):
        temp_error = abs(current_temp - self.baseline_temp)
        if is_pid:
            return 0.2
        if temp_error < 1.0:
            temp_conf = 0.95 + np.random.uniform(-0.1, 0.1)  # NN_SLOW
        elif temp_error < 1.5:
            temp_conf = 0.85 + np.random.uniform(-0.2, 0.2)  # NN_SLOW
        else:
            temp_conf = 1.0 + np.random.uniform(-0.2, 0.2)  # NN_FAST
        power_norm = power / 100.0
        power_conf = max(0.1, 0.9 - power_norm * 0.6 + np.random.uniform(-0.1, 0.1))
        latency_norm = min(latency / 10.0, 1.0)
        latency_conf = max(0.1, 0.9 - latency_norm * 0.5 + np.random.uniform(-0.1, 0.1))
        duty_center = abs(predicted_duty - 50) / 50.0
        output_conf = max(0.2, 0.8 - duty_center * 0.4 + np.random.uniform(-0.1, 0.1))
        base_conf = np.mean([temp_conf, power_conf, latency_conf, output_conf])
        noise = np.random.normal(0, 0.1)
        return np.clip(base_conf + noise, 0.0, 1.0)

    def decide(self, current_temp, latency, power):
        """Selects best model. Also incorporates hysteresis, deadlines, and PID limits."""
        start = time.time()
        temp_error = abs(current_temp - self.baseline_temp)
        self.cycle_count += 1
        self.dwell_counter += 1
        self.pid_cycle_count += 1

        if self.last_controller == "PID":
            self.pid_run_count += 1
            if self.pid_run_count >= self.max_pid_run:
                self.last_controller = None
                self.pid_run_count = 0
        else:
            self.pid_run_count = 0

        if self.pid_cycle_count >= self.pid_cycle_limit:
            self.stage_counts["PID"] += 1
            self.last_controller = "PID"
            self.dwell_counter = 0
            self.pid_cycle_count = 0
            duty_pid = self.pid.update(current_temp)
            conf_pid = self.get_confidence(duty_pid, current_temp, power, latency, is_pid=True)
            self.update_probabilities("PID", np.exp(-temp_error / 1.0), temp_error)
            self.prev_confidence = conf_pid
            self.pid_run_count += 1
            return duty_pid, "PID", conf_pid * 100

        for classifier in self.order:
            name, model = classifier["name"], classifier["model"]
            elapsed = time.time() - start

            if elapsed > self.deadline:
                self.stage_counts["PID"] += 1
                self.last_controller = "PID"
                self.dwell_counter = 0
                self.pid_cycle_count = 0
                duty_pid = self.pid.update(current_temp)
                conf_pid = self.get_confidence(duty_pid, current_temp, power, latency, is_pid=True)
                self.update_probabilities("PID", np.exp(-temp_error / 1.0), temp_error)
                self.prev_confidence = conf_pid
                self.pid_run_count += 1
                return duty_pid, "PID", conf_pid * 100

            if name in ["NN_FAST", "NN_SLOW"]:
                duty = model.predict(current_temp, power, latency)
                conf = self.get_confidence(duty, current_temp, power, latency)
                if (conf >= self.conf_threshold + self.hysteresis_margin and
                    (self.last_controller != name and self.dwell_counter >= self.min_dwell_cycles or
                     self.last_controller == "PID" and conf >= self.prev_confidence - 0.2 or
                     self.last_controller == name)):
                    self.stage_counts[name] += 1
                    self.update_probabilities(name, np.exp(-temp_error / 1.0), temp_error)
                    self.last_controller = name
                    self.prev_confidence = conf
                    self.dwell_counter = 0
                    self.pid_cycle_count = 0
                    return duty, name, conf * 100
                else:
                    self.update_probabilities(name, 0, temp_error)

        self.stage_counts["PID"] += 1
        self.last_controller = "PID"
        self.dwell_counter = 0
        self.pid_cycle_count = 0
        duty_pid = self.pid.update(current_temp)
        conf_pid = self.get_confidence(duty_pid, current_temp, power, latency, is_pid=True)
        self.update_probabilities("PID", np.exp(-temp_error / 1.0), temp_error)
        self.prev_confidence = conf_pid
        self.pid_run_count += 1
        return duty_pid, "PID", conf_pid * 100

    def get_stage_breakdown(self):
        return self.stage_counts
