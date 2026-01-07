#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full end-to-end AI automation test
Tests: Backend AI → Action formatting → Automation service execution
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import subprocess
import json
import struct
import time
import requests
import base64
from PIL import Image
import io

SERVICE_PATH = r"automation_service\build\bin\Release\automation_service.exe"
BACKEND_URL = "http://localhost:5000"

def send_action(process, action):
    """Send a single action to the automation service"""
    # Wrap the AI action in the format the service expects
    wrapped_action = {
        "action": "execute_action",
        "params": action  # The AI action becomes the params
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

def create_dummy_screenshot():
    """Create a small dummy screenshot as base64"""
    img = Image.new('RGB', (100, 100), color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

print("\n" + "="*70)
print("🤖 FULL AI AUTOMATION TEST")
print("="*70)

# Step 1: Check backend is running
print("\n🔹 Step 1: Checking backend...")
try:
    response = requests.get(f"{BACKEND_URL}/api/health", timeout=2)
    print(f"   ✅ Backend is running")
    health = response.json()
    print(f"   Available providers: {', '.join(health['providers'])}")
except requests.exceptions.RequestException as e:
    print(f"   ❌ Backend not running. Start it with: cd backend && python server.py")
    sys.exit(1)

# Step 2: Get AI to generate actions
print("\n🔹 Step 2: Asking AI to generate actions...")
print("   Task: 'Open Notepad and type Hello from AI!'")

screenshot_b64 = create_dummy_screenshot()
ui_tree = {"elements": []}  # Simplified for this test

try:
    response = requests.post(
        f"{BACKEND_URL}/api/get-actions",
        json={
            "provider": "ollama",  # Use Ollama (local, no API key needed)
            "screenshot": screenshot_b64,
            "ui_tree": ui_tree,
            "user_request": "Open Notepad and type 'Hello from AI!'",
            "conversation_history": []
        },
        timeout=60
    )
    
    if response.status_code != 200:
        print(f"   ❌ AI request failed: {response.text}")
        sys.exit(1)
    
    result = response.json()
    if 'error' in result:
        print(f"   ❌ AI error: {result['error']}")
        sys.exit(1)
    
    actions = result.get('actions', [])
    
    # Handle case where actions might be a string (malformed AI response)
    if isinstance(actions, str):
        print(f"   ⚠️ AI returned string instead of array, attempting to parse...")
        try:
            actions = json.loads(actions)
        except:
            print(f"   ❌ Could not parse AI response: {actions[:100]}")
            sys.exit(1)
    
    # Ensure actions is a list
    if not isinstance(actions, list):
        actions = [actions]
    
    print(f"   ✅ AI generated {len(actions)} actions:")
    for i, action in enumerate(actions, 1):
        if isinstance(action, dict):
            action_type = action.get('action', 'unknown')
            print(f"      {i}. {action_type}")
            if action_type == 'type':
                text_preview = action.get('params', {}).get('text', '')[:30]
                print(f"         Text: '{text_preview}...'")
        else:
            print(f"      {i}. Invalid action format: {type(action)}")
    
except requests.exceptions.RequestException as e:
    print(f"   ❌ Request failed: {e}")
    sys.exit(1)

# Step 3: Execute AI actions with automation service
print("\n🔹 Step 3: Executing AI actions with automation service...")
print("   Starting automation service...")

process = subprocess.Popen(
    [SERVICE_PATH],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    bufsize=0
)
time.sleep(0.5)

try:
    success_count = 0
    fail_count = 0
    
    for i, action in enumerate(actions, 1):
        if not isinstance(action, dict):
            print(f"\n   Action {i}/{len(actions)}: SKIPPED (invalid format)")
            fail_count += 1
            continue
        
        action_type = action.get('action', 'unknown')
        print(f"\n   Action {i}/{len(actions)}: {action_type}")
        
        result = send_action(process, action)
        
        if result and result.get('success'):
            print(f"      ✅ Success")
            success_count += 1
            time.sleep(0.5)  # Small delay between actions
        else:
            error = result.get('error', 'Unknown error') if result else 'No response'
            print(f"      ❌ Failed: {error}")
            fail_count += 1
    
    print("\n" + "="*70)
    print(f"✅ EXECUTION COMPLETE!")
    print("="*70)
    print(f"   Successful actions: {success_count}/{len(actions)}")
    print(f"   Failed actions: {fail_count}/{len(actions)}")
    
    if success_count > 0:
        print("\n🎉 AI → Automation pipeline is WORKING!")
        print("   Check your screen - did Notepad open and text get typed?")
    
finally:
    print("\n🔹 Stopping automation service...")
    process.terminate()
    time.sleep(0.5)

print("\n✅ Test complete!")

