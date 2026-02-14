import sys
import os

# Point to source
current_dir = os.getcwd()
src_path = os.path.join(current_dir, "src")
sys.path.insert(0, src_path)

print(f"🔎 Looking for code in: {src_path}")

try:
    import lerobot
    print(f"✅ Found LeRobot at: {lerobot.__file__}")
    
    # List what's inside the package
    package_dir = os.path.dirname(lerobot.__file__)
    print(f"📂 Contents of package: {os.listdir(package_dir)}")
    
    # Check for common
    if "common" in os.listdir(package_dir):
        print("✅ 'common' folder exists!")
        print(f"   Contents: {os.listdir(os.path.join(package_dir, 'common'))}")
    else:
        print("❌ 'common' folder is MISSING. This is the problem.")

except ImportError as e:
    print(f"❌ Failed to import: {e}")