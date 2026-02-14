import sys
import os

# --- THE FIX ---
# This forces Python to look inside the 'src' folder for the code
current_dir = os.getcwd()
sys.path.append(os.path.join(current_dir, "src"))
# ----------------

import time
import torch
from lerobot.common.robot_devices.motors.feetech import FeetechMotorsBus

# --- CONFIGURATION ---
PORT = "/dev/cu.usbmodem58FA0920121"

# Motor Map: { Name: [ID, Model] }
motors = {
    "base": [1, "sts3215"],
    "shoulder": [2, "sts3215"],
    "elbow": [3, "sts3215"],
    "wrist": [4, "sts3215"],
    "gripper": [6, "sts3215"]
}

print(f"Connecting to arm on {PORT}...")
bus = FeetechMotorsBus(port=PORT, motors=motors)
bus.connect()

print("✅ Connected! Moving Base (Motor 1) to Center...")
# 180 is center for these motors
bus.write("pos", torch.tensor([180.0]), motor_names=["base"])
time.sleep(1)

print("Wiggling Left...")
bus.write("pos", torch.tensor([160.0]), motor_names=["base"])
time.sleep(1)

print("Returning to Center...")
bus.write("pos", torch.tensor([180.0]), motor_names=["base"])
time.sleep(0.5)

bus.disconnect()
print("Done. Safe to unplug.")