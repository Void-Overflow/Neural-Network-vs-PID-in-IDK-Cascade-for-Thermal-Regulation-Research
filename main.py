#main.py

from sensors import TemperatureSensors
from research_logger import ResearchLogger
from pid_controller import PIDController
from nn_controller import NeuralNetController
from idk_cascade import IDKCascade

import time
import RPi.GPIO as GPIO
import sys

def overwrite_console(model_type, avg_temp, baseline_temp, duty_cycle, power=None, latency=None, elapsed_time=None, duration_time=None, confidence=None, model=None, stage_breakdown=None):
    sys.stdout.write("\033[F" * (3 if confidence is not None else 2 if power is not None else 1)) # Move cursor up 3 lines if logging
    sys.stdout.flush()

    sys.stdout.write(f"\rCurrent Model: {model_type}  Avg Temp: {avg_temp:.2f}°C  "
                     f"Set Temp: {baseline_temp:.2f}°C  PWM Duty: {duty_cycle:.2f}%      \n")
    if power is not None and latency is not None:
        sys.stdout.write(f"Power: {power:.3f} W  Latency: {latency:.2f} ms  Time Elapsed: {elapsed_time:.2f} min / {duration_time:.2f} min       \n")
    if confidence is not None and model is not None:
        sys.stdout.write(f"Current Model: {model}  Model Confidence: {confidence}%  Model Stage Occurences: PID-{stage_breakdown['PID']} NN1(fast)-{stage_breakdown['NN_FAST']} NN2(slow)-{stage_breakdown['NN_SLOW']}        \n")
    sys.stdout.flush()


def get_user_input():
    print("Available Modes: PID, NN1 (fast), NN2 (slow), IDK_0.1, IDK_0.3, IDK_0.5, IDK_0.7, IDK_0.9")
    model_choice = input("Enter control model: ").strip().upper()

    if not (model_choice == "PID" or model_choice.startswith("NN") or model_choice.startswith("IDK_")):
        print("Invalid model. Defaulting to PID.")
        model_choice = "PID"

    try:
        baseline_temp = float(input("Enter baseline temperature in °C (default = 16): ") or "16")
    except ValueError:
        print("Invalid input. Using default 30°C.")
        baseline_temp = 16.0

    if model_choice == "PID":
        log_choice = input("Do you want to log the the data during this run? (y/n): ").strip().lower()
        logging_enabled = log_choice == 'y'
    else:
        logging_enabled = True

    duration = 45.0
    if logging_enabled == True:
        try:
            duration = float(input("How long would you like the trial to collect data in minutes? (default = 45): ") or "45")
        except ValueError:
            print("Invalid input. Using default 45 minutes")
            duration = 45

    print("\n\n\n")

    return model_choice, baseline_temp, logging_enabled, duration


def main():
    model_type, baselineTemp, logging, duration = get_user_input()

    temp_sensors = TemperatureSensors()
    logger = ResearchLogger(trial_name=model_type, baseline_temp=baselineTemp, log_interval=1.0, duration_minutes=duration) if logging else None
    
    pid = PIDController(kp=5.0, ki=0.5, kd=1.0, setpoint=baselineTemp)
    
    NN = None
    cascade = None 

    if model_type.startswith("IDK_"):
        conf_value = float(model_type.split("_")[1])
        cascade = IDKCascade(baseline_temp=baselineTemp, conf_threshold=conf_value)
    
    elif model_type.startswith("NN"):
        NN_Path = "neural_networks/" + model_type + "/"
        NN = NeuralNetController(NN_Path)

    mosfet_pin = 12
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(mosfet_pin, GPIO.OUT)
    element_pwm = GPIO.PWM(mosfet_pin, 20000)
    element_pwm.start(0)

    try:
        while True:
            current_avg_temp = temp_sensors.read_avg_temperature([True, True, True, True], "c")
            source, confidence = model_type, None

            if model_type.upper() == "PID":
                duty_cycle = pid.update(current_avg_temp)

            elif model_type.startswith("NN"):
                if len(logger.latencies) > 1 and len(logger.power_history) > 1:
                    duty_cycle = NN.predict(current_avg_temp, logger.latencies[-1], logger.power_history[-1])
                else:
                    duty_cycle = pid.update(current_avg_temp)

            elif model_type.startswith("IDK_"):
                if len(logger.latencies) > 1 and len(logger.power_history) > 1:
                    duty_cycle, source, confidence = cascade.decide(current_avg_temp, logger.latencies[-1], logger.power_history[-1])
                else:
                    duty_cycle = pid.update(current_avg_temp)

            duty_cycle = max(0, min(100, duty_cycle))
            element_pwm.ChangeDutyCycle(duty_cycle)

            if logging:
                if not logger.log(current_avg_temp, duty_cycle, confidence, source):
                    break
                if confidence is not None:
                    overwrite_console(model_type, current_avg_temp, baselineTemp, duty_cycle, 
                            power=logger.power_history[-1], 
                            latency=logger.latencies[-1], 
                            elapsed_time = (time.time() - logger.start_time)/60.0, 
                            duration_time = duration,
                            confidence = confidence,
                            model=source,
                            stage_breakdown=cascade.get_stage_breakdown())
                else:
                    overwrite_console(model_type, current_avg_temp, baselineTemp, duty_cycle, 
                            power=logger.power_history[-1], 
                            latency=logger.latencies[-1], 
                            elapsed_time = (time.time() - logger.start_time)/60.0, 
                            duration_time = duration)
            else:
                overwrite_console(model_type, current_avg_temp, baselineTemp, duty_cycle)

            time.sleep(1)

    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        element_pwm.stop()
        GPIO.cleanup()
        if logging:
            logger.summarize(stages=cascade.get_stage_breakdown())
        print("System shutdown complete.")

if __name__=="__main__":
    main()
