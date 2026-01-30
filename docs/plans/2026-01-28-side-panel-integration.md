# Side Panel Integration - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete the browser-ai project by converting the standalone `chrome://ai-panel` page into a Chrome Side Panel, wiring up the C++ handler to call the Python backend via HTTP, fixing the screen capture PNG encoding bug, adding an Anthropic provider to the frontend, and replacing all JavaScript stubs with real calls.

**Architecture:** The Chrome Side Panel registers via `SidePanelEntry` in the existing Chromium Side Panel system. The WebUI HTML/CSS/JS resources are served at `chrome://ai-panel-side-panel.top-chrome/` and rendered in the side panel. The C++ handler makes HTTP POST requests to `localhost:5000` (Python backend). The Python backend already supports OpenAI, Anthropic, and Ollama - no backend changes needed.

**Tech Stack:** C++ (Chromium WebUI, WinHTTP), JavaScript (vanilla, provider classes), Python (Flask backend - already complete)

---

## Task 1: Fix screen capture PNG encoding

The WIC stream is initialized with `InitializeFromMemory(nullptr, 0)` which creates a zero-size read-only buffer. Must use `CreateStreamOnHGlobal` instead for a growable in-memory stream.

**Files:**
- Modify: `automation_service/src/screen_capture.cpp:244-257`

**Step 1: Fix the stream initialization**

Replace the WIC stream initialization (lines 243-257) with an IStream created via `CreateStreamOnHGlobal`:

```cpp
// Create stream - use CreateStreamOnHGlobal for a growable memory stream
IStream* memStream = nullptr;
hr = CreateStreamOnHGlobal(nullptr, TRUE, &memStream);
if (FAILED(hr) || !memStream) {
    factory->Release();
    LOG_ERROR(L"Failed to create memory stream");
    return "";
}
```

Then remove the `IWICStream` usage and use `memStream` directly with the encoder:

```cpp
hr = encoder->Initialize(memStream, WICBitmapEncoderNoCache);
```

And update the stream reading section (lines 346-376) to read from `memStream` instead of querying for a separate `IStream`:

```cpp
// Get stream size
LARGE_INTEGER zero = {};
ULARGE_INTEGER streamSize;
hr = memStream->Seek(zero, STREAM_SEEK_END, &streamSize);
if (FAILED(hr)) {
    frame->Release();
    encoder->Release();
    memStream->Release();
    factory->Release();
    return "";
}

hr = memStream->Seek(zero, STREAM_SEEK_SET, nullptr);
if (FAILED(hr)) {
    frame->Release();
    encoder->Release();
    memStream->Release();
    factory->Release();
    return "";
}

// Read stream data
std::vector<unsigned char> pngData(static_cast<size_t>(streamSize.QuadPart));
ULONG bytesRead = 0;
hr = memStream->Read(pngData.data(), static_cast<ULONG>(pngData.size()), &bytesRead);

// Clean up
frame->Release();
encoder->Release();
memStream->Release();
factory->Release();
```

**Step 2: Rebuild the automation service**

Run:
```cmd
cd automation_service\build
cmake --build . --config Release
```
Expected: Build succeeds

**Step 3: Test screen capture**

Run:
```cmd
cd automation_service
python test_automation.py
```
Expected: Screen capture returns non-empty base64 PNG data

**Step 4: Commit**

```bash
git add automation_service/src/screen_capture.cpp
git commit -m "fix: screen capture PNG encoding using CreateStreamOnHGlobal"
```

---

## Task 2: Fix C++ syntax error and expand handler with HTTP backend calls

The handler has a syntax error (`base:BindRepeating` missing a colon) and only handles `ping`. Need to add handlers for `callBackend`, `captureScreen`, and `executeActions` that make HTTP calls to the Python backend.

**Files:**
- Modify: `src/chrome/browser/ui/webui/ai_panel/ai_panel_handler.h`
- Modify: `src/chrome/browser/ui/webui/ai_panel/ai_panel_handler.cc`

**Step 1: Update the header**

Replace the entire header file with handlers for all operations:

