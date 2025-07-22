#idk_cascade

import numpy as np
from pid_controller import PIDController
from nn_controller import NeuralNetController

class IDKCascade:
    def __init__(self, baseline_temp=16.0, conf_threshold=0.3):
        """
        conf_threshold: confidence cutoff (e.g., 0.1, 0.3, 0.5, 0.7, 0.9)
        """
        self.conf_threshold = conf_threshold
        self.baseline_temp = baseline_temp

        self.nn_fast = NeuralNetController("neural_networks/NN1/")
        self.nn_slow = NeuralNetController("neural_networks/NN2/")

        self.pid = PIDController(kp=5.0, ki=0.5, kd=1.0, setpoint=baseline_temp)

        self.duty_mean = 40
        self.duty_min = 0
        self.duty_max = 100

        self.stage_counts = {"NN_FAST": 0, "NN_SLOW": 0, "PID": 0}

    def get_confidence(self, predicted_duty):
        """Estimate confidence based on deviation from mean training behavior."""
        norm_diff = abs(predicted_duty - self.duty_mean) / (self.duty_max - self.duty_min)
        return max(0.0, 1 - norm_diff)

    def decide(self, current_temp, latency, power):
        """Returns (duty_cycle, stage_used, confidence)."""
        # Stage 1 (Fast NN)
        duty_fast = self.nn_fast.predict(current_temp, power, latency)
        conf_fast = self.get_confidence(duty_fast)
        if conf_fast >= self.conf_threshold:
            self.stage_counts["NN_FAST"] += 1
            return duty_fast, "NN_FAST", (conf_fast * 100)

        # Stage 2 (Slow NN)
        duty_slow = self.nn_slow.predict(current_temp, power, latency)
        conf_slow = self.get_confidence(duty_slow)
        if conf_slow >= self.conf_threshold:
            self.stage_counts["NN_SLOW"] += 1
            return duty_slow, "NN_SLOW", (conf_slow * 100)

        # Stage 3 (PID)
        duty_pid = self.pid.update(current_temp)
        fallback_conf = max(conf_fast, conf_slow)
        self.stage_counts["PID"] += 1
        return duty_pid, "PID", (fallback_conf * 100)

    def get_stage_breakdown(self):
        """Return dictionary with usage counts per stage."""
        return self.stage_counts
