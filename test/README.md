# Layer 1 Verification Tests

This directory contains standalone tests for verifying the browser-side AI provider architecture without requiring a full Chromium build.

## Quick Start

### Option 1: Using the Test Server (Recommended)

```bash
# From the browser-ai directory
cd test
chmod +x run-test-server.sh
./run-test-server.sh
```

Then open your browser to: **http://localhost:8000/test/layer1-test.html**

### Option 2: Using VS Code Live Server

1. Install "Live Server" extension in VS Code
2. Right-click on `test/layer1-test.html`
3. Select "Open with Live Server"

### Option 3: Manual Server

```bash
# Python 3
cd browser-ai
python3 -m http.server 8000

# Or Python 2
python -m SimpleHTTPServer 8000

# Or PHP
php -S localhost:8000

# Or Node.js (if you have http-server installed)
npx http-server -p 8000
```

Then navigate to: http://localhost:8000/test/layer1-test.html

## What Gets Tested

The test suite verifies:

### 1. AIProvider Base Class
- ✓ Provider initialization with name and API key requirement
- ✓ API key management (set, retrieve)
- ✓ Configuration state checking
- ✓ Capabilities reporting
- ✓ Abstract method enforcement

### 2. OpenAI Provider
- ✓ Correct configuration (name, endpoint, model)
- ✓ API key requirement
- ✓ Vision support capabilities
- ✓ Action validation (click, type, scroll, etc.)
- ✓ Invalid action rejection
- ✓ Cost estimation

### 3. Local LLM Provider
- ✓ Privacy-focused configuration
- ✓ No API key requirement
- ✓ Availability checking (stub)
- ✓ Action validation with appropriate confidence scores

### 4. AI Provider Manager
- ✓ Provider registration (OpenAI, Local LLM)
- ✓ Provider listing and discovery
- ✓ Active provider selection
- ✓ Provider switching
- ✓ API key configuration
- ✓ Conversation history management

### 5. UI Integration
- ✓ CSS stylesheet loading
- ✓ Style application to UI elements
- ✓ Component rendering

## Test Output

The test page displays:

1. **Test Results** - Detailed pass/fail for each test
2. **Interactive Demo** - The actual AI Panel UI running in standalone mode
3. **Console Logs** - Detailed test execution logs in browser console

### Expected Results

```
=== Test Summary ===
Tests Run: 30+
Tests Passed: 30+
Tests Failed: 0
```

## Known Limitations

These tests verify the **browser-side JavaScript architecture** only. They do NOT test:

- ❌ C++ WebUI integration (requires Chromium build)
- ❌ Native Messaging communication
- ❌ Actual automation service (Layer 2)
- ❌ Real screen capture and UI inspection
- ❌ Actual AI API calls (uses stubs)

To test those components, you'll need to:
1. Build Chromium with the AI Panel integrated (see main README)
2. Implement Layer 2 (C++ automation service)
3. Run end-to-end tests with real automation

## Troubleshooting

### Test page shows errors

**Problem**: "Cannot load ai_panel.css" or scripts fail to load

**Solution**: You MUST serve the files via HTTP (not file://). Use one of the server options above.

### Some tests fail

**Problem**: Tests report failures

**Solution**: 
1. Check browser console for detailed error messages
2. Ensure all `.js` files in `src/chrome/browser/ui/webui/ai_panel/resources/` are present
3. Try a different browser (Chrome/Edge recommended)
4. Clear browser cache and reload

### Demo UI doesn't render

**Problem**: "Interactive Demo" section is empty

**Solution**: 
1. Check browser console for fetch errors
2. Ensure server is serving from the correct directory (browser-ai root)
3. Try opening directly: http://localhost:8000/src/chrome/browser/ui/webui/ai_panel/resources/ai_panel.html

## Next Steps After Verification

Once Layer 1 tests pass:

1. **Integrate into Chromium** - Update BUILD.gn and register WebUI (see main README)
2. **Build Chromium** - Compile with your AI Panel integrated
3. **Test in Chromium** - Navigate to `chrome://ai-panel`
4. **Build Layer 2** - Implement C++ automation service
5. **End-to-end testing** - Test actual desktop automation

## Contributing

If you find issues with the tests or want to add more test coverage, please submit a PR!

