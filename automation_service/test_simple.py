#!/usr/bin/env python3
"""Simple automation test - verifies typing and keypresses work"""
import sys
import struct
import json
import subprocess
import time
import os

def send_message(message):
    encoded_message = json.dumps(message).encode('utf-8')
    message_length = len(encoded_message)
    length_bytes = struct.pack('@I', message_length)
    return length_bytes + encoded_message

def read_message(input_stream):
    raw_length = input_stream.read(4)
    if len(raw_length) == 0:
        return None
    message_length = struct.unpack('@I', raw_length)[0]
    message = input_stream.read(message_length).decode('utf-8')
    return json.loads(message)

def test_action(service_exe, message):
    process = subprocess.Popen(
        [service_exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    encoded = send_message(message)
    process.stdin.write(encoded)
    process.stdin.flush()
    process.stdin.close()
    
    response = read_message(process.stdout)
    process.wait()
    return response

if __name__ == '__main__':
    service_exe = r'A:\browser-ai\automation_service\build\bin\Release\automation_service.exe'
    
    print("=" * 70)
    print("SIMPLE AUTOMATION TEST")
    print("=" * 70)
    print()
    print("This test will:")
    print("  1. Open Notepad using Windows start command")
    print("  2. Wait for you to see Notepad")
    print("  3. Type a message into Notepad")
    print()
    print("INSTRUCTIONS:")
    print("  - First, we'll open Notepad via command line")
    print("  - You'll see a new Notepad window appear")
    print("  - The script will wait 3 seconds")
    print("  - Then it will type a message into Notepad")
    print()
    
    # Open Notepad directly via subprocess (not via automation)
    print("Opening Notepad...")
    notepad_process = subprocess.Popen(['notepad.exe'])
    print("[OK] Notepad opened!")
    print()
    
    print("Waiting 3 seconds for Notepad to be ready...")
    time.sleep(3)
    print()
    
    print("Now testing automation:")
    print()
    
    # Test 1: Type text
    print("[1/2] Typing message into active window (should be Notepad)...")
    
    message = {
        "action": "execute_action",
        "params": {
            "action": "type",
            "params": {
                "text": "Hello from AI Automation!\n\nIf you can read this in Notepad, the automation service is WORKING!\n\nLayer 2 automation verified! [OK]"
            }
        }
    }
    
    response = test_action(service_exe, message)
    
    if response.get('success'):
        print("     [OK] Text sent successfully!")
        print()
        print("=" * 70)
        print("CHECK NOTEPAD WINDOW!")
        print("=" * 70)
        print()
        print("If you see the message in Notepad:")
        print("  [OK] Typing works")
        print("  [OK] Automation service is functional")
        print("  [OK] Layer 2 is WORKING!")
        print()
    else:
        print(f"     ✗ Failed: {response.get('error', 'Unknown')}")
        print()
    
    # Test 2: Press a key
    print("[2/2] Testing key press (Ctrl+A to select all)...")
    time.sleep(1)
    
    message = {
        "action": "execute_action",
        "params": {
            "action": "press_keys",
            "params": {
                "keys": ["LControl", "A"]
            }
        }
    }
    
    response = test_action(service_exe, message)
    
    if response.get('success'):
        print("     [OK] Key combination sent (text should be selected in Notepad)!")
    else:
        print(f"     ✗ Failed: {response.get('error', 'Unknown')}")
    
    print()
    print("=" * 70)
    print("TEST COMPLETE!")
    print("=" * 70)
    print()
    print("Look at Notepad:")
    print("  - Did text appear? -> Typing works [OK]")
    print("  - Is text selected (highlighted)? -> Key combos work [OK]")
    print()
    print("If both work, your automation service is fully functional!")
    print()
    
    input("Press ENTER to close Notepad and exit...")
    
    try:
        notepad_process.terminate()
    except:
        pass

