import sys
import tty
import termios
import os
import time

# Try to import the raw driver
try:
    from scservo_sdk import PortHandler, PacketHandler, COMM_SUCCESS
except ImportError:
    print("❌ ERROR: Driver missing. Run: pip install feetech-servo-sdk")
    sys.exit(1)

# --- CONFIGURATION ---
DEVICENAME = '/dev/cu.usbmodem58FA0920121'
BAUDRATE = 1000000

# Motor IDs
BASE = 1
SHOULDER = 2
ELBOW = 3
WRIST = 4
GRIPPER = 6

# Initial Positions (Center is 2048)
positions = {
    BASE: 2048,
    SHOULDER: 2048,
    ELBOW: 2048,
    WRIST: 2048,
    GRIPPER: 1500  # Gripper usually has a different range
}

# Step Size (Speed)
STEP = 50 

# Addresses
ADDR_GOAL_POSITION = 42

# Setup Driver
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(0)

if not portHandler.openPort():
    print("❌ Failed to open port")
    sys.exit(1)
if not portHandler.setBaudRate(BAUDRATE):
    print("❌ Failed to set baudrate")
    sys.exit(1)

def write_pos(motor_id, pos):
    # Safety Clamp (0 to 4096)
    pos = max(0, min(4096, pos))
    
    # Send Command
    packetHandler.write2ByteTxRx(portHandler, motor_id, ADDR_GOAL_POSITION, pos)
    return pos

def getch():
    # Reads a single keypress without hitting Enter
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

print("✅ ARM READY! Controls:")
print("---------------------------")
print("  [W] Shoulder Up    [S] Shoulder Down")
print("  [A] Base Left      [D] Base Right")
print("  [I] Elbow Up       [K] Elbow Down")
print("  [J] Wrist Left     [L] Wrist Right")
print("  [SPACE] Toggle Gripper")
print("  [Q] Quit")
print("---------------------------")

# --- CONTROL LOOP ---
try:
    gripper_open = False
    
    while True:
        key = getch().lower()
        
        if key == 'q':
            break
            
        # BASE (A/D)
        elif key == 'a':
            positions[BASE] += STEP
            positions[BASE] = write_pos(BASE, positions[BASE])
            print(f"Base: {positions[BASE]}")
        elif key == 'd':
            positions[BASE] -= STEP
            positions[BASE] = write_pos(BASE, positions[BASE])
            print(f"Base: {positions[BASE]}")
            
        # SHOULDER (W/S)
        elif key == 'w':
            positions[SHOULDER] += STEP
            positions[SHOULDER] = write_pos(SHOULDER, positions[SHOULDER])
            print(f"Shoulder: {positions[SHOULDER]}")
        elif key == 's':
            positions[SHOULDER] -= STEP
            positions[SHOULDER] = write_pos(SHOULDER, positions[SHOULDER])
            print(f"Shoulder: {positions[SHOULDER]}")

        # ELBOW (I/K)
        elif key == 'i':
            positions[ELBOW] += STEP
            positions[ELBOW] = write_pos(ELBOW, positions[ELBOW])
            print(f"Elbow: {positions[ELBOW]}")
        elif key == 'k':
            positions[ELBOW] -= STEP
            positions[ELBOW] = write_pos(ELBOW, positions[ELBOW])
            print(f"Elbow: {positions[ELBOW]}")
            
        # GRIPPER (Space)
        elif key == ' ':
            if gripper_open:
                # Close
                positions[GRIPPER] = 1500
                print("Gripper Closing...")
            else:
                # Open
                positions[GRIPPER] = 2000
                print("Gripper Opening...")
            write_pos(GRIPPER, positions[GRIPPER])
            gripper_open = not gripper_open

except KeyboardInterrupt:
    pass

finally:
    portHandler.closePort()
    print("\nDisconnected.")