import sys
import time
import threading

# Try to import the raw driver
try:
    from scservo_sdk import PortHandler, PacketHandler, COMM_SUCCESS
except ImportError:
    print("❌ ERROR: Driver missing. Run: pip install feetech-servo-sdk")
    sys.exit(1)

try:
    from pynput import keyboard
except ImportError:
    print("❌ ERROR: pynput missing. Run: pip install pynput")
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

# Speed: per-keypress step (legacy) and per-tick for smooth hold
STEP = 50
GRIPPER_STEP = 50
# Smooth hold: movement per control tick (smaller = smoother, ~30–40 Hz loop)
MOVE_PER_TICK = 8
GRIPPER_PER_TICK = 6
CONTROL_HZ = 35

# Software limits (servo range 0-4096); movement is ignored at limits
MIN_POS = 0
MAX_POS = 4096

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

# Keys currently held (for smooth movement). Thread-safe.
pressed_keys = set()
pressed_lock = threading.Lock()

def on_press(key):
    try:
        c = key.char.lower() if key.char else None
    except AttributeError:
        c = None
    if c and c in 'qwasdiklj;u':
        with pressed_lock:
            pressed_keys.add(c)

def on_release(key):
    try:
        c = key.char.lower() if key.char else None
    except AttributeError:
        c = None
    if c:
        with pressed_lock:
            pressed_keys.discard(c)
    # Quit on Q
    if c == 'q':
        return False  # Stop listener

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
print("  HOLD keys to move smoothly:")
print("  [W] Shoulder Up    [S] Shoulder Down")
print("  [A] Base Left      [D] Base Right")
print("  [I] Elbow Up       [K] Elbow Down")
print("  [L] Wrist Left     [;] Wrist Right")
print("  [U] Gripper OPEN   [J] Gripper CLOSE")
print("  [Q] Quit")
print("---------------------------")

running = True

def on_release_quit(key):
    global running
    on_release(key)
    try:
        if key.char and key.char.lower() == 'q':
            running = False
            return False
    except AttributeError:
        pass
    return True

# Start keyboard listener in background
listener = keyboard.Listener(on_press=on_press, on_release=on_release_quit)
listener.daemon = True
listener.start()

tick_duration = 1.0 / CONTROL_HZ
last_status_time = [0]  # use list so inner fn can update

try:
    while running:
        t0 = time.perf_counter()
        with pressed_lock:
            keys = set(pressed_keys)
        for key in keys:
            # BASE (a = +, d = -)
            if key == 'a' and positions[BASE] < MAX_POS:
                positions[BASE] = write_pos(BASE, positions[BASE] + MOVE_PER_TICK)
            elif key == 'd' and positions[BASE] > MIN_POS:
                positions[BASE] = write_pos(BASE, positions[BASE] - MOVE_PER_TICK)
            # SHOULDER (w = +, s = -)
            elif key == 'w' and positions[SHOULDER] < MAX_POS:
                positions[SHOULDER] = write_pos(SHOULDER, positions[SHOULDER] + MOVE_PER_TICK)
            elif key == 's' and positions[SHOULDER] > MIN_POS:
                positions[SHOULDER] = write_pos(SHOULDER, positions[SHOULDER] - MOVE_PER_TICK)
            # ELBOW (i = +, k = -)
            elif key == 'i' and positions[ELBOW] < MAX_POS:
                positions[ELBOW] = write_pos(ELBOW, positions[ELBOW] + MOVE_PER_TICK)
            elif key == 'k' and positions[ELBOW] > MIN_POS:
                positions[ELBOW] = write_pos(ELBOW, positions[ELBOW] - MOVE_PER_TICK)
            # WRIST (l = +, ; = -)
            elif key == 'l' and positions[WRIST] < MAX_POS:
                positions[WRIST] = write_pos(WRIST, positions[WRIST] + MOVE_PER_TICK)
            elif key == ';' and positions[WRIST] > MIN_POS:
                positions[WRIST] = write_pos(WRIST, positions[WRIST] - MOVE_PER_TICK)
            # GRIPPER (u = open +, j = close -)
            elif key == 'u' and positions[GRIPPER] < MAX_POS:
                positions[GRIPPER] = write_pos(GRIPPER, positions[GRIPPER] + GRIPPER_PER_TICK)
            elif key == 'j' and positions[GRIPPER] > MIN_POS:
                positions[GRIPPER] = write_pos(GRIPPER, positions[GRIPPER] - GRIPPER_PER_TICK)
        # Status line every ~0.2 s to avoid spam
        now = time.perf_counter()
        if now - last_status_time[0] >= 0.2:
            last_status_time[0] = now
            print(f"\r  Base:{positions[BASE]} Shoulder:{positions[SHOULDER]} Elbow:{positions[ELBOW]} Wrist:{positions[WRIST]} Gripper:{positions[GRIPPER]}   ", end="", flush=True)
        elapsed = time.perf_counter() - t0
        time.sleep(max(0, tick_duration - elapsed))
except KeyboardInterrupt:
    pass
finally:
    running = False
    portHandler.closePort()
    print("\nDisconnected.")