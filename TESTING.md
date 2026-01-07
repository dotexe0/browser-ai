# 🧪 Testing Guide: Browser AI

Complete guide to testing all components of your Atlas-like automation system.

---

## 📋 Quick Test Summary

| Test Level | Time | What It Tests | Command |
|------------|------|---------------|---------|
| **Level 1** | 30 sec | Service health | `python test_ping.py` |
| **Level 2** | 1 min | Automation features | `python test_automation.py` |
| **Level 3** | 2 min | Browser UI | Open browser to localhost:8000 |
| **Level 4** | 5+ min | End-to-end | Full automation workflow |

---

## ✅ Level 1: Service Health Check

**What it tests:** Native Messaging protocol, basic service functionality

**Location:** `automation_service/`

**Command:**
```bash
cd automation_service
python test_ping.py
```

**Expected Output:**
```
============================================================
Testing Browser AI Automation Service
============================================================

Test 1: Ping
------------------------------------------------------------
Sending: {"action": "ping"}
Response: {
  "message": "pong",
  "success": true,
  "version": "1.0.0"
}

Test 2: Get Capabilities
------------------------------------------------------------
Sending: {"action": "get_capabilities"}
Response: {
  "capabilities": {
    "input_control": true,
    "local_llm": false,
    "screen_capture": true,
    "ui_automation": true
  },
  "success": true
}

============================================================
Tests complete!
============================================================
```

**Pass Criteria:** ✅ Both tests return `"success": true`

---

## ✅ Level 2: Automation Features

**What it tests:** Screen capture, UI inspection, input control

**Location:** `automation_service/`

**Command:**
```bash
cd automation_service
python test_automation.py
```

**Expected Output:**
```
======================================================================
Testing Browser AI Automation Features
======================================================================

Test 1: Capture Screen
----------------------------------------------------------------------
[OK] SUCCESS!
   Screen Size: 1920x1080 (your resolution)
   Image Data Size: 2,345,678 bytes (2.24 MB)
   Format: PNG (base64 encoded)
   Saved to: A:\browser-ai\automation_service\screenshot.png

Test 2: Inspect UI (Desktop)
----------------------------------------------------------------------
[OK] SUCCESS!
   Root Element: Desktop
   Children: 15
   First few elements:
     1. Taskbar (Pane)
     2. Program Manager (Pane)
     3. Chrome (Window)
     ... and 12 more

Test 3: Execute Mouse Move Action
----------------------------------------------------------------------
[OK] SUCCESS!
   Mouse moved to (100, 100)

======================================================================
Automation tests complete!
======================================================================
```

**Pass Criteria:** 
- ✅ Screen capture succeeds with image data > 0 bytes
- ✅ screenshot.png file is created
- ✅ UI tree has children
- ✅ Mouse move succeeds

**Note:** If tests fail:
- Screen capture may need DWM (Desktop Window Manager) access
- Try running terminal as Administrator for full access
- UI inspection works best when not running under restrictions

---

## ✅ Level 3: Browser UI Test

**What it tests:** Complete Layer 1 browser architecture

**Location:** `test/`

### Step 1: Start Test Server

```bash
cd test
./run-test-server.sh
```

Or manually:
```bash
python -m http.server 8000
```

### Step 2: Open Browser

Open any web browser (Chrome, Edge, Firefox) and navigate to:

```
http://localhost:8000/test/layer1-test.html
```

### Step 3: Watch Tests Run

The page will automatically run 30+ tests:

**Test Categories:**
1. ✅ AI Provider Interface (5 tests)
2. ✅ OpenAI Provider (3 tests)
3. ✅ Local LLM Provider (3 tests)
4. ✅ AI Provider Manager (4 tests)
5. ✅ UI Rendering (15+ tests)
   - Settings panel
   - Provider selection
   - API key management
   - Automation controls
   - Execution log
   - Screen preview
   - Action review
   - Status indicators

### Expected Output

```
✓ AI Provider Interface
  ✓ should be instantiable
  ✓ should have required methods
  ✓ should store and retrieve API key
  ✓ should report configuration status
  ✓ should return capabilities

✓ OpenAI Provider  
  ✓ should initialize with correct defaults
  ✓ should be configurable with API key
  ✓ should estimate costs

... (30+ tests)

All tests passed! ✓ (30/30)
```

