# browser-ai

A Chromium-based browser with integrated AI-powered desktop automation.

## Overview

Browser-ai adds an AI automation panel to Chromium that can see your screen, understand UI elements, and execute desktop actions. The system uses a two-process architecture: the browser communicates with a C++ automation service over Native Messaging. All AI provider logic, credential storage, and async request handling run in the C++ service — no Python backend required.

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

## Project Structure

```
src/                                    # Mirrored chromium/src structure
└── chrome/browser/ui/
    ├── webui/ai_panel/                 # AI Panel WebUI
    │   ├── ai_panel_ui.h / .cc
    │   ├── ai_panel_handler.h / .cc
    │   └── resources/
    │       ├── ai_panel.html
    │       ├── ai_panel.css
    │       ├── ai_panel.js             # UI controller
    │       ├── ai_provider_manager.js  # Thin provider client
    │       └── native_messaging_helper.js  # Native Messaging transport
    └── views/side_panel/              # Side panel integration

automation_service/                     # C++ automation service
├── src/
│   ├── main.cpp                       # Entry point, handler registration
│   ├── action_executor.cpp/.h         # Main orchestrator
│   ├── native_messaging.cpp/.h        # Chrome Native Messaging protocol
│   ├── screen_capture.cpp/.h          # GPU-accelerated capture (DXGI/D3D11)
│   ├── ui_automation.cpp/.h           # Windows UIAutomation wrapper
│   ├── input_controller.cpp/.h        # Mouse/keyboard via SendInput
│   ├── credential_store.cpp/.h        # Windows Credential Manager for API keys
│   ├── http_client.cpp/.h             # WinHTTP wrapper for API calls
│   ├── ai_provider.cpp/.h             # OpenAI, Anthropic, Ollama routing
│   ├── async_request.cpp/.h           # Background thread + polling
│   └── common.h                       # Shared types and utilities
├── CMakeLists.txt
├── test_ping.py                       # Basic connectivity test
├── test_automation.py                 # Full capabilities test
└── test_new_handlers.py               # AI provider and credential tests

sync-to-chromium.sh                    # Copy files to chromium/src
sync-from-chromium.sh                  # Copy changes back from chromium/src
```

## Features

- **AI-Powered Desktop Automation**: Describe what you want done; the AI analyzes your screen and executes actions
- **Three AI Providers**: OpenAI GPT-4o, Anthropic Claude Sonnet 4, and Ollama (local/private)
- **Secure Credential Storage**: API keys stored in Windows Credential Manager (OS-encrypted, per-user)
- **Async Request Pipeline**: AI requests run on a background thread; browser polls for results
- **Screen Capture**: GPU-accelerated via DXGI Desktop Duplication
- **UI Inspection**: Windows UIAutomation tree for element-aware clicking
- **Input Control**: Mouse clicks, keyboard typing, scroll, key combos via SendInput
- **Action Preview**: Review AI-planned actions before execution

## Quick Start

### 1. Build the Automation Service

```bash
cd automation_service
mkdir build && cd build
cmake ..
cmake --build . --config Release
```

### 2. Register with Chrome

```bash
automation_service/register-manifest.bat
```

### 3. Configure AI Provider

- **Ollama (local, free)**: Install [Ollama](https://ollama.com), run `ollama pull llava && ollama serve`
- **OpenAI / Anthropic**: Enter your API key in the browser panel Settings

### 4. Run

Navigate to `chrome://ai-panel` (requires Chromium build) or use the test harness:

```bash
cd test
./run-test-server.sh
# Open http://localhost:8000/test/layer1-test.html
```

## Testing

### Browser UI (no build required)
```bash
cd test && ./run-test-server.sh
# Open http://localhost:8000/test/layer1-test.html (36+ unit tests)
# Open http://localhost:8000/test/simple-demo.html (interactive demo)
```

### Automation Service
```bash
cd automation_service
python test_ping.py              # Basic connectivity
python test_automation.py        # Screen capture, input, UI inspection
python test_new_handlers.py      # AI providers, credentials, async requests
```

### Full E2E
```bash
# Terminal 1 (if using Ollama):
ollama serve

# Terminal 2:
cd test
python test_ai_automation.py     # AI-driven Notepad automation
python demo_automation.py        # Quick automation demo (no AI)
```

## Native Messaging Protocol

JSON over stdin/stdout with Chrome's 4-byte length prefix:

| Action | Description |
|--------|-------------|
| `ping` | Health check |
| `get_capabilities` | List available features |
| `capture_screen` | Screenshot as base64 PNG |
| `inspect_ui` | UIAutomation tree as JSON |
| `execute_action` | Run a single action (click, type, etc.) |
| `execute_actions` | Run multiple actions sequentially |
| `check_local_llm` | Check if Ollama is running locally |
| `get_actions` | Submit async AI request (returns `request_id`) |
| `poll` | Check async request status |
| `cancel` | Cancel async request |
| `store_api_key` | Save API key to Windows Credential Manager |
| `delete_api_key` | Remove stored API key |
| `get_provider_status` | Check which providers are configured/available |

## Dependencies

- **Build**: CMake 3.20+, MSVC (Visual Studio 2022)
- **Runtime**: Windows 10+ (for DXGI, UIAutomation, WinHTTP, Credential Manager)
- **AI**: OpenAI API key, Anthropic API key, or [Ollama](https://ollama.com) with `llava` model
- **Optional**: Chromium source + depot_tools (for full browser integration)

## Chromium Integration (Optional)

For full `chrome://ai-panel` integration:

```bash
./sync-to-chromium.sh
cd chromium/src
gn gen out/Default
autoninja -C out/Default chrome
```

See `docs/plans/` for detailed integration guides.

## Development Workflow

1. **Edit** in `src/` (tracked) or `chromium/src/` (direct)
2. **Sync** with `./sync-to-chromium.sh` or `./sync-from-chromium.sh`
3. **Build** the automation service with CMake
4. **Test** with the Python test scripts

## Roadmap

- [x] AI Panel WebUI
- [x] Side panel integration
- [x] Desktop automation (screen capture, UI inspection, input control)
- [x] AI provider routing (OpenAI, Anthropic, Ollama)
- [x] Secure credential storage (Windows Credential Manager)
- [x] Async AI request pipeline
- [x] Eliminate Python backend dependency
- [ ] Streaming AI responses
- [ ] Multi-monitor support
- [ ] Keyboard shortcuts for panel access
- [ ] Panel theming

## License

This project is based on Chromium, which is licensed under the BSD license. The AI panel code follows the same license.
