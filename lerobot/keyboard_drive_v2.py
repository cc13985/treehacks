import sys
import time
import socket  # Required for receiving signals from Node-RED
from scservo_sdk import * # Ensure feetech-servo-sdk is installed

# --- 1. CONFIGURATION ---
DEVICENAME = '/dev/cu.usbmodem58FA0920121'  
BAUDRATE = 1000000

# UDP Configuration (Must match your Node-RED UDP Node)
UDP_IP = "127.0.0.1"
UDP_PORT = 5005

# Motor IDs
BASE = 1
SHOULDER = 2
ELBOW = 3
WRIST = 4
GRIPPER = 6

# --- 2. YOUR CALIBRATED POSES ---
POSES = {
    "HOME": {
        BASE: 2059, 
        SHOULDER: 1821, 
        ELBOW: 1317, 
        WRIST: 3051, 
        GRIPPER: 2475
    },
    "EXTEND": {
        BASE: 2043, 
        SHOULDER: 2477, 
        ELBOW: 1373, 
        WRIST: 2275, 
        GRIPPER: 2475  # Holding the object
    },
    "RIGHT": {
        BASE: 2568,      
        SHOULDER: 1821,  
        ELBOW: 1317,     
        WRIST: 3051,     
        GRIPPER: 2438    
    },
    "LEFT": {
        BASE: 1544,      
        SHOULDER: 1821,  
        ELBOW: 1317,     
        WRIST: 3051,     
        GRIPPER: 2438    
    }
}

# Gripper Settings
GRIPPER_HOLD = 2475  
GRIPPER_OPEN = 3000  # Based on your finding that 1800 was too tight

# --- 3. HARDWARE INITIALIZATION ---
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(0)

if not portHandler.openPort() or not portHandler.setBaudRate(BAUDRATE):
    print("❌ Connection Failed. Check USB cable and DEVICENAME.")
    sys.exit(1)

# Enable Torque for all motors
for id in [BASE, SHOULDER, ELBOW, WRIST, GRIPPER]:
    packetHandler.write1ByteTxRx(portHandler, id, 40, 1)

# Tracker for current motor positions
current_pos = {}
for id in [BASE, SHOULDER, ELBOW, WRIST, GRIPPER]:
    p, res, err = packetHandler.read2ByteTxRx(portHandler, id, 56)
    current_pos[id] = p

# --- 4. ANIMATION ENGINE ---

def write_motor(motor_id, pos):
    """Sends command to motor and updates internal tracker."""
    pos = int(max(0, min(4096, pos)))
    packetHandler.write2ByteTxRx(portHandler, motor_id, 42, pos)
    current_pos[motor_id] = pos

def smooth_move(target_pose, duration_sec=2.0):
    """Interpolates movement for cinematic smoothness."""
    hz = 50 
    steps = int(duration_sec * hz)
    start_snapshot = {mid: current_pos[mid] for mid in target_pose}
    
    for step in range(steps):
        progress = step / steps
        for mid, target in target_pose.items():
            start = start_snapshot[mid]
            new_val = start + (target - start) * progress
            write_motor(mid, new_val)
        time.sleep(1.0 / hz)
    
    for mid, target in target_pose.items():
        write_motor(mid, target)

# --- 5. BEHAVIORS ---

def behavior_hand_over():
    print("\n🤖 Behavior: HAND OVER (Focus Detected)")
    # 1. Extend Arm
    target = POSES["EXTEND"].copy()
    target[GRIPPER] = GRIPPER_HOLD
    smooth_move(target, duration_sec=2.5)
    time.sleep(0.5)
    # 2. Release item
    print("   Releasing item...")
    write_motor(GRIPPER, GRIPPER_OPEN) 
    time.sleep(1.0)
    # 3. Retract to Home
    print("   Retracting...")
    smooth_move(POSES["HOME"], duration_sec=2.0)
    print("✅ Ready for next command.")

def behavior_refuse():
    print("\n🤖 Behavior: REFUSE (Low Activity Detected)")
    # Shake head No (Left -> Right -> Left -> Home)
    smooth_move(POSES["LEFT"], duration_sec=0.4)
    smooth_move(POSES["RIGHT"], duration_sec=0.4)
    smooth_move(POSES["LEFT"], duration_sec=0.4)
    smooth_move(POSES["HOME"], duration_sec=1.0)
    print("✅ Ready for next command.")

# --- 6. MAIN LOOP (UDP LISTENER) ---
print("-----------------------------------------")
print(f"🧠 BCI RECEIVER ACTIVE ON PORT {UDP_PORT}")
print("   - High Beta (>1000): HAND OVER")
print("   - Low Beta (<10 for 5s): REFUSE")
print("-----------------------------------------")

# Setup Socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(False) 

try:
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            message = data.decode('utf-8').strip()
            
            # Continuous status update in terminal
            print(f"\rCurrent Brain State: {message}    ", end="", flush=True)

            if message == "APPROACH":
                behavior_hand_over()
                # Clear any queued messages while moving
                while True:
                    try: sock.recvfrom(1024)
                    except BlockingIOError: break
                print("🧠 Listening...")

            elif message == "REFUSE":
                behavior_refuse()
                # Clear any queued messages while moving
                while True:
                    try: sock.recvfrom(1024)
                    except BlockingIOError: break
                print("🧠 Listening...")

        except BlockingIOError:
            pass
        
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nShutting down...")
finally:
    portHandler.closePort()
    print("Disconnected.")