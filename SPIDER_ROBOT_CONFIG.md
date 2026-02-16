# Spider Robot Configuration Guide
# =================================

# Use this file as a reference for adjusting your spider robot.

## CURRENT ROBOT DIMENSIONS (from SpiderRobot.proto):
# Body: 0.12m x 0.04m x 0.08m (length x height x width)
# Coxa (hip): 0.04m length
# Femur (thigh): 0.06m length  
# Tibia (shin): 0.08m length
# Leg radius: 0.015m

## LEG ATTACHMENT POINTS:
# Front legs: ±0.06m from center (X), ±0.04m (Z)
# Rear legs: ±0.06m from center (X), ±0.04m (Z)

## JOINT ANGLES FOR GOOD STANDING POSE:
# Coxa (yaw): 0.0 rad (neutral)
# Femur (pitch): -0.6 to -0.8 rad (angled down)
# Tibia (pitch): 1.0 to 1.2 rad (bent up)

## TO ADJUST LINKAGE LENGTHS:
# 1. Edit the field values at the top of SpiderRobot.proto:
#    - bodySize
#    - coxaLength  
#    - femurLength
#    - tibiaLength
#    - legRadius

## TO TEST DIFFERENT POSES:
# 1. Use spider_test.py controller
# 2. Modify the position arrays in the code
# 3. Reload the world to see changes

## TROUBLESHOOTING COLLAPSED ROBOT:
# 1. Check if cylinders are properly rotated (rotation 0 0 1 1.5708)
# 2. Verify anchor points match link lengths
# 3. Ensure joint axes are correct (Y for coxa, X for femur/tibia)
# 4. Check physics masses aren't too light

## COORDINATE SYSTEM:
# X: Forward/Backward (positive = forward)
# Y: Up/Down (positive = up)  
# Z: Left/Right (positive = left when looking forward)

## TYPICAL SPIDER ROBOT PROPORTIONS:
# Body length: 100-150mm
# Coxa: 30-50mm
# Femur: 60-80mm  
# Tibia: 80-120mm
# Total leg span: ~300-400mm
