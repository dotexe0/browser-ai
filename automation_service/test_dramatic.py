#!/usr/bin/env python3
"""Dramatic automation test - impossible to miss!"""
import sys
import struct
import json
import subprocess
import time

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
    print("🎬 DRAMATIC AUTOMATION TEST")
    print("=" * 70)
    print()
    print("This test will:")
    print("  1. Open Windows Run dialog (Win+R)")
    print("  2. Type 'notepad'")
    print("  3. Press Enter")
    print("  4. Type 'Hello from AI automation!' in Notepad")
    print()
    print("WATCH YOUR SCREEN CAREFULLY!")
    print()
    input("Press ENTER when ready...")
    print()
    
    steps = [
        {
            "name": "Step 1: Open Run dialog (Win+R)",
            "message": {
                "action": "execute_action",
                "params": {
                    "action": "press_keys",
                    "params": {"keys": ["LWin", "R"]}
                }
            },
            "wait": 1
        },
        {
            "name": "Step 2: Type 'notepad'",
            "message": {
                "action": "execute_action",
                "params": {
                    "action": "type",
                    "params": {"text": "notepad"}
                }
            },
            "wait": 0.5
        },
        {
            "name": "Step 3: Press Enter",
            "message": {
                "action": "execute_action",
                "params": {
                    "action": "press_keys",
                    "params": {"keys": ["Return"]}
                }
            },
            "wait": 1.5
        },
        {
            "name": "Step 4: Type message in Notepad",
            "message": {
                "action": "execute_action",
                "params": {
                    "action": "type",
                    "params": {"text": "Hello from AI automation!\n\nThis message was typed by the automation service!\n\nLayer 2 is WORKING! 🎉"}
                }
            },
            "wait": 0.5
        }
    ]
    
    for i, step in enumerate(steps, 1):
        print(f"[{i}/{len(steps)}] {step['name']}")
        response = test_action(service_exe, step['message'])
        
        if response.get('success'):
            print(f"     ✓ Success!")
        else:
            print(f"     ✗ Failed: {response.get('error', 'Unknown')}")
            print()
            print("Stopping test due to error.")
            break
        
        time.sleep(step['wait'])
        print()
    
    print()
    print("=" * 70)
    print("🎬 TEST COMPLETE!")
    print("=" * 70)
    print()
    print("If you see Notepad with the message, Layer 2 is 100% working!")
    print()

