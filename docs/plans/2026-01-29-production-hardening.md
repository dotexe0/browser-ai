# Production Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Harden all 3 layers for production use: security, input validation, error recovery, and testing.

**Architecture:** Each layer is hardened independently. Layer 1 (JS) gets API key encryption and input sanitization. Layer 2 (C++) gets coordinate validation, CaptureRegion, and timeout recovery. Layer 3 (Python) gets CORS lockdown, request validation, rate limiting, and production mode. Layer 4 adds pytest-based testing for all layers.

**Tech Stack:** JavaScript (Chrome WebUI), C++17 (Windows SDK), Python 3 (Flask), pytest

---

## Phase 1: Layer 1 - Browser UI Hardening

### Task 1: Encrypt API keys in localStorage

**Files:**
- Modify: `src/chrome/browser/ui/webui/ai_panel/resources/ai_provider_manager.js`

**Step 1: Add encryption utilities at the top of AIProviderManager**

Before the class definition, add:

```javascript
const _keyEncrypt = {
  async encrypt(plaintext) {
    const key = await this._getKey();
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encoded = new TextEncoder().encode(plaintext);
    const ciphertext = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      key,
      encoded
    );
    const combined = new Uint8Array(iv.length + ciphertext.byteLength);
    combined.set(iv, 0);
    combined.set(new Uint8Array(ciphertext), iv.length);
    return btoa(String.fromCharCode(...combined));
  },

  async decrypt(stored) {
    try {
      const key = await this._getKey();
      const raw = Uint8Array.from(atob(stored), c => c.charCodeAt(0));
      const iv = raw.slice(0, 12);
      const ciphertext = raw.slice(12);
      const decrypted = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv },
        key,
        ciphertext
      );
      return new TextDecoder().decode(decrypted);
    } catch {
      return stored; // Fallback: return raw value for unencrypted legacy keys
    }
  },

  async _getKey() {
    if (!this._cachedKey) {
      const keyMaterial = new TextEncoder().encode('browser-ai-local-key-v1');
      const baseKey = await crypto.subtle.importKey(
        'raw', keyMaterial, 'PBKDF2', false, ['deriveKey']
      );
      this._cachedKey = await crypto.subtle.deriveKey(
        { name: 'PBKDF2', salt: new TextEncoder().encode('ai-panel-salt'), iterations: 100000, hash: 'SHA-256' },
        baseKey,
        { name: 'AES-GCM', length: 256 },
        false,
        ['encrypt', 'decrypt']
      );
    }
    return this._cachedKey;
  },

  _cachedKey: null
};
```

**Step 2: Update `loadApiKey` to use async decryption**

Replace the `loadApiKey` method (lines 241-249):

```javascript
async loadApiKey(providerName) {
  try {
    const stored = localStorage.getItem(`ai_provider_key_${providerName}`);
    if (!stored) return null;
    return await _keyEncrypt.decrypt(stored);
  } catch (error) {
    console.error('Error loading API key:', error);
    return null;
  }
}
```

**Step 3: Update `saveApiKey` to use async encryption**

Replace the `saveApiKey` method (lines 255-263):

```javascript
async saveApiKey(providerName, apiKey) {
  try {
    const encrypted = await _keyEncrypt.encrypt(apiKey);
    localStorage.setItem(`ai_provider_key_${providerName}`, encrypted);
  } catch (error) {
    console.error('Error saving API key:', error);
  }
}
```

**Step 4: Update `configureProvider` to be async**

Replace the `configureProvider` method (lines 114-126):

```javascript
async configureProvider(providerName, apiKey) {
  const provider = this.providers.get(providerName);
  if (!provider) {
    throw new Error(`Provider not found: ${providerName}`);
  }
  if (provider.requiresApiKey) {
    provider.setApiKey(apiKey);
    await this.saveApiKey(providerName, apiKey);
    console.log(`Configured API key for: ${providerName}`);
  }
}
```

