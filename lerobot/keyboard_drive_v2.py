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

# Motor Map
BASE = 1
SHOULDER = 2
ELBOW = 3
WRIST = 4
GRIPPER = 6  # Verified ID

# Initial Positions (Center is 2048)
# We track these variables in Python so we don't have to read from the motor every loop (too slow)
positions = {
    BASE: 2048,
    SHOULDER: 2048,
    ELBOW: 2048,
    WRIST: 2048,
    GRIPPER: 2048 
}

# Speed
STEP = 50 
GRIPPER_STEP = 50

# Addresses
ADDR_TORQUE_ENABLE = 40
ADDR_GOAL_POSITION = 42

# Setup Driver
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(0)

if not portHandler.openPort() or not portHandler.setBaudRate(BAUDRATE):
    print("❌ Connection Failed.")
    sys.exit(1)

# --- HELPER FUNCTIONS ---
def enable_torque(motor_id):
    packetHandler.write1ByteTxRx(portHandler, motor_id, ADDR_TORQUE_ENABLE, 1)

def write_pos(motor_id, pos):
    # Clamp to safe range (0-4096)
    pos = max(0, min(4096, pos))
    packetHandler.write2ByteTxRx(portHandler, motor_id, ADDR_GOAL_POSITION, pos)
    return pos

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

# --- INITIALIZATION ---
print("Waking up motors...")
for id in [BASE, SHOULDER, ELBOW, WRIST, GRIPPER]:
    enable_torque(id)
    # Optional: Read current pos so the robot doesn't jerk on startup
    p, res, err = packetHandler.read2ByteTxRx(portHandler, id, 56) # 56 is Present Pos
    if res == COMM_SUCCESS:
        positions[id] = p

print(f"✅ ARM READY! Gripper is at {positions[GRIPPER]}")
print("---------------------------")
print("  [W] Shoulder Up    [S] Shoulder Down")
print("  [A] Base Left      [D] Base Right")
print("  [I] Elbow Up       [K] Elbow Down")
print("  [L] Wrist Left     [ ; ] Wrist Right") # Changed to ; for standard layout
print("  [U] Gripper OPEN   [J] Gripper CLOSE") # Incremental control
print("  [Q] Quit")
print("---------------------------")

# --- CONTROL LOOP ---
try:
    while True:
        key = getch().lower()
        
        if key == 'q':
            break
            
        # BASE
        elif key == 'a':
            positions[BASE] += STEP
            positions[BASE] = write_pos(BASE, positions[BASE])
            print(f"Base: {positions[BASE]}")
        elif key == 'd':
            positions[BASE] -= STEP
            positions[BASE] = write_pos(BASE, positions[BASE])
            print(f"Base: {positions[BASE]}")
            
        # SHOULDER
        elif key == 'w':
            positions[SHOULDER] += STEP
            positions[SHOULDER] = write_pos(SHOULDER, positions[SHOULDER])
            print(f"Shoulder: {positions[SHOULDER]}")
        elif key == 's':
            positions[SHOULDER] -= STEP
            positions[SHOULDER] = write_pos(SHOULDER, positions[SHOULDER])
            print(f"Shoulder: {positions[SHOULDER]}")

        # ELBOW
        elif key == 'i':
            positions[ELBOW] += STEP
            positions[ELBOW] = write_pos(ELBOW, positions[ELBOW])
            print(f"Elbow: {positions[ELBOW]}")
        elif key == 'k':
            positions[ELBOW] -= STEP
            positions[ELBOW] = write_pos(ELBOW, positions[ELBOW])
            print(f"Elbow: {positions[ELBOW]}")
        
        # WRIST (New mapping for easier reach)
        elif key == 'l':
            positions[WRIST] += STEP
            positions[WRIST] = write_pos(WRIST, positions[WRIST])
            print(f"Wrist: {positions[WRIST]}")
        elif key == ';':
            positions[WRIST] -= STEP
            positions[WRIST] = write_pos(WRIST, positions[WRIST])
            print(f"Wrist: {positions[WRIST]}")

        # GRIPPER (Incremental)
        elif key == 'u': # Open
            positions[GRIPPER] += GRIPPER_STEP
            positions[GRIPPER] = write_pos(GRIPPER, positions[GRIPPER])
            print(f"Gripper Opening... ({positions[GRIPPER]})")
        elif key == 'j': # Close
            positions[GRIPPER] -= GRIPPER_STEP
            positions[GRIPPER] = write_pos(GRIPPER, positions[GRIPPER])
            print(f"Gripper Closing... ({positions[GRIPPER]})")

except KeyboardInterrupt:
    pass

finally:
    portHandler.closePort()
    print("\nDisconnected.")