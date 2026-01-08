#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug what Ollama actually returns
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
import json
import base64
from PIL import Image
import io

BACKEND_URL = "http://localhost:5000"

def create_dummy_screenshot():
    """Create a small dummy screenshot"""
    img = Image.new('RGB', (100, 100), color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

print("\n" + "="*70)
print("🔍 OLLAMA DEBUG TEST")
print("="*70)

# Test with a very simple, direct request
simple_prompt = """Type this exact text: "AI is working!"

Return ONLY this JSON array:
[{"action": "type", "params": {"text": "AI is working!"}}]"""

print("\n📤 Sending request to Ollama...")
print(f"Prompt: {simple_prompt[:100]}...")

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
    
    print(f"\n📥 Response status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    result = response.json()
    
    print("\n📋 Full response JSON:")
    print(json.dumps(result, indent=2))
    
    if 'error' in result:
        print(f"\n❌ ERROR: {result['error']}")
    elif 'actions' in result:
        actions = result['actions']
        print(f"\n✅ Actions field found")
        print(f"Type: {type(actions)}")
        print(f"Value: {actions}")
        
        if isinstance(actions, str):
            print("\n⚠️ Actions is a STRING, not an array!")
            print(f"Raw string: {repr(actions)}")
            try:
                parsed = json.loads(actions)
                print(f"Parsed JSON: {parsed}")
            except Exception as e:
                print(f"Failed to parse: {e}")
        elif isinstance(actions, list):
            print(f"\n✅ Actions is a list with {len(actions)} items")
            for i, action in enumerate(actions):
                print(f"  {i}: {action}")
    else:
        print("\n⚠️ No 'actions' field in response")
    
except requests.exceptions.RequestException as e:
    print(f"\n❌ Request failed: {e}")
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Debug complete!")

