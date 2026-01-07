# Setup Guide: Layer 2 Automation Service

Complete step-by-step guide to build and integrate the Windows automation service.

## Prerequisites

### 1. Install Visual Studio

**Download**: https://visualstudio.microsoft.com/downloads/

**Required workload**:
- Desktop development with C++

**Required components**:
- MSVC v142 or later (C++ compiler)
- Windows 10/11 SDK
- CMake tools for Windows (optional, or install separately)

### 2. Install CMake (if not included with VS)

**Download**: https://cmake.org/download/

Choose "Windows x64 Installer" and during installation:
- ✓ Add CMake to system PATH

**Verify installation**:
```cmd
cmake --version
```

### 3. Dependencies Already Included

✅ nlohmann/json header - Already downloaded to `third_party/nlohmann/json.hpp`
✅ Windows SDK libraries - Included with Visual Studio

---

## Quick Start (3 Simple Steps)

### Step 1: Build the Service

**Option A: Using the build script (Easiest)**

```cmd
cd automation_service
build.bat
```

**Option B: Manual build**

```cmd
cd automation_service
mkdir build
cd build

# Configure
cmake .. -G "Visual Studio 17 2022" -A x64

# Build
cmake --build . --config Release

# Output will be in: build/bin/Release/automation_service.exe
```

### Step 2: Register with Chrome

```cmd
cd automation_service
register-manifest.bat
```

This adds the service to Windows Registry so Chrome can find it.

### Step 3: Test the Service

```cmd
cd automation_service
test-service.bat
```

You should see JSON responses like:
```json
{"success":true,"message":"pong","version":"1.0.0"}
{"success":true,"capabilities":{...}}
```

---

## Troubleshooting

### Build Errors

**Error: "CMake not found"**
- Install CMake and ensure it's in PATH
- Or run from "Developer Command Prompt for VS"

**Error: "cl.exe not found"**
- Open "Developer Command Prompt for Visual Studio 2022"
- Or add Visual Studio to PATH:
  ```cmd
  "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat"
  ```

**Error: "Cannot open include file: 'nlohmann/json.hpp'"**
- Verify file exists at: `third_party/nlohmann/json.hpp`
- If missing, download it:
  ```cmd
  curl -L -o third_party/nlohmann/json.hpp https://raw.githubusercontent.com/nlohmann/json/develop/single_include/nlohmann/json.hpp
  ```

**Error: "Windows.h not found"**
- Install Windows 10/11 SDK via Visual Studio Installer

### Registration Errors

**Error: "Manifest not found"**
- Build the service first (Step 1)
- Check that `build/bin/manifest.json` exists

**Error: "Access denied" when registering**
- Run cmd as Administrator
- Or use HKEY_CURRENT_USER (which doesn't require admin)

### Test Errors

**Service exits immediately**
- This is normal! The service waits for input from Chrome
- When testing via echo, it should print a response and exit

**No output from test**
- Check that you're in Release mode, not Debug
- Try running the EXE directly:
  ```cmd
  echo {"action":"ping"} | build\bin\Release\automation_service.exe
  ```

---

## Verifying Installation

### 1. Check Build Output

```cmd
dir build\bin\Release
```

Should show:
- `automation_service.exe` (~100KB+)
- `manifest.json`

### 2. Check Registry

Open Registry Editor (regedit) and navigate to:
```
HKEY_CURRENT_USER\Software\Google\Chrome\NativeMessagingHosts\com.browser_ai.automation
```

The (Default) value should point to your manifest.json file.

### 3. Check Manifest Content

Open `build/bin/manifest.json`:

```json
{
  "name": "com.browser_ai.automation",
  "description": "Browser AI Automation Service",
  "path": "C:\\full\\path\\to\\automation_service.exe",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://INSERT_EXTENSION_ID/",
    "chrome://ai-panel/"
  ]
}
```

The `path` should be an absolute Windows path to the EXE.

---

## Integration with Browser (Layer 1)

Once the service is built and registered, update the browser code:

### Update `local_llm_provider.js`

Find the `sendNativeMessage` function and replace the stub:

```javascript
async sendNativeMessage(message) {
  return new Promise((resolve, reject) => {
    // Real implementation (replace the stub)
    chrome.runtime.sendNativeMessage(
      'com.browser_ai.automation',
      message,
      response => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          resolve(response);
        }
      }
    );
  });
}
```

### Test End-to-End

1. Build Chromium with AI Panel (see main README.md)
2. Navigate to `chrome://ai-panel`
3. Click "Preview Screen" button
4. You should see your actual desktop screenshot!

---

## Advanced Configuration

### UIAccess for Elevated Windows

To control elevated (admin) windows:

1. **Code sign your EXE** with a trusted certificate
2. **Update manifest** to request UIAccess:
   ```xml
   <requestedExecutionLevel level="asInvoker" uiAccess="true" />
   ```
3. **Install to trusted location** (Program Files)

For development, run Chrome as admin (not recommended for regular use).

### Custom Logging

Redirect service logs to a file:

```cmd
build\bin\Release\automation_service.exe 2> service.log
```

View logs in real-time:
```cmd
powershell Get-Content service.log -Wait
```

---

## Next Steps

After successful setup:

1. ✅ **Test basic automation** - Capture screen, inspect UI
2. ✅ **Add OpenAI API key** - In browser settings
3. ✅ **Try automation commands** - "Open Notepad and type Hello"
4. 🚀 **Automate your workflow!**

---

## Getting Help

If you encounter issues:

1. **Check the logs** - Service logs to stderr
2. **Test standalone** - Use `test-service.bat`
3. **Verify registry** - Check the manifest path
4. **Check Chrome console** - F12 > Console for errors
5. **Review README.md** - Full technical details

## Clean Rebuild

If things get messed up:

```cmd
cd automation_service
rmdir /s /q build
build.bat
register-manifest.bat
```

This removes the build directory and starts fresh.

