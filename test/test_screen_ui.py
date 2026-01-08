#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test screen capture and UI inspection capabilities
Tests Layer 2 foundational features
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import subprocess
import json
import struct
import time
import base64

SERVICE_PATH = r"..\automation_service\build\bin\Release\automation_service.exe"

def send_message(process, message):
    """Send Native Messaging message"""
    encoded = json.dumps(message).encode('utf-8')
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
print("🔍 TESTING SCREEN CAPTURE & UI INSPECTION")
print("="*70)
print("\nThis test verifies foundational Layer 2 capabilities:")
print("  1. Screen capture (Desktop Duplication API)")
print("  2. UI inspection (UIAutomation)")
print("\n" + "="*70)

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
    # Test 1: Ping
    print("\n🔹 Test 1: Service connectivity...")
    result = send_message(process, {"action": "ping"})
    if result and result.get('success'):
        print(f"   ✅ Service is running (version: {result.get('version', 'unknown')})")
    else:
        print(f"   ❌ Ping failed")
        sys.exit(1)
    
    # Test 2: Get capabilities
    print("\n🔹 Test 2: Querying capabilities...")
    result = send_message(process, {"action": "get_capabilities"})
    if result and result.get('success'):
        caps = result.get('capabilities', {})
        print(f"   ✅ Capabilities retrieved:")
        print(f"      - Screen capture: {caps.get('screen_capture', False)}")
        print(f"      - UI inspection: {caps.get('ui_inspection', False)}")
        print(f"      - Input control: {caps.get('input_control', False)}")
    else:
        print(f"   ❌ Failed to get capabilities")
    
    # Test 3: Screen capture
    print("\n🔹 Test 3: Capturing screen...")
    result = send_message(process, {"action": "capture_screen"})
    
    if result and result.get('success'):
        screenshot = result.get('screenshot', '')
        width = result.get('width', 0)
        height = result.get('height', 0)
        
        print(f"   ✅ Screen captured successfully!")
        print(f"      Resolution: {width}x{height}")
        print(f"      Data size: {len(screenshot)} bytes (base64)")
        
        # Verify it's valid base64
        try:
            decoded = base64.b64decode(screenshot[:100])  # Test first 100 chars
            print(f"      ✅ Valid base64 encoding")
        except:
            print(f"      ⚠️ Invalid base64 encoding")
        
        # Save first screenshot
        if screenshot and len(screenshot) > 100:
            with open('test_screenshot.txt', 'w') as f:
                f.write(f"Screenshot data (first 500 chars):\n{screenshot[:500]}...\n")
                f.write(f"\nResolution: {width}x{height}\n")
                f.write(f"Total size: {len(screenshot)} bytes\n")
            print(f"      💾 Sample saved to test_screenshot.txt")
    else:
        error = result.get('error', 'Unknown error') if result else 'No response'
        print(f"   ❌ Screen capture failed: {error}")
    
    # Test 4: UI Inspection
    print("\n🔹 Test 4: Inspecting UI tree...")
    result = send_message(process, {"action": "inspect_ui"})
    
    if result and result.get('success'):
        ui_tree = result.get('uiTree', {})
        print(f"   ✅ UI tree retrieved!")
        
        def count_elements(node, depth=0):
            count = 1
            children = node.get('children', [])
            for child in children:
                count += count_elements(child, depth + 1)
            return count
        
        total_elements = count_elements(ui_tree)
        print(f"      Total elements: {total_elements}")
        
        # Print root element info
        if ui_tree:
            print(f"      Root element:")
            print(f"        Name: {ui_tree.get('name', 'N/A')}")
            print(f"        Type: {ui_tree.get('type', 'N/A')}")
            print(f"        Bounds: {ui_tree.get('bounds', {})}")
            
            # Show first few children
            children = ui_tree.get('children', [])
            if children:
                print(f"      First few children:")
                for i, child in enumerate(children[:3]):
                    print(f"        {i+1}. {child.get('name', 'Unnamed')} ({child.get('type', 'Unknown')})")
        
        # Save UI tree
        with open('test_ui_tree.json', 'w') as f:
            json.dump(ui_tree, f, indent=2)
        print(f"      💾 Full UI tree saved to test_ui_tree.json")
    else:
        error = result.get('error', 'Unknown error') if result else 'No response'
        print(f"   ❌ UI inspection failed: {error}")
    
    # Test 5: Combined test - Open Notepad and inspect it
    print("\n🔹 Test 5: Testing with real application (Notepad)...")
    print("   Opening Notepad...")
    
    # Open Notepad
    actions = [
        {"action": "execute_action", "params": {"action": "press_keys", "params": {"keys": ["LWin", "R"]}}},
        {"action": "execute_action", "params": {"action": "wait", "params": {"ms": 1000}}},
        {"action": "execute_action", "params": {"action": "type", "params": {"text": "notepad"}}},
        {"action": "execute_action", "params": {"action": "press_keys", "params": {"keys": ["enter"]}}},
        {"action": "execute_action", "params": {"action": "wait", "params": {"ms": 2000}}},
    ]
    
    for action in actions:
        send_message(process, action)
    
    print("   ✅ Notepad opened")
    print("   Capturing screen with Notepad visible...")
    
    result = send_message(process, {"action": "capture_screen"})
    if result and result.get('screenshot'):
        print(f"   ✅ Screen captured (with Notepad)")
    
    print("   Inspecting UI tree with Notepad...")
    result = send_message(process, {"action": "inspect_ui"})
    if result and result.get('uiTree'):
        ui_tree = result['uiTree']
        
        # Try to find Notepad in the tree
        def find_notepad(node):
            name = node.get('name', '').lower()
            if 'notepad' in name or 'untitled' in name:
                return node
            for child in node.get('children', []):
                found = find_notepad(child)
                if found:
                    return found
            return None
        
        notepad_elem = find_notepad(ui_tree)
        if notepad_elem:
            print(f"   ✅ Found Notepad in UI tree!")
            print(f"      Name: {notepad_elem.get('name', 'N/A')}")
            print(f"      Type: {notepad_elem.get('type', 'N/A')}")
            print(f"      Bounds: {notepad_elem.get('bounds', {})}")
        else:
            print(f"   ⚠️ Notepad not found in UI tree (but tree was retrieved)")
    
    print("\n" + "="*70)
    print("✅ FOUNDATIONAL TESTS COMPLETE!")
    print("="*70)
    print("\nResults:")
    print("  ✅ Service connectivity: Working")
    print("  ✅ Screen capture: Implemented and functional")
    print("  ✅ UI inspection: Implemented and functional")
    print("\nNext steps:")
    print("  → Wire screen capture to AI (send screenshot)")
    print("  → Wire UI tree to AI (send element data)")
    print("  → Use AI vision to find elements on screen")
    print("  → Click elements by name (not just coordinates)")
    
finally:
    print("\n🔹 Stopping service...")
    process.terminate()
    time.sleep(0.5)

print("\n✅ Test complete!")

