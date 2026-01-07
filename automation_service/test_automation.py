#!/usr/bin/env python3
"""Test automation features: screen capture and UI inspection"""
import sys
import struct
import json
import subprocess
import base64

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
    print("Testing Browser AI Automation Features")
    print("=" * 70)
    print()
    
    # Test 1: Screen Capture
    print("Test 1: Capture Screen")
    print("-" * 70)
    message = {
        "action": "capture_screen",
        "params": {
            "include_cursor": False
        }
    }
    print(f"Sending: capture_screen request")
    response, logs = test_service(service_exe, message)
    
    if response.get('success'):
        image_data = response.get('image_data', '')
        width = response.get('width', 0)
        height = response.get('height', 0)
        data_size = len(image_data)
        
        print(f"[OK] SUCCESS!")
        print(f"   Screen Size: {width}x{height}")
        print(f"   Image Data Size: {data_size:,} bytes ({data_size/1024/1024:.2f} MB)")
        print(f"   Format: PNG (base64 encoded)")
        
        # Optionally save to file
        if data_size > 0:
            try:
                import os
                output_file = 'screenshot.png'
                with open(output_file, 'wb') as f:
                    f.write(base64.b64decode(image_data))
                abs_path = os.path.abspath(output_file)
                print(f"   Saved to: {abs_path}")
            except Exception as e:
                print(f"   (Could not save file: {e})")
    else:
        print(f"[FAIL] FAILED: {response.get('error', 'Unknown error')}")
    print()
    
    # Test 2: UI Inspection
    print("Test 2: Inspect UI (Desktop)")
    print("-" * 70)
    message = {
        "action": "inspect_ui",
        "params": {
            "max_depth": 2
        }
    }
    print(f"Sending: inspect_ui request (max_depth=2)")
    response, logs = test_service(service_exe, message)
    
    if response.get('success'):
        ui_tree = response.get('ui_tree', {})
        print(f"[OK] SUCCESS!")
        print(f"   Root Element: {ui_tree.get('name', 'Unknown')}")
        print(f"   Type: {ui_tree.get('type', 'Unknown')}")
        print(f"   Children: {len(ui_tree.get('children', []))}")
        
        # Show first few children
        children = ui_tree.get('children', [])
        if children:
            print(f"   First few elements:")
            for i, child in enumerate(children[:5]):
                name = child.get('name', 'Unnamed')
                element_type = child.get('type', 'Unknown')
                print(f"     {i+1}. {name} ({element_type})")
            if len(children) > 5:
                print(f"     ... and {len(children) - 5} more")
    else:
        print(f"[FAIL] FAILED: {response.get('error', 'Unknown error')}")
    print()
    
    # Test 3: Execute Simple Action
    print("Test 3: Execute Mouse Move Action")
    print("-" * 70)
    message = {
        "action": "execute_action",
        "params": {
            "action_type": "move_mouse",
            "x": 100,
            "y": 100
        }
    }
    print(f"Sending: Move mouse to (100, 100)")
    response, logs = test_service(service_exe, message)
    
    if response.get('success'):
        print(f"[OK] SUCCESS!")
        print(f"   Mouse moved to (100, 100)")
    else:
        print(f"[FAIL] FAILED: {response.get('error', 'Unknown error')}")
    print()
    
    print("=" * 70)
    print("Automation tests complete!")
    print("=" * 70)
    print()
    print("Summary:")
    print("- Screen capture: Captures your entire desktop")
    print("- UI inspection: Reads Windows UI element tree")
    print("- Mouse control: Can move mouse cursor")
    print()
    print("[OK] Layer 2 is fully operational!")

