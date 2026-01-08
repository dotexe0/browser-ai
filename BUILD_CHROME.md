# 🔨 Building Chromium with AI Panel

## Prerequisites
- ✅ Visual Studio 2022 installed
- ✅ Chromium source checked out
- ✅ AI Panel files synced to chromium/src

## Build Steps

### Option 1: Full Build (First Time)

```bash
# Navigate to Chromium source
cd A:\browser-ai\chromium\src

# Configure build (one-time setup)
gn gen out\Default

# Build Chrome (will take 30-60 minutes first time)
autoninja -C out\Default chrome
```

### Option 2: Incremental Build (After Changes)

```bash
# Navigate to Chromium source
cd A:\browser-ai\chromium\src

# Build only changed files (much faster, 1-5 minutes)
autoninja -C out\Default chrome
```

### Option 3: Debug Build

```bash
# Navigate to Chromium source
cd A:\browser-ai\chromium\src

# Configure for debug (one-time)
gn gen out\Debug --args="is_debug=true"

# Build debug Chrome
autoninja -C out\Debug chrome
```

## Launch Chrome with AI Panel

### After Build Completes:

```bash
# Launch Release build
A:\browser-ai\chromium\src\out\Default\chrome.exe

# Or launch Debug build
A:\browser-ai\chromium\src\out\Debug\chrome.exe
```

### Access AI Panel:

The AI Panel should be accessible depending on how you integrated it:

**Option A: Side Panel**
- Look in browser side panel (right side)
- Or go to `chrome://ai-panel`

**Option B: WebUI**
- Navigate to `chrome://ai-panel`

## Build Configuration

### Minimal Build (Faster):

If you want a faster build, create a custom build config:

```bash
cd A:\browser-ai\chromium\src

# Create custom config
gn gen out\Fast --args="
  is_debug=false
  is_component_build=true
  symbol_level=0
  enable_nacl=false
  blink_symbol_level=0
"

# Build
autoninja -C out\Fast chrome
```

### Full Release Build:

```bash
cd A:\browser-ai\chromium\src

# Create release config
gn gen out\Release --args="
  is_debug=false
  is_official_build=true
  is_component_build=false
"

# Build (will take longest)
autoninja -C out\Release chrome
```

## Troubleshooting

### Build Errors:

**Error: "gn not found"**
```bash
# Add depot_tools to PATH
set PATH=A:\browser-ai\chromium\depot_tools;%PATH%
```

**Error: "autoninja not found"**
```bash
# Use ninja directly
ninja -C out\Default chrome
```

**Error: "Out of disk space"**
- Chromium build needs ~50GB free space
- Clean old builds: `rmdir /s /q out\Default`

**Error: "Missing dependencies"**
```bash
# Re-run gclient sync
gclient sync
```

### Incremental Build Not Working:

```bash
# Force clean build
autoninja -C out\Default -t clean
autoninja -C out\Default chrome
```

## Verify Build

After build completes, verify:

```bash
# Check exe exists
dir A:\browser-ai\chromium\src\out\Default\chrome.exe

# Check version
A:\browser-ai\chromium\src\out\Default\chrome.exe --version
```

## Expected Build Times

| Build Type | First Time | Incremental |
|------------|------------|-------------|
| Full Release | 45-90 min | 3-10 min |
| Debug | 30-60 min | 2-5 min |
| Component | 20-40 min | 1-3 min |

*Times vary based on CPU cores and disk speed*

## Current Status

**Files Synced**:
- ✅ `chrome/browser/ui/webui/ai_panel/resources/ai_panel.html`
- ✅ `chrome/browser/ui/webui/ai_panel/resources/ai_panel.css`
- ✅ `chrome/browser/ui/webui/ai_panel/resources/ai_panel.js`
- ✅ `chrome/browser/ui/webui/ai_panel/resources/ai_provider_interface.js`
- ✅ `chrome/browser/ui/webui/ai_panel/resources/openai_provider.js`
- ✅ `chrome/browser/ui/webui/ai_panel/resources/local_llm_provider.js`
- ✅ `chrome/browser/ui/webui/ai_panel/resources/ollama_provider.js`
- ✅ `chrome/browser/ui/webui/ai_panel/resources/ai_provider_manager.js`
- ⏸️ `chrome/browser/ui/webui/ai_panel/resources/native_messaging_helper.js` (not included yet)

**Build Type**: Simulation Mode (Layer 1 only)
- UI fully functional
- Provider management works
- Simulated screen capture
- Simulated action execution
- Perfect for testing UI/UX!

## After Build: What Works

### Layer 1 (Browser UI) - FULLY FUNCTIONAL:
✅ Provider selection (OpenAI, Ollama, Local LLM)
✅ API key management
✅ Settings panel
✅ Request input
✅ Simulated screen preview
✅ Simulated action planning
✅ Execution log
✅ Status indicators
✅ All UI elements and styling

### Not Yet Connected:
⏸️ Real screen capture (needs Native Messaging)
⏸️ Real automation execution (needs Native Messaging)
⏸️ Backend API integration (needs integration code)

**This is perfect for**:
- Testing the UI/UX
- Trying the provider switching
- Seeing the visual design
- Verifying the flow
- Demonstrating the concept

## Next Steps After Testing UI

Once you're happy with the UI, we can:

1. Re-add Native Messaging integration
2. Connect to backend API
3. Wire real screen capture
4. Enable real action execution
5. Test full end-to-end flow

---

**Ready to build!** 🚀

Run: `cd A:\browser-ai\chromium\src && autoninja -C out\Default chrome`

