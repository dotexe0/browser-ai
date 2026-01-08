#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Show exactly what Ollama generates without filtering
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

def create_dummy_screenshot():
    img = Image.new('RGB', (100, 100), color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

print("\n" + "="*70)
print("🔍 WHAT DOES OLLAMA ACTUALLY GENERATE?")
print("="*70)

# Open Notepad first
print("\n🔹 Opening Notepad...")
process = subprocess.Popen(
    [SERVICE_PATH],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    bufsize=0
)
time.sleep(0.5)

try:
    # Open Notepad
    actions = [
        {"action": "press_keys", "params": {"keys": ["LWin", "R"]}},
        {"action": "wait", "params": {"ms": 1000}},
        {"action": "type", "params": {"text": "notepad"}},
        {"action": "press_keys", "params": {"keys": ["enter"]}},
        {"action": "wait", "params": {"ms": 2000}}
    ]
    
    for action in actions:
        send_action(process, action)
    
    print("   ✅ Notepad opened")
    
    # Ask Ollama
    print("\n🔹 Asking Ollama to generate actions...")
    
    simple_prompt = """Type this message in Notepad:

"This is from Ollama AI!"

Return ONLY JSON array:
[{"action": "type", "params": {"text": "your message here"}}]"""
    
    response = requests.post(
        f"{BACKEND_URL}/api/get-actions",
        json={
            "provider": "ollama",
            "screenshot": create_dummy_screenshot(),
            "ui_tree": {},
            "user_request": simple_prompt,
            "conversation_history": []
        },
        timeout=60
    )
    
    result = response.json()
    
    print("\n📋 FULL OLLAMA RESPONSE:")
    print(json.dumps(result, indent=2))
    
    if 'error' in result:
        print(f"\n❌ Error: {result['error']}")
    elif 'actions' in result:
        ai_actions = result['actions']
        
        print(f"\n✅ Generated {len(ai_actions)} actions:")
        for i, action in enumerate(ai_actions, 1):
            print(f"\n  Action {i}:")
            print(f"    Type: {action.get('action', 'MISSING')}")
            print(f"    Params: {action.get('params', 'MISSING')}")
            
            # Check if it's a valid type action
            is_type = action.get('action') == 'type'
            has_params = 'params' in action
            has_text = has_params and 'text' in action['params']
            
            print(f"    ✓ Is 'type': {is_type}")
            print(f"    ✓ Has 'params': {has_params}")
            print(f"    ✓ Has 'text': {has_text}")
            
            if is_type and has_text:
                print(f"    ✅ VALID - Will be executed")
                # Execute it
                result = send_action(process, action)
                print(f"    Execution: {'✅ Success' if result.get('success') else '❌ Failed'}")
            else:
                print(f"    ❌ INVALID - Will be filtered out")
    
    print("\n" + "="*70)
    print("Check Notepad - did AI-generated text appear?")
    print("="*70)
    
finally:
    print("\n🔹 Stopping service...")
    process.terminate()

print("\n✅ Done!")

