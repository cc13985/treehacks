import os
import time
import sys

# Try to import the raw driver (installed via feetech-servo-sdk)
try:
    from scservo_sdk import PortHandler, PacketHandler, COMM_SUCCESS
except ImportError:
    print("❌ ERROR: Driver missing. Run: pip install feetech-servo-sdk")
    sys.exit(1)

# --- CONFIGURATION ---
DEVICENAME = '/dev/cu.usbmodem58FA0920121'
BAUDRATE = 1000000  # Standard for STS3215 motors

# Motor ID to test
MOTOR_ID = 1  # Base motor

# STS3215 Register Table
ADDR_GOAL_POSITION = 42
ADDR_PRESENT_POSITION = 56

# Initialize Port & Packet Handlers
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(0) # Protocol 0 is standard for STS

# 1. Open Port
if portHandler.openPort():
    print(f"✅ Succeeded to open the port: {DEVICENAME}")
else:
    print("❌ Failed to open the port")
    sys.exit(1)

# 2. Set Baudrate
if portHandler.setBaudRate(BAUDRATE):
    print(f"✅ Baudrate set to {BAUDRATE}")
else:
    print("❌ Failed to set baudrate")
    sys.exit(1)

# 3. Move to Center (Step 2048)
# Range is 0-4096. Center is 2048.
target_pos = 2048
print(f"Moving Motor {MOTOR_ID} to Center (Step {target_pos})...")

# Write 2 bytes to the Goal Position address
result, error = packetHandler.write2ByteTxRx(portHandler, MOTOR_ID, ADDR_GOAL_POSITION, target_pos)

if result != COMM_SUCCESS:
    print(f"❌ Write failed: {packetHandler.getTxRxResult(result)}")
elif error != 0:
    print(f"❌ Motor Error: {packetHandler.getRxPacketError(error)}")
else:
    print("✅ Command sent successfully!")

# 4. Wiggle (Move to 2200)
time.sleep(1)
print(f"Wiggling to Step 2200...")
packetHandler.write2ByteTxRx(portHandler, MOTOR_ID, ADDR_GOAL_POSITION, 2200)
time.sleep(1)

# 5. Return to Center
print("Returning to Center...")
packetHandler.write2ByteTxRx(portHandler, MOTOR_ID, ADDR_GOAL_POSITION, 2048)

# Close
portHandler.closePort()
print("Done.")