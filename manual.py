import time
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper
import adafruit_motorkit

print(adafruit_motorkit.__file__)
kit = MotorKit(steppers_microsteps=4)
import sys

sequence = [(1, 0, 1, 0), (0, 1, 1, 0), (0, 1, 0, 1), (1, 0, 0, 1)]
microsteps = 4
import math

curve = [math.sin(math.pi / (2 * microsteps) * i) for i in range(microsteps)]
print(curve)
old = (0, 0, 0, 0)
for n in range(5):
    for s in sequence:
        #      print(old,"vs",s)
        for t in range(microsteps):
            for i, c in enumerate(s):
                if c < old[i]:
                    kit.stepper1._coil[i].duty_cycle = int(curve[microsteps - t - 1] * 0xFFFF)
                #    print(i,kit.stepper1._coil[i].duty_cycle,"time rev:",microsteps-t)

                if c > old[i]:
                    kit.stepper1._coil[i].duty_cycle = int(curve[t] * 0xFFFF)
                #     print(i,kit.stepper1._coil[i].duty_cycle,"time:",t)
            #            print(i,(c!=old[i]),curve[t*(c-old[i])],t)
            print([kit.stepper1._coil[j].duty_cycle for j in range(4)])
            time.sleep(float(sys.argv[1]))
        old = s

exit(0)

for i in range(int(sys.argv[3])):
    # for j in range(64):
    if sys.argv[2] == "-1":
        print(kit.stepper1.onestep(direction=stepper.BACKWARD, style=stepper.INTERLEAVE))
    if sys.argv[2] == "1":
        print(kit.stepper1.onestep(direction=stepper.FORWARD, style=stepper.INTERLEAVE))
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
