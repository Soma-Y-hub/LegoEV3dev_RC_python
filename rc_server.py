#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import signal
import time
import threading

from ev3dev2.motor import MoveTank, OUTPUT_B, OUTPUT_C
from ev3dev2.sensor import INPUT_2
from ev3dev2.sensor.lego import UltrasonicSensor

# ===== 設定 =====
LEFT_PORT = OUTPUT_B
RIGHT_PORT = OUTPUT_C
SENSOR_PORT = INPUT_2

# 速度設定
DRIVE_SPEED = 80
TURN_SPEED = 25
CURVE_SPEED = 60

# 距離設定
STOP_DISTANCE_CM = 20.0     # この距離未満で停止
RESUME_DISTANCE_CM = 25.0   # この距離以上で再開

# 監視周期
MONITOR_INTERVAL = 0.05
PRINT_INTERVAL = 0.2

# ===== 初期化 =====
tank = MoveTank(LEFT_PORT, RIGHT_PORT)
us = UltrasonicSensor(SENSOR_PORT)

running = True
state_lock = threading.Lock()

# 現在状態
current_command = "S"
forward_motion = False
obstacle_stop = False

# 障害物停止前の前進コマンドを記録
last_forward_command = None


def get_distance_cm():
    try:
        return us.distance_centimeters
    except Exception as e:
        print("Sensor read error:", e)
        return None


def set_motion_state(cmd, is_forward):
    global current_command, forward_motion
    with state_lock:
        current_command = cmd
        forward_motion = is_forward


def set_obstacle_stop(value):
    global obstacle_stop
    with state_lock:
        obstacle_stop = value


def is_obstacle_stop():
    with state_lock:
        return obstacle_stop


def is_forward_motion():
    with state_lock:
        return forward_motion


def set_last_forward_command(cmd):
    global last_forward_command
    with state_lock:
        last_forward_command = cmd


def get_last_forward_command():
    with state_lock:
        return last_forward_command


def stop_motor():
    tank.off(brake=True)
    set_motion_state("S", False)


def forward():
    tank.on(DRIVE_SPEED, DRIVE_SPEED)
    set_motion_state("F", True)


def back():
    tank.on(-DRIVE_SPEED, -DRIVE_SPEED)
    set_motion_state("B", False)


def left():
    tank.on(-TURN_SPEED, TURN_SPEED)
    set_motion_state("L", False)


def right():
    tank.on(TURN_SPEED, -TURN_SPEED)
    set_motion_state("R", False)


def forward_left():
    tank.on(CURVE_SPEED, DRIVE_SPEED)
    set_motion_state("FL", True)


def forward_right():
    tank.on(DRIVE_SPEED, CURVE_SPEED)
    set_motion_state("FR", True)


def back_left():
    tank.on(-CURVE_SPEED, -DRIVE_SPEED)
    set_motion_state("BL", False)


def back_right():
    tank.on(-DRIVE_SPEED, -CURVE_SPEED)
    set_motion_state("BR", False)


def stop():
    stop_motor()
    print("CMD: STOP")


def resume_last_forward_motion():
    cmd = get_last_forward_command()

    if cmd == "F":
        forward()
        print("AUTO RESUME: FORWARD")

    elif cmd == "FL":
        forward_left()
        print("AUTO RESUME: FORWARD LEFT")

    elif cmd == "FR":
        forward_right()
        print("AUTO RESUME: FORWARD RIGHT")


def execute(cmd):
    cmd = cmd.strip().upper()

    if cmd == "F":
        set_last_forward_command("F")
        if is_obstacle_stop():
            stop_motor()
            print("CMD: FORWARD blocked")
        else:
            forward()
            print("CMD: FORWARD")

    elif cmd == "B":
        set_obstacle_stop(False)
        back()
        print("CMD: BACK")

    elif cmd == "L":
        set_obstacle_stop(False)
        left()
        print("CMD: LEFT")

    elif cmd == "R":
        set_obstacle_stop(False)
        right()
        print("CMD: RIGHT")

    elif cmd == "FL":
        set_last_forward_command("FL")
        if is_obstacle_stop():
            stop_motor()
            print("CMD: FORWARD LEFT blocked")
        else:
            forward_left()
            print("CMD: FORWARD LEFT")

    elif cmd == "FR":
        set_last_forward_command("FR")
        if is_obstacle_stop():
            stop_motor()
            print("CMD: FORWARD RIGHT blocked")
        else:
            forward_right()
            print("CMD: FORWARD RIGHT")

    elif cmd == "BL":
        set_obstacle_stop(False)
        back_left()
        print("CMD: BACK LEFT")

    elif cmd == "BR":
        set_obstacle_stop(False)
        back_right()
        print("CMD: BACK RIGHT")

    elif cmd == "S":
        set_obstacle_stop(False)
        stop()

    else:
        print("UNKNOWN CMD:", cmd)


def distance_monitor():
    last_print_time = 0.0

    while running:
        dist = get_distance_cm()
        now = time.time()

        if dist is not None:
            if now - last_print_time >= PRINT_INTERVAL:
                print("Distance: {:.1f} cm".format(dist))
                last_print_time = now

            # 前進中に障害物が近づいたら停止
            if is_forward_motion() and dist < STOP_DISTANCE_CM:
                set_obstacle_stop(True)
                stop_motor()
                print("!!! EMERGENCY STOP: {:.1f} cm !!!".format(dist))

            # 障害物停止中で、十分離れたら自動再開
            elif is_obstacle_stop() and dist >= RESUME_DISTANCE_CM:
                set_obstacle_stop(False)
                print("Obstacle cleared: {:.1f} cm".format(dist))
                resume_last_forward_motion()

        time.sleep(MONITOR_INTERVAL)


def cleanup(*_args):
    global running
    running = False
    stop_motor()
    print("Shutdown: motor stopped.")


signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


def main():
    global running

    if len(sys.argv) < 2:
        print("Usage: python3 rc_server.py /dev/rfcomm0")
        sys.exit(1)

    dev = sys.argv[1]

    print("Open RFCOMM device:", dev)
    print("Motor ports:", LEFT_PORT, RIGHT_PORT)
    print("Ultrasonic sensor port:", SENSOR_PORT)
    print("Stop distance: {:.1f} cm".format(STOP_DISTANCE_CM))
    print("Resume distance: {:.1f} cm".format(RESUME_DISTANCE_CM))

    stop_motor()

    monitor_thread = threading.Thread(target=distance_monitor, daemon=True)
    monitor_thread.start()

    with open(dev, "r", buffering=1, encoding="utf-8", errors="ignore") as fp:
        print("Connected. Waiting for commands: F/B/L/R/S/FL/FR/BL/BR")

        while running:
            line = fp.readline()

            if line == "":
                print("Disconnected.")
                break

            line = line.strip()
            if not line:
                continue

            execute(line)

    running = False
    stop_motor()
    print("Exited safely.")


if __name__ == "__main__":
    main()