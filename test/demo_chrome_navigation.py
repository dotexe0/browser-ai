#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo: Open Chrome and navigate to a website
Shows automation of complex applications with multiple steps
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import subprocess
import json
import struct
import time

SERVICE_PATH = r"..\automation_service\build\bin\Release\automation_service.exe"

def send_action(process, action):
    """Send action to automation service"""
    wrapped_action = {
        "action": "execute_action",
        "params": action
    }
    
    encoded = json.dumps(wrapped_action).encode('utf-8')
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
print("🌐 DEMO: Opening Chrome and Navigating to GitHub")
print("="*70)
print("\nThis will:")
print("  1. Open Google Chrome")
print("  2. Navigate to github.com")
print("  3. Search for 'browser-ai'")
print("\n" + "="*70)

input("\nPress Enter to continue (or Ctrl+C to cancel)...")

print("\n🚀 Starting automation service...")
process = subprocess.Popen(
    [SERVICE_PATH],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    bufsize=0
)
time.sleep(0.5)

try:
    print("\n🔹 Step 1: Opening Chrome...")
    actions = [
        {"action": "press_keys", "params": {"keys": ["LWin", "R"]}},
        {"action": "wait", "params": {"ms": 1000}},
        {"action": "type", "params": {"text": "chrome"}},
        {"action": "press_keys", "params": {"keys": ["enter"]}},
        {"action": "wait", "params": {"ms": 3000}},
    ]
    
    for action in actions:
        result = send_action(process, action)
        if result and result.get('success'):
            print(f"   ✅ {action['action']}")
    
    print("\n🔹 Step 2: Navigating to GitHub...")
    actions = [
        # Type GitHub URL
        {"action": "type", "params": {"text": "github.com"}},
        {"action": "press_keys", "params": {"keys": ["enter"]}},
        {"action": "wait", "params": {"ms": 3000}},
    ]
    
    for action in actions:
        result = send_action(process, action)
        if result and result.get('success'):
            print(f"   ✅ {action['action']}")
    
    print("\n🔹 Step 3: Searching for 'browser-ai'...")
    actions = [
        # Press / to focus search (GitHub shortcut)
        {"action": "press_keys", "params": {"keys": ["/"]}},
        {"action": "wait", "params": {"ms": 500}},
        
        # Type search query
        {"action": "type", "params": {"text": "browser-ai"}},
        {"action": "wait", "params": {"ms": 500}},
    ]
    
    for action in actions:
        result = send_action(process, action)
        if result and result.get('success'):
            print(f"   ✅ {action['action']}")
    
    print("\n" + "="*70)
    print("✅ COMPLEX AUTOMATION COMPLETE!")
    print("="*70)
    print("\nWhat we just did:")
    print("  ✅ Opened Chrome")
    print("  ✅ Navigated to a website")
    print("  ✅ Used keyboard shortcuts")
    print("  ✅ Performed a search")
    print("\n💡 You can automate:")
    print("   - Web browsing and form filling")
    print("   - Social media posting")
    print("   - Email automation")
    print("   - Data entry tasks")
    print("   - Literally anything you do manually!")
    
finally:
    print("\n🔹 Stopping automation service...")
    process.terminate()
    time.sleep(0.5)

print("\n✅ Demo complete!")

