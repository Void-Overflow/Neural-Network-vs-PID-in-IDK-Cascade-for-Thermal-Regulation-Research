#sensors.py

import board
import busio

import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn


class TemperatureSensors:
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.ads = ADS.ADS1115(i2c)
        self.ads.gain = 1

    def read_temperature(self, channel = 0, unit = "c"): #channel - ranges from 0 - 3 (A0 - A3 on ADC), unit of temperature
        sensor = None
        if channel == 1:
            sensor = ADS.P1
        elif channel == 2:
            sensor = ADS.P2
        elif channel == 3:
            sensor = ADS.P3
        else:
            sensor = ADS.P0
        chan = AnalogIn(self.ads, sensor)
        temperature = 0.0
        if (unit == "f"):
            temperature = ((chan.voltage - 0.5) * 100.0) * (9.0 / 5.0) + 32.0
        elif (unit == "c"):
            temperature = (chan.voltage - 0.5) * 100.0
        elif (unit == "k"):
            temperature = ((chan.voltage - 0.5) * 100.0) + 273.15
	
        return temperature
	
    def read_avg_temperature(self, sensors_used_list, unit = "c"):
        total = 0
        avg = 0.0
        for ch in range(4):
            if sensors_used_list[ch] == True:
                avg += self.read_temperature(ch, unit)
                total += 1
        return avg / total
