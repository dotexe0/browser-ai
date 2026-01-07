#!/usr/bin/env python3
"""Simple Ollama test"""

import requests
import json
import base64

print("Testing Ollama directly...")
print()

# Create a tiny test image (1x1 white pixel)
test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

payload = {
    'model': 'llava',
    'prompt': 'Describe this image briefly.',
    'images': [test_image_b64],
    'stream': False
}

print("Sending request to Ollama...")
print(f"Endpoint: http://localhost:11434/api/generate")
print(f"Model: llava")
print()

try:
    response = requests.post(
        'http://localhost:11434/api/generate',
        json=payload,
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Length: {len(response.text)} bytes")
    print()
    print("Response:")
    print(response.text[:500])  # First 500 chars
    print()
    
    if response.status_code == 200:
        data = response.json()
        if 'response' in data:
            print("[OK] Ollama is working!")
            print(f"AI Response: {data['response'][:200]}")
        else:
            print("[WARN] Unexpected response format")
            print(f"Keys: {list(data.keys())}")
    else:
        print(f"[FAIL] HTTP {response.status_code}")
        
except Exception as e:
    print(f"[ERROR] {e}")

