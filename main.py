#main.py

from sensors import TemperatureSensors
from pid_controller import PIDController

import time
import RPi.GPIO as GPIO

baselineTemp = 30.0

temp_sensors = TemperatureSensors()
pid = PIDController(kp=5.0, ki=0.1, kd=1.0, setpoint=baselineTemp)

mosfet_pin = 12
GPIO.setwarnings(False)			
GPIO.setmode(GPIO.BCM)		
GPIO.setup(mosfet_pin, GPIO.OUT)
element_pwm = GPIO.PWM(mosfet_pin,1000)
element_pwm.start(0)		

def main():
    try:
        while True:
            current_avg_temp = temp_sensors.read_avg_temperature([True, True,True,True], "c") 
            
            duty_cycle = pid.update(current_avg_temp)
            duty_cycle = max(0, min(100, duty_cycle))
            
            element_pwm.ChangeDutyCycle(duty_cycle)
            
            print(f"Current Model: PID  Avg Temp: {current_avg_temp:.3f}  Set Temp: {baselineTemp:.3f}  Adjusted PWM Duty Cycle: {duty_cycle:.3f}        ", end="\r")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
        

if __name__=="__main__":
    main()