**Step 5: Update `loadUserPreference` to be async**

Replace `loadUserPreference` (lines 196-223):

```javascript
async loadUserPreference() {
  try {
    const savedProvider = localStorage.getItem('ai_provider_preference');
    if (savedProvider && this.providers.has(savedProvider)) {
      this.activeProvider = this.providers.get(savedProvider);
      if (this.activeProvider.requiresApiKey) {
        const savedKey = await this.loadApiKey(savedProvider);
        if (savedKey) {
          this.activeProvider.setApiKey(savedKey);
        }
      }
      console.log(`Loaded preferred provider: ${savedProvider}`);
    } else {
      this.activeProvider = Array.from(this.providers.values())[0];
      console.log(`Using default provider: ${this.activeProvider.name}`);
    }
  } catch (error) {
    console.error('Error loading user preference:', error);
    this.activeProvider = Array.from(this.providers.values())[0];
  }
}
```

**Step 6: Update `initialize` to await loadUserPreference**

Replace `initialize()` (lines 25-44):

```javascript
async initialize() {
  const openaiProvider = new OpenAIProvider();
  this.registerProvider(openaiProvider);
  const ollamaProvider = new OllamaProvider();
  this.registerProvider(ollamaProvider);
  const anthropicProvider = new AnthropicProvider();
  this.registerProvider(anthropicProvider);
  const localProvider = new LocalLLMProvider();
  this.registerProvider(localProvider);
  await this.loadUserPreference();
}
```

**Step 7: Update constructor to expose ready promise**

Replace constructor (lines 9-20):

```javascript
constructor() {
  this.providers = new Map();
  this.activeProvider = null;
  this.conversationHistory = [];
  this.ready = this.initialize();
}
```

**Step 8: Update ai_panel.js constructor to await ready**

In `ai_panel.js`, replace the DOMContentLoaded handler (lines 487-490):

```javascript
document.addEventListener('DOMContentLoaded', async () => {
  const panel = new AutomationPanel();
  await panel.providerManager.ready;
  panel.initializeUI();
  window.automationPanel = panel;
});
```

And update the AutomationPanel constructor to not call initializeUI synchronously:

```javascript
constructor() {
  this.providerManager = new AIProviderManager();
  this.currentScreenshot = null;
  this.currentUITree = null;
  this.plannedActions = null;
  this.attachEventListeners();
}
```

**Step 9: Commit**

```bash
git add src/chrome/browser/ui/webui/ai_panel/resources/ai_provider_manager.js
git add src/chrome/browser/ui/webui/ai_panel/resources/ai_panel.js
git commit -m "feat(layer1): encrypt API keys in localStorage with AES-GCM"
```

---

### Task 2: Add input validation to action execution

**Files:**
- Modify: `src/chrome/browser/ui/webui/ai_panel/resources/ai_panel.js`

**Step 1: Add action validation method to AutomationPanel**

Add after `cancelActions()` method (after line 353):

```javascript
/**
 * Validate an action before execution
 * @param {Object} action
 * @returns {{valid: boolean, error?: string}}
 */
validateAction(action) {
  if (!action || typeof action !== 'object') {
    return { valid: false, error: 'Action must be an object' };
  }

  const validActions = ['click', 'type', 'scroll', 'press_keys', 'wait'];
  if (!validActions.includes(action.action)) {
    return { valid: false, error: `Unknown action type: ${action.action}` };
  }

  const params = action.params || {};

  if (action.action === 'click') {
    if (typeof params.x !== 'number' || typeof params.y !== 'number') {
      return { valid: false, error: 'Click requires numeric x and y' };
    }
    if (params.x < 0 || params.y < 0 || params.x > 10000 || params.y > 10000) {
      return { valid: false, error: `Click coordinates out of bounds: (${params.x}, ${params.y})` };
    }
  }

  if (action.action === 'type') {
    if (typeof params.text !== 'string' || params.text.length === 0) {
      return { valid: false, error: 'Type requires non-empty text string' };
    }
    if (params.text.length > 10000) {
      return { valid: false, error: 'Text too long (max 10000 chars)' };
    }
  }

  if (action.action === 'wait') {
    if (typeof params.ms !== 'number' || params.ms < 0 || params.ms > 30000) {
      return { valid: false, error: 'Wait requires ms between 0 and 30000' };
    }
  }

  if (action.action === 'scroll') {
    if (typeof params.delta !== 'number') {
      return { valid: false, error: 'Scroll requires numeric delta' };
    }
  }

  if (action.action === 'press_keys') {
    if (!Array.isArray(params.keys) || params.keys.length === 0) {
      return { valid: false, error: 'press_keys requires non-empty keys array' };
    }
  }

  return { valid: true };
}
```

