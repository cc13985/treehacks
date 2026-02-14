import sys
import os
import torch

# Point to the new src directory
sys.path.insert(0, "/Users/jeremoo/trehacks/lerobot/src")

try:
    # V0.4+ New Hardware Factory Location
    from lerobot.common.robot_devices.factory import make_robot
    print("✅ SUCCESS: Found make_robot in common.robot_devices.factory")
except ImportError:
    try:
        # Some interim branches use this
        from lerobot.robots.factory import make_robot
        print("✅ SUCCESS: Found make_robot in lerobot.robots.factory")
    except ImportError as e:
        print(f"❌ ERROR: Could not find hardware factory. {e}")
        # Debug: Print what IS inside common
        if os.path.exists("/Users/jeremoo/trehacks/lerobot/src/lerobot/common"):
            print("Contents of lerobot/common:", os.listdir("/Users/jeremoo/trehacks/lerobot/src/lerobot/common"))

print(f"✅ SUCCESS: Torch {torch.__version__} is ready!")