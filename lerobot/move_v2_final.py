import sys
import os
import time
import torch

# 1. Force Python to see the 'src' folder
current_dir = os.getcwd()
sys.path.insert(0, os.path.join(current_dir, "src"))

from lerobot.motors.feetech import FeetechMotorsBus

# 2. Mock MotorConfig just in case
try:
    from lerobot.motors.motors_bus import MotorConfig
except ImportError:
    class MotorConfig:
        def __init__(self, id, model):
            self.id = id
            self.model = model

# --- CONFIGURATION ---
PORT = "/dev/cu.usbmodem58FA0920121"

# 5-DOF Mapping
motors = {
    "base":     MotorConfig(id=1, model="sts3215"),
    "shoulder": MotorConfig(id=2, model="sts3215"),
    "elbow":    MotorConfig(id=3, model="sts3215"),
    "wrist":    MotorConfig(id=4, model="sts3215"),
    "gripper":  MotorConfig(id=6, model="sts3215")
}

print(f"Connecting to arm on {PORT}...")
bus = FeetechMotorsBus(port=PORT, motors=motors)
bus.connect()

print("✅ CONNECTED!")

# 3. READ current state first
# This gives us a tensor of 5 values (one for each motor)
current_pos = bus.read("Present_Position")
print(f"Current Joint Positions: {current_pos}")

# 4. Create a target (Move Base +50 steps)
# Note: Without calibration, these are raw steps (0-4096). 
# 50 steps is a small, safe wiggle.
target_pos = current_pos.clone()
print("Wiggling Base (Motor 1)...")

# Add 100 steps to the base (Index 0)
target_pos[0] = target_pos[0] + 100
bus.write("Goal_Position", target_pos)
time.sleep(1)

# Return to start
print("Returning...")
bus.write("Goal_Position", current_pos)
time.sleep(1)

bus.disconnect()
print("Done.")