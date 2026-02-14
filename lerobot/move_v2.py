import sys
import os
import time
import torch

# 1. Force Python to see the 'src' folder
current_dir = os.getcwd()
sys.path.insert(0, os.path.join(current_dir, "src"))

# 2. THE FIX: New Import Path for V2
# OLD: from lerobot.common.robot_devices.motors.feetech import FeetechMotorsBus
# NEW:
try:
    from lerobot.motors.feetech import FeetechMotorsBus
    print("✅ Found Feetech driver in 'lerobot.motors'")
except ImportError:
    # Backup: sometimes it's inside a 'drivers' subfolder
    from lerobot.motors.drivers.feetech import FeetechMotorsBus
    print("✅ Found Feetech driver in 'lerobot.motors.drivers'")

# --- CONFIGURATION ---
PORT = "/dev/cu.usbmodem58FA0920121"

# 5-DOF Mapping
motors = {
    "base": (1, "sts3215"),
    "shoulder": (2, "sts3215"),
    "elbow": (3, "sts3215"),
    "wrist": (4, "sts3215"),
    "gripper": (6, "sts3215")
}

print(f"Connecting to arm on {PORT}...")
bus = FeetechMotorsBus(port=PORT, motors=motors)
bus.connect()

print("✅ CONNECTED! The arm is live.")
print("Moving Base to Center (180)...")
bus.write("pos", torch.tensor([180.0]), motor_names=["base"])
time.sleep(1)

print("Wiggling Left...")
bus.write("pos", torch.tensor([160.0]), motor_names=["base"])
time.sleep(1)

print("Returning to Center...")
bus.write("pos", torch.tensor([180.0]), motor_names=["base"])
time.sleep(0.5)

bus.disconnect()
print("Done.")