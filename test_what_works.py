#!/usr/bin/env python3
"""Test what actions the service actually supports"""

import subprocess
import json
import struct

SERVICE_PATH = r"automation_service\build\bin\Release\automation_service.exe"

def send_action(process, action):
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

print("Testing service actions...")
process = subprocess.Popen(
    [SERVICE_PATH],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

try:
    # Test 1: Get capabilities
    print("\n1. Capabilities:")
    result = send_action(process, {"action": "get_capabilities", "params": {}})
    print(json.dumps(result, indent=2))
    
    # Test 2: Try press_key (singular)
    print("\n2. Testing 'press_key' (singular):")
    result = send_action(process, {
        "action": "press_key",
        "params": {"key": "A"}
    })
    print(json.dumps(result, indent=2))
    
    # Test 3: Try press_keys (plural)
    print("\n3. Testing 'press_keys' (plural):")
    result = send_action(process, {
        "action": "press_keys",
        "params": {"keys": ["LWin", "R"]}
    })
    print(json.dumps(result, indent=2))
    
    # Test 4: Try click
    print("\n4. Testing 'click':")
    result = send_action(process, {
        "action": "click",
        "params": {"x": 100, "y": 100}
    })
    print(json.dumps(result, indent=2))
    
    # Test 5: Try type
    print("\n5. Testing 'type':")
    result = send_action(process, {
        "action": "type",
        "params": {"text": "test"}
    })
    print(json.dumps(result, indent=2))
    
finally:
    process.terminate()
    process.wait()

print("\n[DONE]")

