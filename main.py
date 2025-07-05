#main.py

from sensors import TemperatureSensors

import time
import RPi.GPIO as GPIO

temp_sensors = TemperatureSensors()

mosfet_pin = 12
GPIO.setwarnings(False)			
GPIO.setmode(GPIO.BCM)		
GPIO.setup(mosfet_pin, GPIO.OUT)
element_pwm = GPIO.PWM(mosfet_pin,1000)
element_pwm.start(0)		

def map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def main():
    try:
        while True:
            avg_temp = temp_sensors.read_avg_temperature([True, True,True,True], "c") 
            pwm_signal = map(avg_temp, 10.0, 83.0, 0.0, 100.0)
            element_pwm.ChangeDutyCycle(pwm_signal)
            print(f"Average Temperature from 4 sensors: {avg_temp} *C")
            
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
        

if __name__=="__main__":
    main()