**Step 2: Add validation to confirmAndExecuteActions**

Replace `confirmAndExecuteActions()` (lines 307-344). Insert validation before the fetch call:

```javascript
async confirmAndExecuteActions() {
  if (!this.plannedActions || this.plannedActions.length === 0) {
    return;
  }

  // Validate all actions before executing
  for (let i = 0; i < this.plannedActions.length; i++) {
    const result = this.validateAction(this.plannedActions[i]);
    if (!result.valid) {
      this.log(`Action ${i + 1} invalid: ${result.error}`, 'error');
      return;
    }
  }

  this.log('Executing actions...', 'info');
  this.setAutomationStatus('working');
  document.getElementById('actions-section').classList.add('hidden');

  try {
    const response = await fetch('http://localhost:5000/api/get-actions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider: this.providerManager.getActiveProvider()?.providerId || 'ollama',
        screenshot: this.currentScreenshot || '',
        ui_tree: this.currentUITree || {},
        user_request: document.getElementById('user-request').value.trim(),
        execute: true,
        actions: this.plannedActions
      })
    });

    const data = await response.json();

    if (data.all_executed) {
      this.log('All actions executed successfully', 'success');
    } else if (data.execution_failed_at !== undefined) {
      this.log(`Execution failed at action ${data.execution_failed_at + 1}`, 'error');
    }

    this.setAutomationStatus('ready');
    this.plannedActions = null;
  } catch (error) {
    this.log(`Execution error: ${error.message}`, 'error');
    this.setAutomationStatus('error');
  }
}
```

**Step 3: Add validation to displayActions to show invalid actions visually**

Replace `displayActions()` (lines 377-401):

```javascript
displayActions(actions) {
  const section = document.getElementById('actions-section');
  const list = document.getElementById('actions-list');
  list.innerHTML = '';

  actions.forEach((action, index) => {
    const validation = this.validateAction(action);
    const item = document.createElement('div');
    item.className = `action-item${validation.valid ? '' : ' invalid'}`;

    item.innerHTML = `
      <div class="action-details">
        <div class="action-type">${index + 1}. ${(action.action || 'UNKNOWN').toUpperCase()}${validation.valid ? '' : ' [INVALID]'}</div>
        <div class="action-params">${JSON.stringify(action.params || {})}</div>
        ${validation.valid ? '' : `<div class="action-error">${validation.error}</div>`}
      </div>
      <div class="action-confidence">
        ${Math.round((action.confidence || 0) * 100)}% confident
      </div>
    `;

    list.appendChild(item);
  });

  section.classList.remove('hidden');
}
```

**Step 4: Commit**

```bash
git add src/chrome/browser/ui/webui/ai_panel/resources/ai_panel.js
git commit -m "feat(layer1): add action validation before execution"
```

---

### Task 3: Sanitize user request input

**Files:**
- Modify: `src/chrome/browser/ui/webui/ai_panel/resources/ai_panel.js`

**Step 1: Add sanitization method**

Add to AutomationPanel class:

