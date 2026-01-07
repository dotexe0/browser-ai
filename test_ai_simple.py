#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple AI test: Opens Notepad, then asks AI to type a message
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
    """Create a small dummy screenshot"""
    img = Image.new('RGB', (100, 100), color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

print("\n" + "="*70)
print("🤖 AI-ASSISTED TYPING TEST")
print("="*70)
print("\nThis test will:")
print("  1. Open Notepad (using proven automation)")
print("  2. Ask AI to generate typing actions")
print("  3. Execute AI's typing commands")
print()

# Start automation service
print("🔹 Starting automation service...")
process = subprocess.Popen(
    [SERVICE_PATH],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    bufsize=0
)
time.sleep(0.5)

try:
    # Step 1: Open Notepad using our proven automation
    print("\n🔹 Step 1: Opening Notepad (proven automation)...")
    
    actions = [
        {"action": "press_keys", "params": {"keys": ["LWin", "R"]}},
        {"action": "wait", "params": {"ms": 1000}},
        {"action": "type", "params": {"text": "notepad"}},
        {"action": "press_keys", "params": {"keys": ["enter"]}},
        {"action": "wait", "params": {"ms": 2000}}
    ]
    
    for action in actions:
        send_action(process, action)
    
    print("   ✅ Notepad should be open now")
    
    # Step 2: Ask AI to generate a typing message
    print("\n🔹 Step 2: Asking AI to write a message...")
    
    # Simple request that doesn't require screen analysis
    simple_prompt = """Generate a JSON array with ONE action to type this message in Notepad:

"Hello! This message was written by AI.
The automation system is working!"

Return ONLY this format:
[{"action": "type", "params": {"text": "your message here"}}]"""
    
    try:
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
        
        if response.status_code != 200:
            print(f"   ❌ AI request failed: {response.text}")
            raise Exception("AI request failed")
        
        result = response.json()
        if 'error' in result:
            print(f"   ⚠️ AI error: {result['error']}")
            print("   Using fallback message instead...")
            ai_actions = [{
                "action": "type",
                "params": {
                    "text": "Hello! This message was written by AI.\nThe automation system is working!"
                }
            }]
        else:
            ai_actions = result.get('actions', [])
            
            # Parse if string
            if isinstance(ai_actions, str):
                try:
                    ai_actions = json.loads(ai_actions)
                except:
                    ai_actions = [{
                        "action": "type",
                        "params": {
                            "text": "Hello! This message was written by AI.\nThe automation system is working!"
                        }
                    }]
            
            if not isinstance(ai_actions, list):
                ai_actions = [ai_actions]
            
            # Filter to only typing actions with valid params
            ai_actions = [
                a for a in ai_actions 
                if isinstance(a, dict) and 
                   a.get('action') == 'type' and 
                   'params' in a and 
                   'text' in a['params']
            ]
            
            if not ai_actions:
                print("   ⚠️ AI didn't generate valid typing actions")
                print("   Using fallback message instead...")
                ai_actions = [{
                    "action": "type",
                    "params": {
                        "text": "Hello! This message was written by AI.\nThe automation system is working!"
                    }
                }]
        
        print(f"   ✅ Ready to type AI's message")
        
    except Exception as e:
        print(f"   ⚠️ AI unavailable: {e}")
        print("   Using fallback message instead...")
        ai_actions = [{
            "action": "type",
            "params": {
                "text": "Hello! This message was written by AI.\nThe automation system is working!"
            }
        }]
    
    # Step 3: Execute AI's typing actions
    print("\n🔹 Step 3: Executing AI's typing commands...")
    
    for i, action in enumerate(ai_actions, 1):
        print(f"   Typing action {i}/{len(ai_actions)}...")
        result = send_action(process, action)
        
        if result and result.get('success'):
            print(f"   ✅ Success")
        else:
            error = result.get('error', 'Unknown error') if result else 'No response'
            print(f"   ❌ Failed: {error}")
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETE!")
    print("="*70)
    print("\n🎉 Check Notepad - you should see the AI-generated message!")
    print("\nNote: If AI was unavailable, you'll see the fallback message.")
    
finally:
    print("\n🔹 Stopping automation service...")
    process.terminate()
    time.sleep(0.5)

print("\n✅ Test finished!")

