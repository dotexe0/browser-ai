# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Browser-ai is a Chromium-based browser with AI-powered desktop automation. The system has two layers:

1. **Browser UI** - Chrome WebUI at `chrome://ai-panel` with thin JavaScript client
2. **Automation Service** - C++ Windows service handling screen capture, UI inspection, input control, AI provider routing, credential storage, and async request management

## Build Commands

### C++ Automation Service
```bash
cd automation_service
mkdir build && cd build
cmake ..
cmake --build . --config Release
# Output: build/bin/Release/automation_service.exe
```
Or use the convenience script: `automation_service/build.bat`

After building, register with Chrome:
```bash
automation_service/register-manifest.bat
```

### Chromium Build (optional, for full integration)
```bash
./sync-to-chromium.sh     # Copy custom files to chromium/src
cd chromium/src
gn gen out/Default
autoninja -C out/Default chrome
```

## Testing

### Browser UI - No build required
```bash
cd test
./run-test-server.sh
# Open http://localhost:8000/test/layer1-test.html (36+ unit tests)
# Open http://localhost:8000/test/simple-demo.html (interactive demo)
```

### Automation Service
```bash
cd automation_service
python test_ping.py              # Basic connectivity
python test_automation.py        # Full capabilities (screen capture, input, UI inspection)
python test_new_handlers.py      # AI providers, credentials, async requests
```

### Full E2E Test
```bash
# Terminal 1: Ollama (if using local AI)
ollama serve

# Terminal 2: E2E test
cd test
python test_ai_automation.py   # Opens Notepad, AI types text
python demo_automation.py      # Quick automation demo (no AI)
```

## Architecture

```
Browser (chrome://ai-panel)
    | Native Messaging (stdin/stdout JSON)
C++ Automation Service (automation_service.exe)
    |-- Screen Capture (DXGI/D3D11)
    |-- Input Control (SendInput)
    |-- UI Inspection (UIAutomation)
    |-- AI Providers (OpenAI, Anthropic, Ollama via WinHTTP)
    |-- Credential Store (Windows Credential Manager)
    +-- Async Requests (background thread + polling)
```

### Key Directories

- `src/chrome/browser/ui/webui/ai_panel/` - Chrome WebUI (HTML/CSS/JS + C++ handlers)
- `automation_service/src/` - C++ automation service
  - `action_executor.cpp` - Main orchestrator
  - `native_messaging.cpp` - Chrome protocol handler
  - `ui_automation.cpp` - Windows UIAutomation wrapper
  - `screen_capture.cpp` - GPU-accelerated capture (DXGI/D3D11)
  - `input_controller.cpp` - Mouse/keyboard via SendInput
  - `credential_store.cpp` - Windows Credential Manager for API keys
  - `http_client.cpp` - WinHTTP wrapper for AI API calls
  - `ai_provider.cpp` - OpenAI, Anthropic, Ollama routing
  - `async_request.cpp` - Background thread + polling for AI requests

### AI Provider System

The C++ automation service handles all AI provider logic:
- `ai_provider.cpp` - Routes requests to OpenAI (GPT-4o), Anthropic (Claude Sonnet 4), or Ollama (llava)
- `credential_store.cpp` - Stores API keys in Windows Credential Manager (encrypted by OS)
- `async_request.cpp` - Runs AI calls on a background thread, browser polls for results

Browser JavaScript is a thin client:
- `native_messaging_helper.js` - Native Messaging transport
- `ai_provider_manager.js` - Thin wrapper for provider selection and async polling
- `ai_panel.js` - UI controller

### Native Messaging Protocol

JSON over stdin/stdout with Chrome's 4-byte length prefix:
```json
{"action": "capture_screen"}
{"action": "execute_action", "params": {"action": "click", "params": {"x": 100, "y": 200}}}
{"action": "inspect_ui"}
{"action": "get_actions", "provider": "openai", "user_request": "Open Notepad"}
{"action": "poll", "request_id": "abc12345"}
{"action": "store_api_key", "provider": "openai", "api_key": "sk-..."}
{"action": "get_provider_status"}
```

## Development Workflow

Two options for Chromium files:
1. **Direct**: Edit in `chromium/src/`, then `./sync-from-chromium.sh` to save changes
2. **Tracked**: Edit in `src/`, then `./sync-to-chromium.sh` to copy to Chromium

Browser UI + Automation Service can be tested without building Chromium using `test/layer1-test.html`.

## Dependencies

- **C++**: Windows SDK (UIAutomation, D3D11, DXGI, WinHTTP, wincred.h), nlohmann/json (header-only in third_party/)
- **AI**: OpenAI API key OR Anthropic API key OR Ollama with `llava` model

## Configuration

- API keys are stored in Windows Credential Manager (managed via the Settings panel or `store_api_key` action)
- `automation_service/manifest.json.in` - Native Messaging manifest template
- `src/.../BUILD.gn` - Chromium build integration
