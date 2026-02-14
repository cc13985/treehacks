import sys
import time
from scservo_sdk import PortHandler, PacketHandler, COMM_SUCCESS

# --- CONFIG ---
DEVICENAME = '/dev/cu.usbmodem58FA0920121'
BAUDRATE = 1000000
GRIPPER_ID = 6

# STS3215 Addresses
ADDR_TORQUE_ENABLE = 40
ADDR_GOAL_POSITION = 42
ADDR_PRESENT_POSITION = 56

portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(0)

if not portHandler.openPort() or not portHandler.setBaudRate(BAUDRATE):
    print("❌ Failed to open port")
    sys.exit(1)

print(f"Testing Gripper (ID {GRIPPER_ID})...")

# 1. Ping the motor to see if it exists
model_number, result, error = packetHandler.ping(portHandler, GRIPPER_ID)
if result != COMM_SUCCESS:
    print(f"❌ PING FAILED! Motor {GRIPPER_ID} is not responding.")
    print("Check your cable connection to the gripper.")
    sys.exit(1)
else:
    print(f"✅ Pong! Found Motor {GRIPPER_ID}.")

# 2. FORCE TORQUE ON (Wake it up)
print("Enabling Torque...")
packetHandler.write1ByteTxRx(portHandler, GRIPPER_ID, ADDR_TORQUE_ENABLE, 1)

# 3. Read where it is right now
current_pos, result, error = packetHandler.read2ByteTxRx(portHandler, GRIPPER_ID, ADDR_PRESENT_POSITION)
print(f"Current Gripper Position: {current_pos}")

if current_pos == 0:
    print("⚠️ Warning: Position 0 might mean the motor is lost or uncalibrated.")

# 4. Gentle Wiggle (Open/Close by 200 steps)
print("Attempting to CLOSE (Move -200 steps)...")
target = current_pos - 200
packetHandler.write2ByteTxRx(portHandler, GRIPPER_ID, ADDR_GOAL_POSITION, target)
time.sleep(1)

print("Attempting to OPEN (Move +200 steps)...")
target = current_pos + 200
packetHandler.write2ByteTxRx(portHandler, GRIPPER_ID, ADDR_GOAL_POSITION, target)
time.sleep(1)

# 5. Return
print("Relaxing...")
packetHandler.write2ByteTxRx(portHandler, GRIPPER_ID, ADDR_GOAL_POSITION, current_pos)
packetHandler.write1ByteTxRx(portHandler, GRIPPER_ID, ADDR_TORQUE_ENABLE, 0) # Torque Off

portHandler.closePort()
print("Done.")