```cpp
#ifndef CHROME_BROWSER_UI_WEBUI_AI_PANEL_AI_PANEL_HANDLER_H_
#define CHROME_BROWSER_UI_WEBUI_AI_PANEL_AI_PANEL_HANDLER_H_

#include <string>
#include "content/public/browser/web_ui_message_handler.h"

class AiPanelHandler : public content::WebUIMessageHandler {
 public:
  AiPanelHandler() = default;
  ~AiPanelHandler() override = default;

  void RegisterMessages() override;

 private:
  void HandlePing(const base::Value::List& args);
  void HandleCallBackend(const base::Value::List& args);
  void HandleExecuteActions(const base::Value::List& args);

  // HTTP helper: POST JSON to url, return response body
  std::string HttpPost(const std::string& url, const std::string& json_body);
};

#endif  // CHROME_BROWSER_UI_WEBUI_AI_PANEL_AI_PANEL_HANDLER_H_
```

**Step 2: Implement the handler**

Replace the entire `.cc` file. Key additions:
- `HandleCallBackend`: receives provider, screenshot, ui_tree, user_request from JS, POSTs to `localhost:5000/api/get-actions`, returns response to JS.
- `HandleExecuteActions`: receives actions array, POSTs each to `localhost:5000/api/get-actions` with `execute: true`, returns results.
- `HttpPost`: uses WinHTTP to make HTTP POST requests.

```cpp
#include "chrome/browser/ui/webui/ai_panel/ai_panel_handler.h"

#include <windows.h>
#include <winhttp.h>
#include "base/functional/bind.h"
#include "base/json/json_reader.h"
#include "base/json/json_writer.h"
#include "base/values.h"

#pragma comment(lib, "winhttp.lib")

void AiPanelHandler::RegisterMessages() {
  web_ui()->RegisterMessageCallback(
      "ping",
      base::BindRepeating(&AiPanelHandler::HandlePing,
                          base::Unretained(this)));
  web_ui()->RegisterMessageCallback(
      "callBackend",
      base::BindRepeating(&AiPanelHandler::HandleCallBackend,
                          base::Unretained(this)));
  web_ui()->RegisterMessageCallback(
      "executeActions",
      base::BindRepeating(&AiPanelHandler::HandleExecuteActions,
                          base::Unretained(this)));
}

void AiPanelHandler::HandlePing(const base::Value::List& args) {
  AllowJavascript();
  FireWebUIListener("pong", base::Value("pong from C++"));
}

void AiPanelHandler::HandleCallBackend(const base::Value::List& args) {
  AllowJavascript();

  if (args.empty() || !args[0].is_string()) {
    FireWebUIListener("backendResponse",
                      base::Value("{\"error\":\"Invalid request\"}"));
    return;
  }

  const std::string& request_json = args[0].GetString();
  std::string response = HttpPost(
      "http://localhost:5000/api/get-actions", request_json);

  FireWebUIListener("backendResponse", base::Value(response));
}

void AiPanelHandler::HandleExecuteActions(const base::Value::List& args) {
  AllowJavascript();

  if (args.empty() || !args[0].is_string()) {
    FireWebUIListener("executeResponse",
                      base::Value("{\"error\":\"Invalid request\"}"));
    return;
  }

  const std::string& request_json = args[0].GetString();
  std::string response = HttpPost(
      "http://localhost:5000/api/get-actions", request_json);

  FireWebUIListener("executeResponse", base::Value(response));
}

std::string AiPanelHandler::HttpPost(const std::string& url,
                                      const std::string& json_body) {
  HINTERNET session = WinHttpOpen(L"BrowserAI/1.0",
                                   WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
                                   WINHTTP_NO_PROXY_NAME,
                                   WINHTTP_NO_PROXY_BYPASS, 0);
  if (!session)
    return "{\"error\":\"Failed to open HTTP session\"}";

  HINTERNET connection = WinHttpConnect(session, L"localhost",
                                         5000, 0);
  if (!connection) {
    WinHttpCloseHandle(session);
    return "{\"error\":\"Failed to connect to backend\"}";
  }

  HINTERNET request = WinHttpOpenRequest(connection, L"POST",
                                          L"/api/get-actions",
                                          nullptr, WINHTTP_NO_REFERER,
                                          WINHTTP_DEFAULT_ACCEPT_TYPES, 0);
  if (!request) {
    WinHttpCloseHandle(connection);
    WinHttpCloseHandle(session);
    return "{\"error\":\"Failed to create HTTP request\"}";
  }

  const wchar_t* headers = L"Content-Type: application/json\r\n";
  BOOL sent = WinHttpSendRequest(
      request, headers, -1L,
      (LPVOID)json_body.c_str(), json_body.size(),
      json_body.size(), 0);

  if (!sent || !WinHttpReceiveResponse(request, nullptr)) {
    WinHttpCloseHandle(request);
    WinHttpCloseHandle(connection);
    WinHttpCloseHandle(session);
    return "{\"error\":\"Backend not responding. Is server.py running?\"}";
  }

  // Read response
  std::string response;
  DWORD bytes_available = 0;
  do {
    WinHttpQueryDataAvailable(request, &bytes_available);
    if (bytes_available > 0) {
      std::vector<char> buffer(bytes_available + 1, 0);
      DWORD bytes_read = 0;
      WinHttpReadData(request, buffer.data(), bytes_available, &bytes_read);
      response.append(buffer.data(), bytes_read);
    }
  } while (bytes_available > 0);

  WinHttpCloseHandle(request);
  WinHttpCloseHandle(connection);
  WinHttpCloseHandle(session);

  return response.empty()
             ? "{\"error\":\"Empty response from backend\"}"
             : response;
}
```

