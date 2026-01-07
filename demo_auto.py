#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Non-interactive automation demo - opens Notepad and types text automatically
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import subprocess
import json
import struct
import time

SERVICE_PATH = r"automation_service\build\bin\Release\automation_service.exe"

def send_action(process, action):
    """Send a single action to the service"""
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

print("\n" + "="*70)
print("🤖 AUTOMATION DEMO - WATCH YOUR SCREEN! 🤖")
print("="*70)
print("\nStarting in 2 seconds...")
time.sleep(2)

print("✅ Starting automation service...")
process = subprocess.Popen(
    [SERVICE_PATH],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    bufsize=0
)
time.sleep(0.5)

try:
    print("\n🔹 Step 1: Opening Notepad...")
    print("   Pressing Win+R...")
    result = send_action(process, {
        "action": "execute_action",
        "params": {
            "action": "press_keys",
            "params": {"keys": ["LWin", "R"]}
        }
    })
    print(f"   Result: {'✅ OK' if result.get('success') else '❌ FAIL'}")
    time.sleep(1)
    
    print("\n🔹 Step 2: Typing 'notepad'...")
    result = send_action(process, {
        "action": "execute_action",
        "params": {
            "action": "type",
            "params": {"text": "notepad"}
        }
    })
    print(f"   Result: {'✅ OK' if result.get('success') else '❌ FAIL'}")
    time.sleep(0.5)
    
    print("\n🔹 Step 3: Pressing Enter...")
    result = send_action(process, {
        "action": "execute_action",
        "params": {
            "action": "press_keys",
            "params": {"keys": ["enter"]}
        }
    })
    print(f"   Result: {'✅ OK' if result.get('success') else '❌ FAIL'}")
    time.sleep(2)
    
    print("\n🔹 Step 4: Typing message in Notepad...")
    message = "Hello from BrowserAI!\n\nThis text was typed by the automation service.\n\nThe automation works!"
    result = send_action(process, {
        "action": "execute_action",
        "params": {
            "action": "type",
            "params": {"text": message}
        }
    })
    print(f"   Result: {'✅ OK' if result.get('success') else '❌ FAIL'}")
    
    print("\n" + "="*70)
    print("✅ DEMO COMPLETE!")
    print("="*70)
    print("\nCheck Notepad - you should see the typed message!")
    print("\nNote: If Notepad didn't open, the service may need elevated")
    print("      permissions to send keyboard input to Windows.")
    
finally:
    print("\n🔹 Stopping service...")
    process.terminate()
    time.sleep(0.5)

print("\n✅ Demo finished!")

