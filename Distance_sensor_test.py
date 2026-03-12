#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from time import sleep
from ev3dev2.sensor import INPUT_2
from ev3dev2.sensor.lego import UltrasonicSensor

# 距離センサー（INPUT_2）
us = UltrasonicSensor(INPUT_2)

print("Ultrasonic Sensor Distance Monitor")

while True:
    distance = us.distance_centimeters
    print("Distance: {:.1f} cm".format(distance))
    sleep(0.2)