**Step 3: Commit**

```bash
git add src/chrome/browser/ui/webui/ai_panel/ai_panel_handler.h
git add src/chrome/browser/ui/webui/ai_panel/ai_panel_handler.cc
git commit -m "feat: implement C++ handler with HTTP backend calls via WinHTTP"
```

---

## Task 3: Add Anthropic provider to frontend JavaScript

The backend already supports Anthropic, but the frontend has no `AnthropicProvider` class. Add one following the same pattern as `OpenAIProvider` and `OllamaProvider`.

**Files:**
- Create: `src/chrome/browser/ui/webui/ai_panel/resources/anthropic_provider.js`
- Modify: `src/chrome/browser/ui/webui/ai_panel/resources/ai_provider_manager.js` (register it)
- Modify: `src/chrome/browser/ui/webui/ai_panel/resources/ai_panel.html` (load script)
- Modify: `src/chrome/browser/ui/webui/ai_panel/ai_panel_ui.cc` (serve resource)

**Step 1: Create the Anthropic provider**

```javascript
/**
 * Anthropic Claude Provider
 *
 * Uses Anthropic's Claude API for desktop automation via backend proxy.
 */

class AnthropicProvider extends AIProvider {
  constructor() {
    super('Anthropic Claude', false); // API key managed server-side
    this.backendEndpoint = 'http://localhost:5000/api/get-actions';
    this.providerId = 'anthropic';
  }

  getCapabilities() {
    return {
      supportsVision: true,
      supportsStreaming: false,
      maxImageSize: 20 * 1024 * 1024,
      contextWindow: 200000
    };
  }

  async isConfigured() {
    try {
      const response = await fetch('http://localhost:5000/api/health');
      const data = await response.json();
      return data.providers.anthropic === true;
    } catch (error) {
      return false;
    }
  }

  async getActions(params) {
    const configured = await this.isConfigured();
    if (!configured) {
      throw new Error('Anthropic not configured. Set ANTHROPIC_API_KEY in backend .env file.');
    }

    const response = await this.callBackend(params);
    return this.parseResponse(response);
  }

  async callBackend(params) {
    const requestBody = {
      provider: this.providerId,
      screenshot: params.screenshot,
      ui_tree: params.uiTree,
      user_request: params.userRequest
    };

    const response = await fetch(this.backendEndpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP ${response.status}`);
    }

    return await response.json();
  }

  parseResponse(response) {
    if (response.error) throw new Error(response.error);
    if (!response.success || !Array.isArray(response.actions)) {
      throw new Error('Invalid response from Anthropic');
    }
    return response.actions.map(action => this.validateAction(action));
  }

  validateAction(action) {
    const validActions = ['click', 'type', 'scroll', 'press_keys', 'wait'];
    if (!action.action || !validActions.includes(action.action)) {
      throw new Error(`Invalid action type: ${action.action}`);
    }
    if (!action.params || typeof action.params !== 'object') {
      throw new Error(`Action missing params: ${JSON.stringify(action)}`);
    }
    if (typeof action.confidence !== 'number') {
      action.confidence = 0.85;
    }
    return action;
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AnthropicProvider };
}
```

**Step 2: Register in provider manager**

In `ai_provider_manager.js`, add after the Ollama registration (around line 33):

```javascript
// Register Anthropic provider (cloud, via backend proxy)
const anthropicProvider = new AnthropicProvider();
this.registerProvider(anthropicProvider);
```

And remove the TODO comment about Anthropic on lines 38-39.

**Step 3: Add script tag to HTML**

In `ai_panel.html`, add before the `ai_panel.js` script tag (line 122):

```html
<script src="anthropic_provider.js"></script>
```

**Step 4: Register resource in C++ WebUI**

In `ai_panel_ui.cc`, add after the existing `AddResourcePath` calls:

```cpp
source->AddResourcePath("anthropic_provider.js", IDR_AI_PANEL_ANTHROPIC_PROVIDER_JS);
```

(The IDR constant will need to be defined in the resource .grd file as part of the Chromium build integration.)

**Step 5: Commit**

```bash
git add src/chrome/browser/ui/webui/ai_panel/resources/anthropic_provider.js
git add src/chrome/browser/ui/webui/ai_panel/resources/ai_provider_manager.js
git add src/chrome/browser/ui/webui/ai_panel/resources/ai_panel.html
git add src/chrome/browser/ui/webui/ai_panel/ai_panel_ui.cc
git commit -m "feat: add Anthropic Claude provider to frontend"
```

---

## Task 4: Replace JavaScript stubs with real WebUI bridge calls

The `ai_panel.js` uses `simulateCaptureScreen()` and `simulateActionExecution()`. Replace these with calls through `chrome.send()` to the C++ handler, which forwards to the Python backend.

**Files:**
- Modify: `src/chrome/browser/ui/webui/ai_panel/resources/ai_panel.js`

**Step 1: Add WebUI bridge helper at top of file**

Add after the class declaration opens (after line 8):

```javascript
// WebUI bridge for communicating with C++ handler
this.pendingCallbacks = new Map();
this.callbackId = 0;

