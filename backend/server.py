#!/usr/bin/env python3
"""
Provider-Agnostic AI Proxy Server

Supports multiple AI providers:
- OpenAI GPT-4 Vision
- Anthropic Claude
- Local models (via Ollama)
- Easy to add more providers

Benefits:
- Keeps API keys secure (server-side only)
- Single endpoint for browser
- Provider abstraction
- Rate limiting and logging
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import base64
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow requests from browser

# Provider configurations
PROVIDERS = {
    'openai': {
        'api_key': os.getenv('OPENAI_API_KEY', ''),
        'endpoint': 'https://api.openai.com/v1/chat/completions',
        'model': 'gpt-4-vision-preview'
    },
    'anthropic': {
        'api_key': os.getenv('ANTHROPIC_API_KEY', ''),
        'endpoint': 'https://api.anthropic.com/v1/messages',
        'model': 'claude-3-sonnet-20240229'
    },
    'ollama': {
        'endpoint': os.getenv('OLLAMA_ENDPOINT', 'http://localhost:11434/api/generate'),
        'model': os.getenv('OLLAMA_MODEL', 'llava')  # Vision-capable model
    }
}


def call_openai(screenshot_base64, ui_tree, user_request):
    """Call OpenAI GPT-4 Vision API"""
    
    api_key = PROVIDERS['openai']['api_key']
    if not api_key:
        return {'error': 'OpenAI API key not configured'}
    
    # Build the prompt
    system_prompt = """You are a desktop automation assistant. Analyze the screenshot and UI tree, then return a JSON array of actions to accomplish the user's request.

Available actions:
- click: {action: "click", params: {x: 100, y: 200}}
- type: {action: "type", params: {text: "hello"}}
- press_keys: {action: "press_keys", params: {keys: ["LWin", "R"]}}
- scroll: {action: "scroll", params: {delta: -3, x: 500, y: 400}}
- wait: {action: "wait", params: {ms: 1000}}

Return ONLY a JSON array of actions, no other text."""

    # Prepare the request
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': PROVIDERS['openai']['model'],
        'messages': [
            {
                'role': 'system',
                'content': system_prompt
            },
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': f"User request: {user_request}\n\nUI Tree: {json.dumps(ui_tree, indent=2)}"
                    },
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f'data:image/png;base64,{screenshot_base64}'
                        }
                    }
                ]
            }
        ],
        'max_tokens': 1000
    }
    
    try:
        response = requests.post(
            PROVIDERS['openai']['endpoint'],
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        actions_text = result['choices'][0]['message']['content']
        
        # Try to parse as JSON
        try:
            actions = json.loads(actions_text)
            return {'success': True, 'actions': actions}
        except json.JSONDecodeError:
            # If not valid JSON, return as error
            return {'error': 'Failed to parse AI response as JSON', 'raw_response': actions_text}
            
    except requests.exceptions.RequestException as e:
        return {'error': f'OpenAI API error: {str(e)}'}


def call_anthropic(screenshot_base64, ui_tree, user_request):
    """Call Anthropic Claude API"""
    
    api_key = PROVIDERS['anthropic']['api_key']
    if not api_key:
        return {'error': 'Anthropic API key not configured'}
    
    # Claude has different vision API format
    headers = {
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01',
        'Content-Type': 'application/json'
    }
    
    system_prompt = """You are a desktop automation assistant. Return ONLY a JSON array of actions."""
    
    payload = {
        'model': PROVIDERS['anthropic']['model'],
        'max_tokens': 1024,
        'messages': [
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'image',
                        'source': {
                            'type': 'base64',
                            'media_type': 'image/png',
                            'data': screenshot_base64
                        }
                    },
                    {
                        'type': 'text',
                        'text': f"{system_prompt}\n\nUser request: {user_request}\n\nUI Tree: {json.dumps(ui_tree)}"
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(
            PROVIDERS['anthropic']['endpoint'],
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        actions_text = result['content'][0]['text']
        
        try:
            actions = json.loads(actions_text)
            return {'success': True, 'actions': actions}
        except json.JSONDecodeError:
            return {'error': 'Failed to parse AI response', 'raw_response': actions_text}
            
    except requests.exceptions.RequestException as e:
        return {'error': f'Anthropic API error: {str(e)}'}


def call_ollama(screenshot_base64, ui_tree, user_request):
    """Call local Ollama instance"""
    
    endpoint = PROVIDERS['ollama']['endpoint']
    model = PROVIDERS['ollama']['model']
    
    prompt = f"""Analyze this desktop screenshot and return a JSON array of actions to: {user_request}

UI Tree: {json.dumps(ui_tree)}