```javascript
/**
 * Sanitize user input request
 * @param {string} input
 * @returns {string}
 */
sanitizeRequest(input) {
  if (typeof input !== 'string') return '';
  // Trim and limit length
  let sanitized = input.trim().substring(0, 2000);
  // Remove control characters except newlines
  sanitized = sanitized.replace(/[\x00-\x09\x0B\x0C\x0E-\x1F\x7F]/g, '');
  return sanitized;
}
```

**Step 2: Apply sanitization in executeAutomation**

In `executeAutomation()`, replace line 264:

```javascript
const userRequest = this.sanitizeRequest(document.getElementById('user-request').value);
```

**Step 3: Commit**

```bash
git add src/chrome/browser/ui/webui/ai_panel/resources/ai_panel.js
git commit -m "feat(layer1): sanitize user request input"
```

---

## Phase 2: Layer 2 - C++ Automation Service Hardening

### Task 4: Add coordinate bounds checking to InputController

**Files:**
- Modify: `automation_service/src/input_controller.cpp`
- Modify: `automation_service/src/input_controller.h`

**Step 1: Add bounds checking method to header**

In `input_controller.h`, add to private section:

```cpp
bool ValidateCoordinates(int x, int y) const;
```

**Step 2: Implement bounds checking in .cpp**

Add before `ScreenToAbsolute`:

```cpp
bool InputController::ValidateCoordinates(int x, int y) const {
    return x >= 0 && y >= 0 && x < screenWidth_ && y < screenHeight_;
}
```

**Step 3: Add validation to Click, DoubleClick, Drag, MoveMouse, Scroll**

In `Click()`, add at the beginning (after line 40):

```cpp
void InputController::Click(int x, int y, MouseButton button) {
    if (!ValidateCoordinates(x, y)) {
        LOG_ERROR(L"Click coordinates out of bounds: (%d, %d), screen: (%d, %d)", x, y, screenWidth_, screenHeight_);
        return;
    }
    // ... rest of existing code
```

Apply same pattern to `MoveMouse`, `DoubleClick`, `Drag` (validate both start and end), and `Scroll` (when x,y >= 0).

**Step 4: Update action_executor.cpp to return error on invalid coordinates**

In `ExecuteClick()`, add bounds check before calling inputController:

```cpp
json ActionExecutor::ExecuteClick(const json& params) {
    if (!params.contains("x") || !params.contains("y")) {
        return {{"success", false}, {"error", "Missing x or y coordinates"}};
    }

    int x = params["x"];
    int y = params["y"];

    int screenW, screenH;
    screenCapture_->GetScreenDimensions(screenW, screenH);
    if (x < 0 || y < 0 || x >= screenW || y >= screenH) {
        return {{"success", false}, {"error", "Coordinates out of screen bounds"}};
    }

    // ... rest of existing click code
```

**Step 5: Commit**

```bash
git add automation_service/src/input_controller.cpp automation_service/src/input_controller.h automation_service/src/action_executor.cpp
git commit -m "feat(layer2): add coordinate bounds validation"
```

---

### Task 5: Implement CaptureRegion cropping

**Files:**
- Modify: `automation_service/src/screen_capture.cpp`

**Step 1: Implement the CaptureRegion method**

Replace the stubbed `CaptureRegion` (lines 207-221):

```cpp
ImageData ScreenCapture::CaptureRegion(const Rect& region) {
    ImageData fullScreen = CaptureScreen();

    if (fullScreen.empty()) {
        return ImageData();
    }

    int screenW, screenH;
    GetScreenDimensions(screenW, screenH);

    // Clamp region to screen bounds
    int rx = std::max(0, region.x);
    int ry = std::max(0, region.y);
    int rw = std::min(region.width, screenW - rx);
    int rh = std::min(region.height, screenH - ry);

    if (rw <= 0 || rh <= 0) {
        return ImageData();
    }

    // fullScreen is BGRA, 4 bytes per pixel, rows are screenW * 4 bytes
    int srcStride = screenW * 4;
    int dstStride = rw * 4;
    ImageData cropped(dstStride * rh);

    for (int row = 0; row < rh; ++row) {
        const uint8_t* srcRow = fullScreen.data() + (ry + row) * srcStride + rx * 4;
        uint8_t* dstRow = cropped.data() + row * dstStride;
        memcpy(dstRow, srcRow, dstStride);
    }

    return cropped;
}
```

