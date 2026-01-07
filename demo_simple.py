#!/usr/bin/env python3
"""
SIMPLE AUTOMATION DEMO (No AI)

This opens Notepad and types text.
No AI involved - just pure automation to prove it works!
"""

import subprocess
import json
import struct
import time

SERVICE_PATH = r"automation_service\build\bin\Release\automation_service.exe"

def send_action(process, action):
    """Send action to service"""
    encoded = json.dumps(action).encode('utf-8')
    length = struct.pack('@I', len(encoded))
    
    process.stdin.write(length)
    process.stdin.write(encoded)
    process.stdin.flush()
    
    raw_length = process.stdout.read(4)
    if not raw_length:
        return None
    
    msg_length = struct.unpack('@I', raw_length)[0]
    response = process.stdout.read(msg_length)
    
    return json.loads(response.decode('utf-8'))

print("=" * 70)
print("SIMPLE AUTOMATION DEMO")
print("=" * 70)
print()
print("This will open Notepad and type text.")
print("Watch your screen!")
print()

input("Press Enter to start... ")
print()

# Start service
print("[1/4] Starting automation service...")
process = subprocess.Popen(
    [SERVICE_PATH],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
print("[OK] Service started")
print()

try:
    # Open Run dialog
    print("[2/4] Opening Run dialog (Win+R)...")
    result = send_action(process, {
        "action": "execute_action",
        "params": {
            "action": "press_keys",
            "params": {"keys": ["LWin", "R"]}
        }
    })
    print(f"      Result: {result.get('success', False)}")
    if not result.get('success'):
        print(f"      Error: {result.get('error', 'unknown')}")
    time.sleep(0.8)
    
    # Type "notepad"
    print("[3/4] Typing 'notepad'...")
    result = send_action(process, {
        "action": "execute_action",
        "params": {
            "action": "type",
            "params": {"text": "notepad"}
        }
    })
    print(f"      Result: {result.get('success', False)}")
    time.sleep(0.5)
    
    # Press Enter
    print("      Pressing Enter...")
    result = send_action(process, {
        "action": "execute_action",
        "params": {
            "action": "press_keys",
            "params": {"keys": ["Return"]}
        }
    })
    print(f"      Result: {result.get('success', False)}")
    time.sleep(2.0)  # Wait for Notepad to open
    
    # Type message
    print("[4/4] Typing message...")
    message = """Hello from Browser AI!

This text was typed by the automation service.

No AI involved - just testing that automation works!

Layer 2 (Automation Service) is WORKING!"""
    
    result = send_action(process, {
        "action": "execute_action",
        "params": {
            "action": "type",
            "params": {"text": message}
        }
    })
    print(f"      Result: {result.get('success', False)}")
    
    print()
    print("=" * 70)
    print("DONE! Check Notepad!")
    print("=" * 70)
    print()
    print("If you see the text in Notepad, automation is working!")
    print()

except KeyboardInterrupt:
    print("\n[STOP] Interrupted")
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
finally:
    print("Stopping service...")
    process.terminate()
    process.wait()
    print("[OK] Done")
    print()

input("Press Enter to close... ")

