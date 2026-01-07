#!/usr/bin/env python3
"""Test mouse movement via click action"""
import sys
import struct
import json
import subprocess
import time

def send_message(message):
    """Send a message using Chrome Native Messaging protocol"""
    encoded_message = json.dumps(message).encode('utf-8')
    message_length = len(encoded_message)
    length_bytes = struct.pack('@I', message_length)
    return length_bytes + encoded_message

def read_message(input_stream):
    """Read a message from Native Messaging protocol"""
    raw_length = input_stream.read(4)
    if len(raw_length) == 0:
        return None
    message_length = struct.unpack('@I', raw_length)[0]
    message = input_stream.read(message_length).decode('utf-8')
    return json.loads(message)

def test_service(service_exe, message):
    """Test the service with a message"""
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
    stderr = process.stderr.read().decode('utf-8')
    process.wait()
    
    return response, stderr

if __name__ == '__main__':
    service_exe = r'A:\browser-ai\automation_service\build\bin\Release\automation_service.exe'
    
    print("=" * 70)
    print("Testing Mouse Movement via Click Action")
    print("=" * 70)
    print()
    
    # Test: Click action (which moves mouse then clicks)
    print("Test: Click at position (100, 100)")
    print("-" * 70)
    print()
    print("WATCH YOUR MOUSE - It should move to top-left area of screen!")
    print("Executing in 2 seconds...")
    time.sleep(2)
    
    message = {
        "action": "execute_action",
        "params": {
            "action": "click",
            "params": {
                "x": 100,
                "y": 100,
                "button": "left"
            }
        }
    }
    
    print(f"Sending: {json.dumps(message, indent=2)}")
    print()
    
    response, logs = test_service(service_exe, message)
    
    print("Response:")
    print(json.dumps(response, indent=2))
    print()
    
    if response.get('success'):
        print("[OK] Mouse should have moved to (100, 100) and clicked!")
        print()
        print("Did your mouse move? If yes, Layer 2 automation is WORKING!")
    else:
        print(f"[FAIL] Error: {response.get('error', 'Unknown error')}")
        print()
        print("This might need elevated permissions.")
        print("Try running terminal as Administrator.")
    
    print()
    print("=" * 70)
    print()
    
    # Test 2: Type text (should work)
    print("Test 2: Press Windows key (opens Start menu)")
    print("-" * 70)
    print()
    print("WATCH YOUR SCREEN - Start menu should open!")
    print("Executing in 2 seconds...")
    time.sleep(2)
    
    message = {
        "action": "execute_action",
        "params": {
            "action": "press_keys",
            "params": {
                "keys": ["LWin"]
            }
        }
    }
    
    print(f"Sending: press Windows key")
    print()
    
    response, logs = test_service(service_exe, message)
    
    print("Response:")
    print(json.dumps(response, indent=2))
    print()
    
    if response.get('success'):
        print("[OK] Windows key pressed! Did Start menu open?")
    else:
        print(f"[FAIL] Error: {response.get('error', 'Unknown error')}")
    
    print()
    print("=" * 70)
    print("Tests complete!")
    print("=" * 70)

