# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Browser-ai is a Chromium-based browser with AI-powered desktop automation. The system has three layers:

1. **Browser UI (Layer 1)** - Chrome WebUI at `chrome://ai-panel` with JavaScript AI providers
2. **Automation Service (Layer 2)** - C++ Windows service for screen capture, UI inspection, and input control
3. **AI Backend (Layer 3)** - Python Flask proxy supporting OpenAI GPT-4 Vision and Ollama (local)

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

### Python Backend
```bash
cd backend
pip install -r requirements.txt
cp env-template.txt .env  # Then edit with API keys
python server.py          # Runs on http://localhost:5000
```

### Chromium Build (optional, for full integration)
```bash
./sync-to-chromium.sh     # Copy custom files to chromium/src
cd chromium/src
gn gen out/Default
autoninja -C out/Default chrome
```

## Testing

### Layer 1 (Browser UI) - No build required
```bash
cd test
./run-test-server.sh
# Open http://localhost:8000/test/layer1-test.html (36+ unit tests)
# Open http://localhost:8000/test/simple-demo.html (interactive demo)
```

### Layer 2 (Automation Service)
```bash
cd automation_service
python test_ping.py        # Basic connectivity
python test_automation.py  # Full capabilities (screen capture, input, UI inspection)
```

### Layer 3 (Backend)
```bash
# Terminal 1: Start server
cd backend && python server.py

# Terminal 2: Run tests
cd backend
python test_backend.py     # Health checks
python test_e2e.py         # Full integration
```

### Full E2E Test (all layers)
```bash
# Terminal 1: Backend
cd backend && python server.py

# Terminal 2: Ollama (if using local AI)
ollama serve

# Terminal 3: E2E test
cd test
python test_ai_automation.py   # Opens Notepad, AI types text
python demo_automation.py      # Quick automation demo (no AI)
```

## Architecture

```
Browser (chrome://ai-panel)
    ↓ WebUI Bridge (chrome.send())
C++ WebUI Handler (ai_panel_handler.cc)
    ↓ HTTP
Python Backend (server.py)
    ↓ Subprocess + Native Messaging
C++ Automation Service (automation_service.exe)
    ↓ Windows API
Desktop (UIAutomation, DXGI, SendInput)
```

### Key Directories

- `src/chrome/browser/ui/webui/ai_panel/` - Chrome WebUI (HTML/CSS/JS + C++ handlers)
- `automation_service/src/` - C++ automation service
  - `action_executor.cpp` - Main orchestrator
  - `native_messaging.cpp` - Chrome protocol handler
  - `ui_automation.cpp` - Windows UIAutomation wrapper
  - `screen_capture.cpp` - GPU-accelerated capture (DXGI/D3D11)
  - `input_controller.cpp` - Mouse/keyboard via SendInput
- `backend/` - Python AI proxy
  - `server.py` - Flask server with provider routing

### AI Provider System

JavaScript providers in `src/.../resources/`:
- `ai_provider_interface.js` - Base class
- `ai_provider_manager.js` - Provider registry and switching
- `openai_provider.js`, `ollama_provider.js`, `local_llm_provider.js`

To add a new provider: extend `AIProvider` class, register with `AIProviderManager`, add backend handler in `server.py`.

### Native Messaging Protocol

JSON over stdin/stdout with Chrome's 4-byte length prefix:
```json
{"action": "capture_screen"}
{"action": "execute_action", "params": {"action": "click", "params": {"x": 100, "y": 200}}}
{"action": "inspect_ui"}
```

## Development Workflow

Two options for Chromium files:
1. **Direct**: Edit in `chromium/src/`, then `./sync-from-chromium.sh` to save changes
2. **Tracked**: Edit in `src/`, then `./sync-to-chromium.sh` to copy to Chromium

Layer 1 + 2 can be tested without building Chromium using `test/layer1-test.html`.

## Dependencies

- **C++**: Windows SDK (UIAutomation, D3D11, DXGI), nlohmann/json (header-only in third_party/)
- **Python**: Flask, Flask-CORS, requests, python-dotenv
- **AI**: OpenAI API key OR Ollama with `llava` model

## Configuration

- `backend/.env` - API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, OLLAMA_MODEL)
- `automation_service/manifest.json.in` - Native Messaging manifest template
- `src/.../BUILD.gn` - Chromium build integration
