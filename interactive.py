import time
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper
import adafruit_motorkit

print(adafruit_motorkit.__file__)
kit = MotorKit(steppers_microsteps=4)
import sys


for i in range(int(sys.argv[3])):
    for j in range(16):
        if sys.argv[2] == "-1":
            kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.MICROSTEP)
        if sys.argv[2] == "1":
            kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.MICROSTEP)
        time.sleep(float(sys.argv[4]))
    # time.sleep(float(sys.argv[1]))
# kit._stepper1.release()
exit(1)
time.sleep(1)


def fwd(x=1):
    for i in range(x):
        print(kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.INTERLEAVE))
        time.sleep(0.01)


def back(x=1):
    for i in range(x):
        print(kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.INTERLEAVE))
        time.sleep(0.01)
