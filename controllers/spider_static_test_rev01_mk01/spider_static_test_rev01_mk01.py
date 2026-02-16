from controller import Robot
import math

TIME_STEP = 16

robot = Robot()

print("Robot Initialized")
# 1) Get the motor
coxa_motor = robot.getDevice("coxa_motor")  # MUST match name above
print("coxa_motor =", coxa_motor)

if coxa_motor is None:
    print("ERROR: motor 'coxa_motor' not found")
    quit()

# 2) Put motor in position mode and give it some speed
coxa_motor.setPosition(0.0)   # not infinity -> position control
coxa_motor.setVelocity(2.0)   # rad/s

t = 0.0

while robot.step(TIME_STEP) != -1:
    t += TIME_STEP / 1000.0

    # simple swing ±0.5 rad
    target = 0.5 * math.sin(2.0 * t)
    coxa_motor.setPosition(target)
