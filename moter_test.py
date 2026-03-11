#!/usr/bin/env python3

from ev3dev2.motor import MoveTank, OUTPUT_B, OUTPUT_C
from time import sleep

tank = MoveTank(OUTPUT_B, OUTPUT_C)

def forward():
    tank.on(50, 50)

def back():
    tank.on(-30, -30)

def left():
    tank.on(-20, 20)

def right():
    tank.on(20, -20)

def stop():
    tank.off(brake=True)

forward()
sleep(2)
stop()
sleep(1)

left()
sleep(1)
stop()