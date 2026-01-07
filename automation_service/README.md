# Browser AI Automation Service

Native Windows automation service for the Browser AI project. Provides desktop automation capabilities via Native Messaging protocol.

## Features

- **UIAutomation**: Inspect and interact with UI elements
- **Screen Capture**: GPU-accelerated screen capture via Desktop Duplication API
- **Input Control**: Mouse and keyboard input injection via SendInput
- **Native Messaging**: Communication with browser using Chrome's Native Messaging protocol

## Building

### Prerequisites

- Windows 10/11
- Visual Studio 2019 or later (with C++ desktop development)
- CMake 3.20 or later
- Windows SDK 10.0 or later

### Dependencies

The project requires:
- **UIAutomationCore.lib** - Windows UI Automation (included in Windows SDK)
- **D3D11.lib** - Direct3D 11 (included in Windows SDK)
- **DXGI.lib** - DirectX Graphics Infrastructure (included in Windows SDK)
- **windowscodecs.lib** - Windows Imaging Component (included in Windows SDK)
- **nlohmann/json** - JSON library (header-only, included in third_party/)

### Build Steps

```bash
# Create build directory
cd automation_service
mkdir build
cd build

# Generate Visual Studio project
cmake ..

# Build
cmake --build . --config Release

# Or open automation_service.sln in Visual Studio and build
```

### Output

Built executable: `build/bin/automation_service.exe`
Manifest: `build/bin/manifest.json`

## Installation

### 1. Build the Service

Follow the build steps above.

### 2. Register Native Messaging Host

The service must be registered in Windows Registry:

```reg
Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\Software\Google\Chrome\NativeMessagingHosts\com.browser_ai.automation]
@="C:\\path\\to\\automation_service\\build\\bin\\manifest.json"
```

Or use PowerShell:

```powershell
$manifestPath = "C:\path\to\automation_service\build\bin\manifest.json"
New-Item -Path "HKCU:\Software\Google\Chrome\NativeMessagingHosts\com.browser_ai.automation" -Force
Set-ItemProperty -Path "HKCU:\Software\Google\Chrome\NativeMessagingHosts\com.browser_ai.automation" -Name "(Default)" -Value $manifestPath
```

### 3. Test the Service

```bash
# Test stdin/stdout communication
echo {"action":"ping"} | automation_service.exe
# Should output: {"success":true,"message":"pong","version":"1.0.0"}
```

## Architecture

### Component Overview

```
┌─────────────────────┐
│   Browser (WebUI)   │
│   Layer 1          │
└──────────┬──────────┘
           │ Native Messaging
           │ (JSON over stdin/stdout)
           ▼
┌─────────────────────┐
│  Native Messaging   │
│  Protocol Handler   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Action Executor    │
│  (Orchestrator)     │
└─┬─────────┬─────────┘
  │         │         
  ▼         ▼         
┌────┐   ┌────┐   ┌──────┐
│UI  │   │Screen  │Input │
│Auto│   │Capture │Ctrl  │
└────┘   └────┘   └──────┘
```

### Message Protocol

**Request Format:**
```json
{
  "action": "action_name",
  "params": { ... }
}
```

**Response Format:**
```json
{
  "success": true/false,
  "error": "error message if failed",
  ... action-specific data ...
}
```

### Supported Actions

#### get_capabilities
Get service capabilities.

```json
Request: {"action": "get_capabilities"}
Response: {
  "success": true,
  "capabilities": {
    "screen_capture": true,
    "ui_automation": true,
    "input_control": true,
    "local_llm": false
  }
}
```

#### capture_screen
Capture current screen.

```json
Request: {"action": "capture_screen"}
Response: {
  "success": true,
  "screenshot": "base64_png_data",
  "width": 1920,
  "height": 1080
}
```

#### inspect_ui
Get UI tree.

```json
Request: {"action": "inspect_ui"}
Response: {
  "success": true,
  "uiTree": {
    "name": "Desktop",
    "type": "Window",
    "bounds": {...},
    "children": [...]
  }
}
```

#### execute_action
Execute a single automation action.

```json
Request: {
  "action": "execute_action",
  "params": {
    "action": "click",
    "params": {"x": 100, "y": 200, "button": "left"}
  }
}
```

#### execute_actions
Execute multiple actions sequentially.

```json
Request: {
  "action": "execute_actions",
  "params": {
    "actions": [
      {"action": "click", "params": {"x": 100, "y": 200}},
      {"action": "type", "params": {"text": "Hello"}},
      {"action": "wait", "params": {"ms": 1000}}
    ]
  }
}
```

### Action Types

- **click**: `{"x": int, "y": int, "button": "left"|"right"|"middle", "double": bool}`
- **type**: `{"text": string}`
- **scroll**: `{"delta": int, "x": int, "y": int}`
- **press_keys**: `{"keys": ["ctrl", "s"]}`
- **wait**: `{"ms": int}`

## Security Considerations

### UIAccess

For production, the service should be code-signed and have UIAccess enabled to control elevated windows:

```xml
<trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
  <security>
    <requestedPrivileges>
      <requestedExecutionLevel level="asInvoker" uiAccess="true" />
    </requestedPrivileges>
  </security>
</trustInfo>
```

Requirements for UIAccess:
1. Application must be signed with a certificate from a trusted CA
2. Application must be installed in a trusted location (Program Files)
3. Manifest must request UIAccess=true

### Permissions

The service can:
- ✓ Read screen contents
- ✓ Inspect UI elements of any application
- ✓ Control mouse and keyboard
- ✓ Access clipboard (if implemented)

**Recommendation**: Only run the service when actively using automation features.

## Troubleshooting

### Service doesn't start

- Check that manifest.json path in registry is correct
- Verify automation_service.exe exists at the path specified in manifest
- Check Windows Event Viewer for errors

### Screen capture fails

- Ensure Desktop Duplication API is supported (Windows 8+)
- Check that display drivers are up to date
- Verify application has access to display (not blocked by DRM)

### Input injection doesn't work

- Some games block SendInput with anti-cheat
- Elevated windows require UIAccess (see Security section)
- Check that foreground window is not blocking input

### UI Automation fails

- Not all applications expose UI elements via UIAutomation
- Custom controls may not be accessible
- Try running application in compatibility mode

## Development

### Adding New Actions

1. Add action type to `ActionType` enum in `common.h`
2. Add handler method in `ActionExecutor`
3. Register handler in `main.cpp`
4. Update protocol documentation

### Debugging

- The service logs to stderr
- To capture logs, redirect stderr: `automation_service.exe 2> debug.log`
- Use Visual Studio debugger to attach to running process

## License

BSD License (same as Chromium)

## Related Projects

- [Chromium](https://www.chromium.org/) - Browser platform
- [nlohmann/json](https://github.com/nlohmann/json) - JSON library
- [Windows UI Automation](https://docs.microsoft.com/en-us/windows/win32/winauto/entry-uiauto-win32)