**Step 2: Commit**

```bash
git add automation_service/src/screen_capture.cpp
git commit -m "feat(layer2): implement CaptureRegion cropping"
```

---

### Task 6: Add wait limit and validate action params in action_executor

**Files:**
- Modify: `automation_service/src/action_executor.cpp`

**Step 1: Cap wait duration**

Replace `ExecuteWait` (lines 248-257):

```cpp
json ActionExecutor::ExecuteWait(const json& params) {
    if (!params.contains("ms")) {
        return {{"success", false}, {"error", "Missing ms parameter"}};
    }

    int ms = params["ms"];
    if (ms < 0 || ms > 30000) {
        return {{"success", false}, {"error", "Wait duration must be 0-30000ms"}};
    }

    inputController_->Wait(ms);
    return {{"success", true}, {"action", "wait"}};
}
```

**Step 2: Add text length limit in ExecuteType**

Replace `ExecuteType` (lines 206-217):

```cpp
json ActionExecutor::ExecuteType(const json& params) {
    if (!params.contains("text")) {
        return {{"success", false}, {"error", "Missing text parameter"}};
    }

    std::string text = params["text"];
    if (text.length() > 10000) {
        return {{"success", false}, {"error", "Text too long (max 10000 chars)"}};
    }

    std::wstring wtext = StringToWString(text);
    inputController_->TypeText(wtext);
    return {{"success", true}, {"action", "type"}};
}
```

**Step 3: Commit**

```bash
git add automation_service/src/action_executor.cpp
git commit -m "feat(layer2): add param limits for wait and type actions"
```

---

### Task 7: Build and verify Layer 2

**Step 1: Rebuild**

```bash
cd automation_service/build
cmake --build . --config Release
```

Expected: Build succeeds with only existing warnings.

**Step 2: Run ping test**

```bash
cd automation_service
python test_ping.py
```

Expected: Both tests pass.

**Step 3: Commit (if any fixes needed)**

---

## Phase 3: Layer 3 - Python Backend Hardening

### Task 8: Lock down CORS and disable debug mode

**Files:**
- Modify: `backend/server.py`

**Step 1: Replace open CORS with restricted origins**

Replace line 32:

```python
CORS(app, origins=['http://localhost:*', 'chrome-untrusted://*', 'chrome://*'])
```

**Step 2: Disable debug mode in production**

Replace the `app.run` line (line 530):

```python
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
```

**Step 3: Commit**

```bash
git add backend/server.py
git commit -m "feat(layer3): restrict CORS origins and disable debug by default"
```

---

### Task 9: Add request validation and size limits

**Files:**
- Modify: `backend/server.py`

**Step 1: Add request size limit**

After `CORS(app, ...)` line, add:

```python
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB max request
```

**Step 2: Add validation to /api/get-actions**

Replace the body of `get_actions()` starting at `data = request.json` (line 397):

