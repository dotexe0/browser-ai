#!/usr/bin/env python3
"""Quick test to check if Ollama is running and has models"""

import requests
import json

print("=" * 60)
print("Testing Ollama Connection")
print("=" * 60)
print()

# Test 1: Check if Ollama is running
print("1. Checking if Ollama is running...")
try:
    response = requests.get('http://localhost:11434/api/tags', timeout=2)
    print("   ✅ Ollama is running!")
    print()
    
    # Test 2: Check installed models
    print("2. Checking installed models...")
    data = response.json()
    models = data.get('models', [])
    
    if not models:
        print("   ❌ No models installed!")
        print()
        print("   Install a vision model:")
        print("   ollama pull llava")
        print()
    else:
        print(f"   ✅ Found {len(models)} model(s):")
        for model in models:
            name = model.get('name', 'unknown')
            size = model.get('size', 0)
            size_gb = size / (1024**3)
            print(f"      - {name} ({size_gb:.1f} GB)")
        print()
        
        # Test 3: Check for vision models
        print("3. Checking for vision models...")
        has_vision = any('llava' in m.get('name', '').lower() or 
                        'bakllava' in m.get('name', '').lower()
                        for m in models)
        
        if has_vision:
            print("   ✅ Vision model found! Ready to use.")
        else:
            print("   ⚠️  No vision model found.")
            print("   Install one:")
            print("   ollama pull llava")
        print()
    
    print("=" * 60)
    if models and any('llava' in m.get('name', '').lower() for m in models):
        print("🎉 Ollama is ready!")
        print()
        print("Next step: Start the backend server")
        print("   cd backend")
        print("   python server.py")
    else:
        print("⚠️  Ollama needs a vision model")
        print()
        print("Run: ollama pull llava")
    print("=" * 60)
    
except requests.exceptions.ConnectionError:
    print("   ❌ Cannot connect to Ollama!")
    print()
    print("=" * 60)
    print("🔧 Ollama is not running")
    print("=" * 60)
    print()
    print("Fix:")
    print("1. Open a NEW terminal window")
    print("2. Run: ollama serve")
    print("3. Leave it running in the background")
    print()
    print("OR")
    print()
    print("Start the Ollama desktop app from Start Menu")
    print("=" * 60)
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    print()

