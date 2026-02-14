import sys
import os
import time
import torch

# 1. Force Python to see the 'src' folder
current_dir = os.getcwd()
sys.path.insert(0, os.path.join(current_dir, "src"))

# 2. Import the Feetech Driver
from lerobot.motors.feetech import FeetechMotorsBus

# 3. Import the MotorConfig class (The missing piece!)
try:
    # It usually lives here in V2
    from lerobot.motors.motors_bus import MotorConfig
    print("✅ Found MotorConfig class")
except ImportError:
    print("⚠️ Could not find MotorConfig, defining a temporary one...")
    # Fallback if the import moves again
    class MotorConfig:
        def __init__(self, id, model):
            self.id = id
            self.model = model

# --- CONFIGURATION ---
PORT = "/dev/cu.usbmodem58FA0920121"

# 4. Define motors using the Object, not just a tuple
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

print("✅ CONNECTED! The arm is live.")
print("Moving Base to Center (180)...")
# Note: Newer buses might expect 'degrees' not 'pos', but let's try 'pos' first
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