```python
    data = request.json
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    provider = data.get('provider', 'openai')
    screenshot = data.get('screenshot', '')
    ui_tree = data.get('ui_tree', {})
    user_request = data.get('user_request', '')
    execute = data.get('execute', False)

    # Validate provider
    valid_providers = ('openai', 'anthropic', 'ollama')
    if provider not in valid_providers:
        return jsonify({'error': f'Unknown provider: {provider}. Valid: {valid_providers}'}), 400

    # Validate user_request
    if not user_request or not isinstance(user_request, str):
        return jsonify({'error': 'user_request is required and must be a string'}), 400
    if len(user_request) > 5000:
        return jsonify({'error': 'user_request too long (max 5000 chars)'}), 400

    # Validate screenshot size (base64 ~1.33x raw, 20MB raw = ~27MB base64)
    if screenshot and len(screenshot) > 30_000_000:
        return jsonify({'error': 'Screenshot too large (max ~20MB)'}), 400

    # Remove data URL prefix if present
    if screenshot.startswith('data:image'):
        screenshot = screenshot.split(',')[1]
```

**Step 3: Add validation to /api/add-provider**

Replace the `add_provider()` body:

```python
    data = request.json
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    provider_id = data.get('id')
    if not provider_id or not isinstance(provider_id, str):
        return jsonify({'error': 'Provider ID required (string)'}), 400
    if len(provider_id) > 50:
        return jsonify({'error': 'Provider ID too long'}), 400

    # Only allow adding config, not overwriting built-in providers
    builtin = ('openai', 'anthropic', 'ollama')
    if provider_id in builtin:
        return jsonify({'error': f'Cannot overwrite built-in provider: {provider_id}'}), 400

    PROVIDERS[provider_id] = data.get('config', {})
    return jsonify({'success': True, 'message': f'Provider {provider_id} added'})
```

**Step 4: Commit**

```bash
git add backend/server.py
git commit -m "feat(layer3): add request validation and size limits"
```

---

### Task 10: Add rate limiting

**Files:**
- Modify: `backend/server.py`

**Step 1: Add simple in-memory rate limiter**

After imports, add:

```python
import time
from functools import wraps

# Simple rate limiter
_rate_limit_store = {}

def rate_limit(max_per_minute=30):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            client_ip = request.remote_addr
            now = time.time()
            key = f'{f.__name__}:{client_ip}'

            # Clean old entries
            if key in _rate_limit_store:
                _rate_limit_store[key] = [t for t in _rate_limit_store[key] if now - t < 60]
            else:
                _rate_limit_store[key] = []

            if len(_rate_limit_store[key]) >= max_per_minute:
                return jsonify({'error': 'Rate limit exceeded. Try again later.'}), 429

            _rate_limit_store[key].append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator
```

**Step 2: Apply rate limiting to expensive endpoints**

Add decorator to `get_actions`:

```python
@app.route('/api/get-actions', methods=['POST'])
@rate_limit(max_per_minute=20)
def get_actions():
```

Add decorator to `capture_screen`:

```python
@app.route('/api/capture', methods=['POST'])
@rate_limit(max_per_minute=30)
def capture_screen():
```

**Step 3: Commit**

```bash
git add backend/server.py
git commit -m "feat(layer3): add rate limiting to expensive endpoints"
```

---

### Task 11: Add AI response validation

**Files:**
- Modify: `backend/server.py`

**Step 1: Add response validation function**

After the rate limiter code, add:

```python
def validate_ai_actions(actions):
    """Validate and sanitize AI-generated actions before execution."""
    if not isinstance(actions, list):
        return []

    valid_action_types = {'click', 'type', 'scroll', 'press_keys', 'wait'}
    validated = []

    for action in actions:
        if not isinstance(action, dict):
            continue
        action_type = action.get('action')
        if action_type not in valid_action_types:
            continue

        params = action.get('params', {})
        if not isinstance(params, dict):
            continue

        # Validate per-action params
        if action_type == 'click':
            x, y = params.get('x'), params.get('y')
            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                continue
            if x < 0 or y < 0 or x > 10000 or y > 10000:
                continue

        if action_type == 'type':
            text = params.get('text', '')
            if not isinstance(text, str) or len(text) == 0 or len(text) > 10000:
                continue

        if action_type == 'wait':
            ms = params.get('ms', 0)
            if not isinstance(ms, (int, float)) or ms < 0 or ms > 30000:
                continue

        validated.append(action)

    return validated
```