Available actions: click, type, press_keys, scroll, wait
Return ONLY JSON array, no other text."""
    
    payload = {
        'model': model,
        'prompt': prompt,
        'images': [screenshot_base64],
        'stream': False
    }
    
    try:
        response = requests.post(
            endpoint,
            json=payload,
            timeout=60  # Local inference can be slow
        )
        response.raise_for_status()
        
        result = response.json()
        actions_text = result.get('response', '')
        
        # Strip markdown code fences if present
        actions_text = actions_text.strip()
        if actions_text.startswith('```'):
            # Remove opening fence
            lines = actions_text.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]  # Remove ```json or ```
            # Remove closing fence
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            actions_text = '\n'.join(lines).strip()
        
        print(f"[DEBUG] Ollama actions_text after stripping: {repr(actions_text)}", flush=True)
        
        try:
            actions = json.loads(actions_text)
            print(f"[DEBUG] Successfully parsed {len(actions)} actions", flush=True)
            return {'success': True, 'actions': actions}
        except json.JSONDecodeError as e:
            print(f"[DEBUG] JSON parse error: {e}", flush=True)
            return {'error': 'Failed to parse Ollama response', 'raw_response': actions_text}
            
    except requests.exceptions.RequestException as e:
        return {'error': f'Ollama error: {str(e)}. Is Ollama running?'}


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'providers': {
            'openai': bool(PROVIDERS['openai']['api_key']),
            'anthropic': bool(PROVIDERS['anthropic']['api_key']),
            'ollama': True  # Always available if running
        }
    })


@app.route('/api/providers', methods=['GET'])
def list_providers():
    """List available providers"""
    available = []
    
    if PROVIDERS['openai']['api_key']:
        available.append({
            'id': 'openai',
            'name': 'OpenAI GPT-4 Vision',
            'type': 'cloud',
            'requires_key': True,
            'configured': True
        })
    
    if PROVIDERS['anthropic']['api_key']:
        available.append({
            'id': 'anthropic',
            'name': 'Anthropic Claude',
            'type': 'cloud',
            'requires_key': True,
            'configured': True
        })
    
    # Ollama is always "available" but might not be running
    available.append({
        'id': 'ollama',
        'name': 'Ollama (Local)',
        'type': 'local',
        'requires_key': False,
        'configured': True,
        'privacy': 'full'
    })
    
    return jsonify({'providers': available})


@app.route('/api/get-actions', methods=['POST'])
def get_actions():
    """
    Get automation actions from AI provider
    
    Request body:
    {
        "provider": "openai" | "anthropic" | "ollama",
        "screenshot": "base64_encoded_png",
        "ui_tree": {...},
        "user_request": "Open Notepad and type hello"
    }
    
    Response:
    {
        "success": true,
        "actions": [...]
    }
    """
    
    data = request.json
    provider = data.get('provider', 'openai')
    screenshot = data.get('screenshot', '')
    ui_tree = data.get('ui_tree', {})
    user_request = data.get('user_request', '')
    
    if not user_request:
        return jsonify({'error': 'user_request is required'}), 400
    
    # Remove data URL prefix if present
    if screenshot.startswith('data:image'):
        screenshot = screenshot.split(',')[1]
    
    # Route to appropriate provider
    if provider == 'openai':
        result = call_openai(screenshot, ui_tree, user_request)
    elif provider == 'anthropic':
        result = call_anthropic(screenshot, ui_tree, user_request)
    elif provider == 'ollama':
        result = call_ollama(screenshot, ui_tree, user_request)
    else:
        return jsonify({'error': f'Unknown provider: {provider}'}), 400
    
    return jsonify(result)


@app.route('/api/add-provider', methods=['POST'])
def add_provider():
    """
    Add or update provider configuration
    
    Allows adding custom providers at runtime
    """
    data = request.json
    provider_id = data.get('id')
    
    if not provider_id:
        return jsonify({'error': 'Provider ID required'}), 400
    
    # Store custom provider config
    PROVIDERS[provider_id] = data.get('config', {})
    
    return jsonify({'success': True, 'message': f'Provider {provider_id} added'})


if __name__ == '__main__':
    print("=" * 70, flush=True)
    print("Provider-Agnostic AI Proxy Server", flush=True)
    print("=" * 70, flush=True)
    print(flush=True)
    print("Configured providers:", flush=True)
    
    if PROVIDERS['openai']['api_key']:
        print("  [OK] OpenAI GPT-4 Vision (cloud)", flush=True)
    else:
        print("  [ ] OpenAI (no API key)", flush=True)
    
    if PROVIDERS['anthropic']['api_key']:
        print("  [OK] Anthropic Claude (cloud)", flush=True)
    else:
        print("  [ ] Anthropic (no API key)", flush=True)
    
    print("  [?] Ollama (local) - check if running", flush=True)
    print(flush=True)
    print("Endpoints:", flush=True)
    print("  GET  /api/health - Health check", flush=True)
    print("  GET  /api/providers - List available providers", flush=True)
    print("  POST /api/get-actions - Get AI actions", flush=True)
    print("  POST /api/add-provider - Add custom provider", flush=True)
    print(flush=True)
    print("Starting server on http://localhost:5000", flush=True)
    print("=" * 70, flush=True)
    print(flush=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

