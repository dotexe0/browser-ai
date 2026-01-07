#!/usr/bin/env python3
"""Test what the service actually returns"""

import subprocess
import json
import struct

SERVICE_PATH = r"automation_service\build\bin\Release\automation_service.exe"

def send_message(process, message):
    """Send message via Native Messaging"""
    encoded = json.dumps(message).encode('utf-8')
    length = struct.pack('@I', len(encoded))
    
    process.stdin.write(length)
    process.stdin.write(encoded)
    process.stdin.flush()
    
    # Read response
    raw_length = process.stdout.read(4)
    if not raw_length:
        return None
        
    msg_length = struct.unpack('@I', raw_length)[0]
    response = process.stdout.read(msg_length)
    
    return json.loads(response.decode('utf-8'))

print("Starting service...")
process = subprocess.Popen(
    [SERVICE_PATH],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

try:
    # Test 1: Ping
    print("\n1. Testing ping...")
    response = send_message(process, {"action": "ping", "params": {}})
    print(f"   Response: {json.dumps(response, indent=2)[:200]}")
    
    # Test 2: Capabilities
    print("\n2. Testing capabilities...")
    response = send_message(process, {"action": "get_capabilities", "params": {}})
    print(f"   Response: {json.dumps(response, indent=2)[:300]}")
    
    # Test 3: Screen capture
    print("\n3. Testing screen capture...")
    response = send_message(process, {"action": "capture_screen", "params": {}})
    
    if response:
        print(f"   Success: {response.get('success')}")
        print(f"   Has screenshot: {'screenshot' in response}")
        if 'screenshot' in response:
            print(f"   Screenshot length: {len(response['screenshot'])} bytes")
        if 'error' in response:
            print(f"   Error: {response['error']}")
    else:
        print("   No response!")
    
    # Test 4: UI inspection
    print("\n4. Testing UI inspection...")
    response = send_message(process, {"action": "inspect_ui", "params": {}})
    
    if response:
        print(f"   Success: {response.get('success')}")
        print(f"   Has ui_tree: {'ui_tree' in response}")
        if 'ui_tree' in response:
            print(f"   UI tree: {json.dumps(response['ui_tree'], indent=2)[:300]}")
        if 'error' in response:
            print(f"   Error: {response['error']}")
    else:
        print("   No response!")
    
finally:
    process.terminate()
    process.wait()
    print("\nService stopped")