**Pass Criteria:** ✅ All 30+ tests pass

**Screenshot:** You should see the AI Panel UI rendered with all components

---

## ✅ Level 4: End-to-End Automation

**What it tests:** Full automation workflow with AI

**Prerequisites:**
- ✅ OpenAI API key (or local LLM setup)
- ✅ Test server running
- ✅ Automation service built and registered

### Test Scenario 1: Screen Capture

1. Open test UI: `http://localhost:8000/test/layer1-test.html`
2. Open browser DevTools (F12) → Console tab
3. Run test code:

```javascript
// Get provider manager
const providerManager = new AIProviderManager();
const provider = providerManager.getProvider('Local LLM (Privacy)');

// Test connection to automation service
const response = await provider.checkAvailability();
console.log('Service available:', response);
```

**Expected Output:**
```javascript
Service available: false
// (Because local LLM isn't set up yet - this is normal!)
```

### Test Scenario 2: OpenAI Provider (With API Key)

1. Get OpenAI API key from https://platform.openai.com/api-keys
2. Open Settings panel in test UI
3. Select "OpenAI GPT-4 Vision"
4. Enter API key → Save
5. Click "Preview Screen"
6. **Expected:** Service captures screen and sends to OpenAI

```javascript
// Test OpenAI provider
const openAI = providerManager.getProvider('OpenAI GPT-4 Vision');
openAI.setApiKey('sk-...');  // Your API key

// Test action generation
const actions = await openAI.getActions({
  screenshot: 'base64_image_data',
  uiTree: {},
  userRequest: 'Click the start button'
});

console.log('Generated actions:', actions);
```

**Expected:** OpenAI returns suggested actions

### Test Scenario 3: Automation Execution

1. Enter prompt: "Open Notepad"
2. Click "Execute"
3. **Expected behavior:**
   - Service captures screen
   - AI analyzes screen
   - Actions generated
   - User reviews actions
   - Actions executed
   - Notepad opens!

**Pass Criteria:**
- ✅ Screen captured
- ✅ AI returns actions
- ✅ Actions displayed for review
- ✅ Actions execute successfully
- ✅ Target application responds

---

## 🔍 Troubleshooting

### Test Server Won't Start

**Problem:** Port 8000 already in use

**Solution:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <process_id> /F

# Or use different port
python -m http.server 8001
```

### Service Tests Fail

**Problem:** `automation_service.exe` not found

**Solution:**
```bash
cd automation_service
build.bat
```

**Problem:** Screen capture returns 0 bytes

**Solution:**
- Run terminal as Administrator
- Check that Desktop Window Manager (DWM) is running
- Ensure graphics drivers are up to date

**Problem:** "Native Messaging error"

**Solution:**
```bash
# Re-register manifest
cd automation_service
register-manifest.bat

