#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import signal
from ev3dev2.motor import MoveTank, OUTPUT_B, OUTPUT_C

# ===== 設定 =====
LEFT_PORT = OUTPUT_B
RIGHT_PORT = OUTPUT_C

# 前進・後退の速度
DRIVE_SPEED = 60

# 旋回の速度
TURN_SPEED = 25

# カーブ時の内輪側速度
CURVE_SPEED = 40

# ===== モーター初期化 =====
tank = MoveTank(LEFT_PORT, RIGHT_PORT)

running = True


def forward():
    tank.on(DRIVE_SPEED, DRIVE_SPEED)


def back():
    tank.on(-DRIVE_SPEED, -DRIVE_SPEED)


def left():
    tank.on(-TURN_SPEED, TURN_SPEED)


def right():
    tank.on(TURN_SPEED, -TURN_SPEED)


def forward_left():
    tank.on(CURVE_SPEED, DRIVE_SPEED)


def forward_right():
    tank.on(DRIVE_SPEED, CURVE_SPEED)


def back_left():
    tank.on(-CURVE_SPEED, -DRIVE_SPEED)


def back_right():
    tank.on(-DRIVE_SPEED, -CURVE_SPEED)


def stop():
    tank.off(brake=True)


def execute(cmd):
    cmd = cmd.strip().upper()

    if cmd == "F":
        forward()
        print("CMD: FORWARD")

    elif cmd == "B":
        back()
        print("CMD: BACK")

    elif cmd == "L":
        left()
        print("CMD: LEFT")

    elif cmd == "R":
        right()
        print("CMD: RIGHT")

    elif cmd == "FL":
        forward_left()
        print("CMD: FORWARD LEFT")

    elif cmd == "FR":
        forward_right()
        print("CMD: FORWARD RIGHT")

    elif cmd == "BL":
        back_left()
        print("CMD: BACK LEFT")

    elif cmd == "BR":
        back_right()
        print("CMD: BACK RIGHT")

    elif cmd == "S":
        stop()
        print("CMD: STOP")

    else:
        print("UNKNOWN CMD:", cmd)


def cleanup(*_args):
    global running
    running = False
    stop()
    print("Shutdown: motor stopped.")


signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 rc_server.py /dev/rfcomm0")
        sys.exit(1)

    dev = sys.argv[1]
    print("Open RFCOMM device:", dev)

    with open(dev, "r", buffering=1, encoding="utf-8", errors="ignore") as fp:
        stop()
        print("Connected. Waiting for commands: F/B/L/R/S/FL/FR/BL/BR")

        while running:
            line = fp.readline()
            if line == "":
                print("Disconnected.")
                break

            line = line.strip()
            if not line:
                continue

            # 1行を1コマンドとして処理
            execute(line)

    stop()
    print("Exited safely.")


if __name__ == "__main__":
    main()