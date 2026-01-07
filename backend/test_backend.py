#!/usr/bin/env python3
"""
Test the backend proxy server

Tests all provider endpoints and functionality.
"""

import requests
import json
import base64
from io import BytesIO
from PIL import Image

# Create a simple test image (100x100 white square)
def create_test_image():
    img = Image.new('RGB', (100, 100), color='white')
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Test data
TEST_SCREENSHOT = create_test_image()
TEST_UI_TREE = {
    "windows": [
        {
            "title": "Notepad",
            "bounds": {"x": 100, "y": 100, "width": 800, "height": 600},
            "controls": [
                {
                    "type": "Edit",
                    "name": "Text Editor",
                    "bounds": {"x": 110, "y": 150, "width": 780, "height": 500}
                }
            ]
        }
    ]
}
TEST_REQUEST = "Click on the text editor"

def test_health():
    """Test health endpoint"""
    print("\n1. Testing health endpoint...")
    
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        data = response.json()
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(data, indent=2)}")
        
        if data['status'] == 'ok':
            print("   ✅ Health check passed")
            return True
        else:
            print("   ❌ Health check failed")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_providers():
    """Test providers list endpoint"""
    print("\n2. Testing providers list...")
    
    try:
        response = requests.get('http://localhost:5000/api/providers', timeout=5)
        data = response.json()
        
        print(f"   Status: {response.status_code}")
        print(f"   Available providers:")
        
        for provider in data['providers']:
            privacy_badge = f" 🔒 [{provider.get('privacy', 'cloud')}]" if 'privacy' in provider else ""
            config_badge = "✓" if provider['configured'] else "✗"
            print(f"      {config_badge} {provider['name']} ({provider['type']}){privacy_badge}")
        
        print("   ✅ Providers list retrieved")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_openai():
    """Test OpenAI provider"""
    print("\n3. Testing OpenAI provider...")
    
    try:
        # Check if configured
        health_response = requests.get('http://localhost:5000/api/health')
        health_data = health_response.json()
        
        if not health_data['providers']['openai']:
            print("   ⏭️  OpenAI not configured (skipping)")
            return True
        
        # Make request
        payload = {
            'provider': 'openai',
            'screenshot': TEST_SCREENSHOT,
            'ui_tree': TEST_UI_TREE,
            'user_request': TEST_REQUEST
        }
        
        print("   Sending request to OpenAI... (this may take a few seconds)")
        response = requests.post(
            'http://localhost:5000/api/get-actions',
            json=payload,
            timeout=30
        )
        data = response.json()
        
        print(f"   Status: {response.status_code}")
        
        if 'error' in data:
            print(f"   ❌ Error: {data['error']}")
            return False
        
        if data.get('success') and 'actions' in data:
            print(f"   ✅ Received {len(data['actions'])} actions:")
            for i, action in enumerate(data['actions'][:3]):  # Show first 3
                print(f"      {i+1}. {action['action']}: {action.get('params', {})}")
            return True
        else:
            print(f"   ❌ Unexpected response: {data}")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out (OpenAI may be slow)")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_ollama():
    """Test Ollama provider"""
    print("\n4. Testing Ollama provider...")
    
    try:
        # Check if Ollama is running
        try:
            ollama_health = requests.get('http://localhost:11434/api/tags', timeout=2)
            ollama_data = ollama_health.json()
            
            # Check for llava model
            has_llava = any('llava' in model['name'] for model in ollama_data.get('models', []))
            
            if not has_llava:
                print("   ⏭️  Ollama running but llava model not installed")
                print("      Run: ollama pull llava")
                return True
                
        except:
            print("   ⏭️  Ollama not running (skipping)")
            return True
        
        # Make request
        payload = {
            'provider': 'ollama',
            'screenshot': TEST_SCREENSHOT,
            'ui_tree': TEST_UI_TREE,
            'user_request': TEST_REQUEST
        }
        
        print("   Sending request to Ollama... (local inference may take 10-30 seconds)")
        response = requests.post(
            'http://localhost:5000/api/get-actions',
            json=payload,
            timeout=60  # Local can be slow
        )
        data = response.json()
        
        print(f"   Status: {response.status_code}")
        
        if 'error' in data:
            print(f"   ❌ Error: {data['error']}")
            return False
        
        if data.get('success') and 'actions' in data:
            print(f"   ✅ Received {len(data['actions'])} actions:")
            for i, action in enumerate(data['actions'][:3]):
                print(f"      {i+1}. {action['action']}: {action.get('params', {})}")
            return True
        else:
            print(f"   ❌ Unexpected response: {data}")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out (local inference is slow)")
        print("      Note: First request to Ollama can take 30+ seconds")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("=" * 70)
    print("🧪 Backend Proxy Server Tests")
    print("=" * 70)
    
    # Check if server is running
    try:
        requests.get('http://localhost:5000/api/health', timeout=2)
    except:
        print("\n❌ Backend server not running!")
        print("\nStart it with:")
        print("   cd backend")
        print("   python server.py")
        print()
        return
    
    # Run tests
    results = []
    results.append(("Health Check", test_health()))
    results.append(("Providers List", test_providers()))
    results.append(("OpenAI Provider", test_openai()))
    results.append(("Ollama Provider", test_ollama()))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} - {name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print()
    print(f"   {passed_count}/{total_count} tests passed")
    print("=" * 70)
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Backend is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check configuration:")
        print("   - OpenAI: Set OPENAI_API_KEY in .env")
        print("   - Ollama: Install from https://ollama.ai and run 'ollama pull llava'")
    
    print()

if __name__ == '__main__':
    main()