**Step 2: Apply validation in get_actions before execution**

In the `get_actions` endpoint, after `result = call_*()`, before the execute block, add:

```python
    # Validate AI-generated actions
    if result.get('success') and result.get('actions'):
        result['actions'] = validate_ai_actions(result['actions'])
        if not result['actions']:
            result['success'] = False
            result['error'] = 'AI returned no valid actions'
```

**Step 3: Commit**

```bash
git add backend/server.py
git commit -m "feat(layer3): validate AI-generated actions before execution"
```

---

### Task 12: Test Layer 3 changes

**Step 1: Restart the backend**

Stop and restart `backend/server.py`.

**Step 2: Run test_backend.py**

```bash
cd backend && python test_backend.py
```

Expected: Health, providers, and Ollama tests pass (3/4 minimum).

**Step 3: Commit (if any fixes needed)**

---

## Phase 4: Testing Infrastructure

### Task 13: Set up pytest framework for backend

**Files:**
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_api.py`
- Create: `backend/tests/conftest.py`

**Step 1: Create conftest.py with Flask test client**

```python
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from server import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
```

**Step 2: Create test_api.py**

```python
"""Backend API tests."""
import json


def test_health_endpoint(client):
    resp = client.get('/api/health')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'ok'
    assert 'providers' in data


def test_providers_endpoint(client):
    resp = client.get('/api/providers')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'providers' in data
    assert isinstance(data['providers'], list)
    # Ollama should always be listed
    names = [p['name'] for p in data['providers']]
    assert 'Ollama (Local)' in names


def test_get_actions_missing_request(client):
    resp = client.post('/api/get-actions',
                       json={'provider': 'ollama', 'screenshot': '', 'ui_tree': {}})
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'error' in data


def test_get_actions_invalid_provider(client):
    resp = client.post('/api/get-actions',
                       json={'provider': 'nonexistent', 'user_request': 'test'})
    assert resp.status_code == 400


def test_get_actions_request_too_long(client):
    resp = client.post('/api/get-actions',
                       json={'provider': 'ollama', 'user_request': 'x' * 6000})
    assert resp.status_code == 400


def test_add_provider_missing_id(client):
    resp = client.post('/api/add-provider', json={})
    assert resp.status_code == 400


def test_add_provider_cannot_overwrite_builtin(client):
    resp = client.post('/api/add-provider', json={'id': 'openai', 'config': {}})
    assert resp.status_code == 400


def test_add_provider_success(client):
    resp = client.post('/api/add-provider',
                       json={'id': 'custom_test', 'config': {'endpoint': 'http://example.com'}})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True


def test_capture_no_service(client, monkeypatch):
    """If automation service doesn't exist, capture returns error."""
    monkeypatch.setattr('os.path.exists', lambda p: False)
    resp = client.post('/api/capture', json={'action': 'capture'})
    assert resp.status_code == 500
