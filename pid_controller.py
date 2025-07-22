#pid_controller.py

import time

class PIDController:
    def __init__(self, kp, ki, kd, setpoint=25.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.integral = 0
        self.prev_error = 0
        self.prev_time = None

    def update(self, measured_value):
        current_time = time.time()
        error = measured_value - self.setpoint

        if self.prev_time is None:
            self.prev_time = current_time
            return 0

        dt = current_time - self.prev_time
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt if dt > 0 else 0

        output = (
            self.kp * error +
            self.ki * self.integral +
            self.kd * derivative
        )
        output = max(-100, min(100, output))
        
        self.prev_error = error
        self.prev_time = current_time
        
        self.integral += error * dt

        self.integral = max(-100, min(self.integral, 100))

        #print(f"[PID] error={error:.2f}, output={output:.2f}, dt={dt:.2f}")
        return output