// Listen for C++ responses
if (typeof cr !== 'undefined' && cr.addWebUIListener) {
  cr.addWebUIListener('backendResponse', (response) => {
    this._handleBackendResponse(response);
  });
  cr.addWebUIListener('executeResponse', (response) => {
    this._handleExecuteResponse(response);
  });
}
```

**Step 2: Replace `captureScreen()` method**

Replace the `captureScreen()` method (lines 228-249) to use the C++ handler instead of simulation. The method should call `chrome.send('callBackend', [...])` with a capture_screen request that goes to the automation service, OR call the backend's screen-capture-aware endpoint.

Since the backend calls the automation service via subprocess, the flow is:
- JS calls `chrome.send('callBackend', [json])` with `user_request: "__capture_screen__"`
- C++ POSTs to Python backend
- Python backend calls automation_service.exe for screen capture + UI inspection

However, the simpler path is to make `captureScreen()` use `fetch()` directly to the backend (since WebUI pages can make HTTP requests) rather than routing through C++. This avoids unnecessary complexity:

```javascript
async captureScreen() {
  this.log('Capturing screen...', 'info');
  this.setAutomationStatus('working');

  try {
    // Call automation service directly for screen capture
    const response = await fetch('http://localhost:5000/api/capture', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'capture' })
    });

    if (!response.ok) {
      throw new Error(`Capture failed: ${response.status}`);
    }

    const data = await response.json();
    this.currentScreenshot = data.screenshot || '';
    this.currentUITree = data.ui_tree || {};

    if (this.currentScreenshot) {
      this.displayScreenPreview(this.currentScreenshot);
    }
    this.displayUITree(this.currentUITree);

    this.log('Screen captured successfully', 'success');
    this.setAutomationStatus('ready');
  } catch (error) {
    this.log(`Error capturing screen: ${error.message}`, 'error');
    this.setAutomationStatus('error');
  }
}
```

**Step 3: Replace `confirmAndExecuteActions()` method**

Replace the simulation loop (lines 298-325) to send actions to the backend with `execute: true`:

```javascript
async confirmAndExecuteActions() {
  if (!this.plannedActions || this.plannedActions.length === 0) {
    return;
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

**Step 4: Remove simulation methods**

Delete `simulateCaptureScreen()` (lines 470-497) and `simulateActionExecution()` (lines 503-509).

**Step 5: Commit**

```bash
git add src/chrome/browser/ui/webui/ai_panel/resources/ai_panel.js
git commit -m "feat: replace JS stubs with real backend calls"
```

---

## Task 5: Add /api/capture endpoint to Python backend

The frontend needs a capture endpoint that calls the automation service for screen capture + UI inspection and returns the results.

**Files:**
- Modify: `backend/server.py`

**Step 1: Add capture endpoint**

Add before the `if __name__` block:

```python
@app.route('/api/capture', methods=['POST'])
def capture_screen():
    """
    Capture screen and UI tree via automation service

    Returns:
    {
        "success": true,
        "screenshot": "base64_png",
        "ui_tree": {...}
    }
    """
    automation_service_path = os.path.join(
        os.path.dirname(__file__),
        '../automation_service/build/bin/Release/automation_service.exe'
    )

    if not os.path.exists(automation_service_path):
        return jsonify({
            'success': False,
            'error': f'Automation service not found at {automation_service_path}'
        }), 500

    result = {}

    # Capture screen
    try:
        screen_result = _call_automation_service(
            automation_service_path, {'action': 'capture_screen'})
        result['screenshot'] = screen_result.get('screenshot', '')
        result['width'] = screen_result.get('width', 0)
        result['height'] = screen_result.get('height', 0)
    except Exception as e:
        result['screenshot'] = ''
        result['capture_error'] = str(e)

    # Inspect UI
    try:
        ui_result = _call_automation_service(
            automation_service_path, {'action': 'inspect_ui'})
        result['ui_tree'] = ui_result.get('uiTree', {})
    except Exception as e:
        result['ui_tree'] = {}
        result['ui_error'] = str(e)

    result['success'] = True
    return jsonify(result)


def _call_automation_service(service_path, message):
    """Call automation service with Native Messaging protocol"""
    import struct

    message_json = json.dumps(message)
    message_bytes = message_json.encode('utf-8')
    # Native Messaging uses 4-byte length prefix
    length_prefix = struct.pack('I', len(message_bytes))

    process = subprocess.Popen(
        [service_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout, stderr = process.communicate(
        input=length_prefix + message_bytes, timeout=10)

    if not stdout or len(stdout) < 4:
        raise RuntimeError(f'No response from service: {stderr.decode("utf-8", errors="replace")}')

    # Read 4-byte length prefix
    response_length = struct.unpack('I', stdout[:4])[0]
    response_json = stdout[4:4 + response_length].decode('utf-8')
    return json.loads(response_json)
```

**Step 2: Also fix `execute_action_via_service` to use proper Native Messaging protocol**

The existing function uses a text-based protocol (`len\n{json}`) but the automation service uses Native Messaging (4-byte binary length prefix). Update it to use `_call_automation_service`:

```python
def execute_action_via_service(action):
    """Execute a single action via the automation service"""
    automation_service_path = os.path.join(
        os.path.dirname(__file__),
        '../automation_service/build/bin/Release/automation_service.exe'
    )

    if not os.path.exists(automation_service_path):
        return {'success': False, 'error': 'Automation service not found'}

    try:
        message = {
            'action': 'execute_action',
            'params': action
        }
        return _call_automation_service(automation_service_path, message)
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Automation service timeout'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

**Step 3: Commit**

```bash
git add backend/server.py
git commit -m "feat: add /api/capture endpoint and fix Native Messaging protocol"
```

---

## Task 6: Convert from standalone page to Chrome Side Panel

Change the WebUI registration from a standalone `chrome://ai-panel` page to a Chrome Side Panel entry. This involves creating a coordinator, registering the side panel entry, and updating the WebUI to serve at the side panel URL.

**Files:**
- Create: `src/chrome/browser/ui/views/side_panel/ai_panel/ai_panel_side_panel_coordinator.h`
- Create: `src/chrome/browser/ui/views/side_panel/ai_panel/ai_panel_side_panel_coordinator.cc`
- Modify: `src/chrome/browser/ui/webui/ai_panel/ai_panel_ui.h` (update for side panel URL)
- Modify: `src/chrome/browser/ui/webui/ai_panel/ai_panel_ui.cc` (update URL and resource serving)
- Modify: `src/chrome/browser/ui/webui/ai_panel/resources/ai_panel.css` (adapt layout for side panel)

### Side Panel Registration Files (Chromium modifications)

These files must be modified in `chromium/src/` and synced. The plan documents what changes to make:

**Modify in chromium/src:**
- `chrome/browser/ui/views/side_panel/side_panel_entry_id.h` - Add `kAIPanel` entry
- `chrome/browser/ui/actions/chrome_action_id.h` - Add action ID
- `chrome/browser/ui/views/side_panel/side_panel_util.cc` - Register in `PopulateGlobalEntries()`
- `chrome/browser/ui/browser_window/internal/browser_window_features.cc` - Create coordinator
- `chrome/browser/ui/webui/chrome_web_ui_configs.cc` - Register WebUI config

**Step 1: Create the coordinator header**

```cpp
#ifndef CHROME_BROWSER_UI_VIEWS_SIDE_PANEL_AI_PANEL_AI_PANEL_SIDE_PANEL_COORDINATOR_H_
#define CHROME_BROWSER_UI_VIEWS_SIDE_PANEL_AI_PANEL_AI_PANEL_SIDE_PANEL_COORDINATOR_H_

#include <memory>
#include "chrome/browser/ui/views/side_panel/side_panel_entry.h"

class Browser;
class SidePanelRegistry;

namespace views {
class View;
}

class AiPanelSidePanelCoordinator {
 public:
  explicit AiPanelSidePanelCoordinator(Browser* browser);
  ~AiPanelSidePanelCoordinator();

  void CreateAndRegisterEntry(SidePanelRegistry* global_registry);

 private:
  std::unique_ptr<views::View> CreateAiPanelWebView();

  raw_ptr<Browser> browser_;
};

#endif  // CHROME_BROWSER_UI_VIEWS_SIDE_PANEL_AI_PANEL_AI_PANEL_SIDE_PANEL_COORDINATOR_H_
```

**Step 2: Create the coordinator implementation**

```cpp
#include "chrome/browser/ui/views/side_panel/ai_panel/ai_panel_side_panel_coordinator.h"

#include "chrome/browser/ui/browser.h"
#include "chrome/browser/ui/views/side_panel/side_panel_entry.h"
#include "chrome/browser/ui/views/side_panel/side_panel_registry.h"
#include "chrome/browser/ui/views/side_panel/side_panel_web_ui_view.h"
#include "chrome/browser/ui/webui/ai_panel/ai_panel_ui.h"
#include "chrome/common/webui_url_constants.h"

AiPanelSidePanelCoordinator::AiPanelSidePanelCoordinator(Browser* browser)
    : browser_(browser) {}

AiPanelSidePanelCoordinator::~AiPanelSidePanelCoordinator() = default;

void AiPanelSidePanelCoordinator::CreateAndRegisterEntry(
    SidePanelRegistry* global_registry) {
  global_registry->Register(std::make_unique<SidePanelEntry>(
      SidePanelEntry::Key(SidePanelEntry::Id::kAIPanel),
      base::BindRepeating(
          &AiPanelSidePanelCoordinator::CreateAiPanelWebView,
          base::Unretained(this))));
}

std::unique_ptr<views::View>
AiPanelSidePanelCoordinator::CreateAiPanelWebView() {
  auto wrapper =
      std::make_unique<BubbleContentsWrapperT<AIPanelUI>>(
          GURL("chrome://ai-panel-side-panel.top-chrome/"),
          browser_->profile(),
          /*task_manager_string_id=*/0,
          /*webui_resizes_host=*/true,
          /*esc_closes_ui=*/false);
  wrapper->ReloadWebContents();

  auto view = std::make_unique<SidePanelWebUIViewT<AIPanelUI>>(
      browser_, base::NullCallback(), std::move(wrapper));
  return view;
}
```

**Step 3: Update the WebUI to use side panel URL**

In `ai_panel_ui.cc`, change the URL from `"ai-panel"` to `"ai-panel-side-panel.top-chrome"`:

```cpp
auto* source = content::WebUIDataSource::CreateAndAdd(
    web_ui->GetWebContents()->GetBrowserContext(),
    "ai-panel-side-panel.top-chrome");
```

**Step 4: Adapt CSS for side panel width**

The side panel is ~360px wide. Update `ai_panel.css`:

- Change `.panel-container` from `max-width: 900px` to `width: 100%; max-width: 100%;`
- Remove `margin: 0 auto` and `box-shadow`
- Reduce header padding from `20px` to `12px`
- Reduce font sizes for the constrained width
- Make textarea full width

Replace the top of the CSS:

```css
body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: var(--color-side-panel-background, #fff);
  color: var(--color-side-panel-foreground, #333);
  line-height: 1.5;
  font-size: 13px;
  margin: 0;
  padding: 0;
}

.panel-container {
  width: 100%;
  min-height: 100vh;
}

.panel-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h1 {
  font-size: 16px;
  font-weight: 600;
}
```

**Step 5: Add kAIPanel to side_panel_entry_id.h** (in chromium/src)

Add to the `SIDE_PANEL_ENTRY_IDS` macro:

```cpp
V(kAIPanel, kActionSidePanelShowAIPanel, "AIPanel")
```

**Step 6: Add action ID** (in chromium/src)

In `chrome_action_id.h`, add:

```cpp
kActionSidePanelShowAIPanel,
```

**Step 7: Register in PopulateGlobalEntries** (in chromium/src)

In `side_panel_util.cc`, add:

```cpp
browser->browser_window_features()
    ->ai_panel_side_panel_coordinator()
    ->CreateAndRegisterEntry(window_registry);
```

**Step 8: Create coordinator in browser_window_features.cc** (in chromium/src)

Add coordinator member and creation.

**Step 9: Register WebUI config** (in chromium/src)

In `chrome_web_ui_configs.cc`:

```cpp
map.AddWebUIConfig(std::make_unique<AIPanelUIConfig>());
```

**Step 10: Commit**

```bash
git add src/chrome/browser/ui/views/side_panel/ai_panel/
git add src/chrome/browser/ui/webui/ai_panel/
git commit -m "feat: convert AI panel from standalone page to Chrome Side Panel"
```

---

## Task 7: Update Chromium build files and sync

Update BUILD.gn files to include all new sources, sync to chromium, and rebuild.

**Files:**
- Modify: `src/chrome/browser/ui/webui/ai_panel/BUILD.gn`
- Run: `sync-to-chromium.sh`
- Build: Chromium

**Step 1: Update BUILD.gn**

Add all source files including the new ones.

**Step 2: Sync to Chromium**

```bash
./sync-to-chromium.sh
```

**Step 3: Apply Chromium modifications**

Apply the changes from Task 6 Steps 5-9 directly in `chromium/src/`.

**Step 4: Generate build and compile**

```bash
cd chromium/src
gn gen out/Default
autoninja -C out/Default chrome
```

**Step 5: Commit**

```bash
git add src/chrome/browser/ui/webui/ai_panel/BUILD.gn
git commit -m "build: update BUILD.gn with all AI panel sources"
```

---

## Task 8: End-to-end testing

Test the full pipeline: Side Panel opens, connects to backend, calls AI, executes automation.

**Step 1: Start backend**

```bash
cd backend
python server.py
```

**Step 2: Start Ollama**

```bash
ollama serve
```

**Step 3: Launch Chromium**

```bash
chromium/src/out/Default/chrome.exe
```

**Step 4: Open Side Panel**

Click the side panel icon in the toolbar, select "AI Automation".

**Step 5: Test each provider**

1. Select Ollama -> type "Open Notepad and type hello" -> Execute
2. Select Anthropic (if key configured) -> type "Open calculator" -> Execute
3. Select OpenAI (if key configured) -> repeat

**Step 6: Verify**

- Side panel opens and renders correctly
- Provider dropdown shows all three providers
- Screen capture returns real screenshot
- AI returns action plans
- Executing actions controls the desktop

**Step 7: Commit**

```bash
git add -A
git commit -m "feat: complete side panel integration - all layers connected"
```

---

## Summary of Changes

| Task | What | Files Changed |
|------|------|---------------|
| 1 | Fix PNG encoding | screen_capture.cpp |
| 2 | C++ HTTP handler | ai_panel_handler.h/cc |
| 3 | Anthropic provider | anthropic_provider.js, manager, html, ui.cc |
| 4 | Replace JS stubs | ai_panel.js |
| 5 | Capture endpoint | server.py |
| 6 | Side Panel conversion | coordinator, CSS, UI, Chromium files |
| 7 | Build integration | BUILD.gn, sync, compile |
| 8 | E2E testing | All layers |