# Verify registry
reg query "HKCU\Software\Google\Chrome\NativeMessagingHosts\com.browser_ai.automation"
```

### Browser Tests Fail

**Problem:** Tests don't run automatically

**Solution:**
- Hard refresh browser (Ctrl+Shift+R)
- Check browser console for errors
- Verify JavaScript files are loading

**Problem:** "Chrome runtime not available"

**Solution:**
- This is normal when testing in regular browser
- LocalLLMProvider will use fallback stub
- For real integration, need Chromium build

### OpenAI Tests Fail

**Problem:** "Invalid API key"

**Solution:**
- Verify API key is correct
- Check you have credits: https://platform.openai.com/usage
- Try regenerating API key

**Problem:** "Rate limit exceeded"

**Solution:**
- Wait 60 seconds and try again
- Check your OpenAI usage limits
- Consider upgrading plan

---

## 📊 Test Results Checklist

Use this checklist to verify everything works:

### Service Tests
- [ ] `test_ping.py` passes (ping)
- [ ] `test_ping.py` passes (capabilities)
- [ ] `test_automation.py` captures screen (> 0 bytes)
- [ ] `test_automation.py` creates screenshot.png file
- [ ] `test_automation.py` inspects UI (children > 0)
- [ ] `test_automation.py` moves mouse successfully

### Browser Tests  
- [ ] Test server starts on port 8000
- [ ] layer1-test.html loads successfully
- [ ] All 30+ tests pass
- [ ] Settings panel opens and closes
- [ ] Provider selection works
- [ ] API key can be saved
- [ ] Automation controls render
- [ ] Execution log displays
- [ ] No console errors

### Integration Tests
- [ ] OpenAI provider configures with API key
- [ ] OpenAI provider reports "Configured"
- [ ] Local LLM provider reports availability
- [ ] Screen preview works
- [ ] Action review displays actions
- [ ] Execute button enables when configured

### End-to-End Tests
- [ ] Can capture desktop screenshot
- [ ] AI returns suggested actions
- [ ] Actions display in review panel
- [ ] Can execute simple action (mouse move)
- [ ] Can execute complex action (click, type)
- [ ] Execution log shows results

---

## 🎯 What Each Test Validates

| Test | Layer 1 | Layer 2 | Layer 3 | Layer 4 |
|------|---------|---------|---------|---------|
| **test_ping.py** | - | ✅ Protocol | - | - |
| **test_automation.py** | - | ✅ Features | - | - |
| **layer1-test.html** | ✅ UI | - | - | - |
| **OpenAI integration** | ✅ | ✅ | ✅ | - |
| **Full automation** | ✅ | ✅ | ✅ | ✅ |

---

## 🚀 Quick Test Commands

Copy-paste these to run all tests:

```bash
# Test 1: Service health
cd A:\browser-ai\automation_service && python test_ping.py

# Test 2: Automation features  
cd A:\browser-ai\automation_service && python test_automation.py

# Test 3: Start browser test server
cd A:\browser-ai\test && python -m http.server 8000
# Then open: http://localhost:8000/test/layer1-test.html

# Test 4: Check screenshot was saved
ls -lh A:\browser-ai\automation_service\screenshot.png
```

---

## ✅ Success Criteria

**Your system is working if:**

1. ✅ **Service responds** - `test_ping.py` passes
2. ✅ **Service captures** - `screenshot.png` file exists
3. ✅ **UI renders** - All 30+ browser tests pass
4. ✅ **Integration works** - OpenAI provider configures
5. ✅ **Automation executes** - Can move mouse or click

**If all 5 criteria pass: Layer 2 is fully operational!** 🎉

---

## 📝 Test Log Template

Use this template to document your test results:

```
Date: _______________
Tester: _______________

Service Tests:
- [ ] test_ping.py: PASS / FAIL
- [ ] test_automation.py: PASS / FAIL  
- [ ] screenshot.png created: YES / NO
- [ ] Screenshot size: ______ KB

Browser Tests:
- [ ] Test server started: YES / NO
- [ ] layer1-test.html loads: YES / NO
- [ ] Tests passed: ____ / 30+
- [ ] Console errors: YES / NO

Integration:
- [ ] OpenAI API key configured: YES / NO
- [ ] Screen capture works: YES / NO
- [ ] Actions generated: YES / NO

End-to-End:
- [ ] Simple automation (mouse move): PASS / FAIL
- [ ] Complex automation (click app): PASS / FAIL
- [ ] Full workflow: PASS / FAIL

Notes:
_________________________________
_________________________________
_________________________________
```

---

## 🎓 Testing Best Practices

1. **Test incrementally** - Start with Level 1, work up to Level 4
2. **Check logs** - Service logs to stderr, browser logs to console
3. **Isolate issues** - If end-to-end fails, test each layer separately
4. **Use Admin mode** - Some tests need elevated permissions
5. **Verify manually** - Watch mouse cursor move, see windows open
6. **Save results** - Keep screenshots and logs for debugging
7. **Test edge cases** - Try invalid inputs, missing permissions
8. **Performance test** - Time how long operations take
9. **Stress test** - Multiple rapid commands
10. **Integration test** - All layers working together

---

## 📚 Related Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Getting started guide
- **[LAYER2_COMPLETE.md](LAYER2_COMPLETE.md)** - Layer 2 status
- **[SETUP.md](automation_service/SETUP.md)** - Setup instructions
- **[README.md](automation_service/README.md)** - Technical docs
- **[test/README.md](test/README.md)** - Test documentation

---

**Happy Testing!** 🧪✨

If all tests pass, you're ready to automate your desktop with AI! 🤖