```

**Step 3: Create empty __init__.py**

```python
```

**Step 4: Run the tests**

```bash
cd backend && python -m pytest tests/ -v
```

Expected: All tests pass.

**Step 5: Commit**

```bash
git add backend/tests/
git commit -m "feat(testing): add pytest framework with backend API tests"
```

---

### Task 14: Add pytest tests for action validation

**Files:**
- Create: `backend/tests/test_validation.py`

**Step 1: Create validation tests**

```python
"""Tests for AI action validation."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from server import validate_ai_actions


def test_valid_click():
    actions = [{'action': 'click', 'params': {'x': 100, 'y': 200}}]
    result = validate_ai_actions(actions)
    assert len(result) == 1


def test_click_negative_coords():
    actions = [{'action': 'click', 'params': {'x': -1, 'y': 200}}]
    result = validate_ai_actions(actions)
    assert len(result) == 0


def test_click_huge_coords():
    actions = [{'action': 'click', 'params': {'x': 99999, 'y': 200}}]
    result = validate_ai_actions(actions)
    assert len(result) == 0


def test_valid_type():
    actions = [{'action': 'type', 'params': {'text': 'hello'}}]
    result = validate_ai_actions(actions)
    assert len(result) == 1


def test_type_empty_text():
    actions = [{'action': 'type', 'params': {'text': ''}}]
    result = validate_ai_actions(actions)
    assert len(result) == 0


def test_type_too_long():
    actions = [{'action': 'type', 'params': {'text': 'x' * 20000}}]
    result = validate_ai_actions(actions)
    assert len(result) == 0


def test_valid_wait():
    actions = [{'action': 'wait', 'params': {'ms': 1000}}]
    result = validate_ai_actions(actions)
    assert len(result) == 1


def test_wait_too_long():
    actions = [{'action': 'wait', 'params': {'ms': 999999}}]
    result = validate_ai_actions(actions)
    assert len(result) == 0


def test_unknown_action_stripped():
    actions = [
        {'action': 'click', 'params': {'x': 10, 'y': 20}},
        {'action': 'hack_system', 'params': {}},
        {'action': 'type', 'params': {'text': 'ok'}},
    ]
    result = validate_ai_actions(actions)
    assert len(result) == 2
    assert result[0]['action'] == 'click'
    assert result[1]['action'] == 'type'


def test_non_list_returns_empty():
    assert validate_ai_actions("not a list") == []
    assert validate_ai_actions(None) == []
    assert validate_ai_actions(42) == []


def test_non_dict_items_skipped():
    actions = [{'action': 'click', 'params': {'x': 5, 'y': 5}}, "bad", 42]
    result = validate_ai_actions(actions)
    assert len(result) == 1
```

**Step 2: Run**

```bash
cd backend && python -m pytest tests/test_validation.py -v
```

Expected: All tests pass.

**Step 3: Commit**

```bash
git add backend/tests/test_validation.py
git commit -m "feat(testing): add action validation tests"
```

---

### Task 15: Add rate limiter tests

**Files:**
- Create: `backend/tests/test_rate_limit.py`

**Step 1: Create rate limit tests**

```python
"""Tests for rate limiting."""


def test_rate_limit_allows_normal_usage(client):
    """Normal usage should not be rate limited."""
    for _ in range(5):
        resp = client.get('/api/health')
        assert resp.status_code == 200


def test_get_actions_rate_limit(client):
    """Exceeding rate limit returns 429."""
    payload = {'provider': 'ollama', 'user_request': 'test'}
    responses = []
    for _ in range(25):
        resp = client.post('/api/get-actions', json=payload)
        responses.append(resp.status_code)

    # At least some should be rate-limited (429)
    assert 429 in responses
```

**Step 2: Run all tests**

```bash
cd backend && python -m pytest tests/ -v
```

**Step 3: Commit**

```bash
git add backend/tests/test_rate_limit.py
git commit -m "feat(testing): add rate limiter tests"
```

---

### Task 16: Final verification - run all tests

**Step 1: Run all backend pytest tests**

```bash
cd backend && python -m pytest tests/ -v
```

**Step 2: Run automation service tests**

```bash
cd automation_service && python test_ping.py
```

**Step 3: Run backend integration tests**

```bash
cd backend && python test_backend.py
```

All should pass. Fix any issues and commit.

---

## Summary

| Phase | Tasks | What it does |
|-------|-------|-------------|
| Phase 1: Layer 1 | Tasks 1-3 | API key encryption, action validation, input sanitization |
| Phase 2: Layer 2 | Tasks 4-7 | Coordinate bounds, CaptureRegion, param limits, rebuild |
| Phase 3: Layer 3 | Tasks 8-12 | CORS lockdown, request validation, rate limiting, AI response validation |
| Phase 4: Testing | Tasks 13-16 | pytest framework, API tests, validation tests, rate limit tests |
