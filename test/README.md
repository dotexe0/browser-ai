# 🧪 Browser AI Test Suite

This folder contains all essential tests for the Browser AI system.

---

## 📋 Test Organization

### **Browser UI Tests** (Layer 1)

#### `layer1-test.html`
**Purpose**: Comprehensive unit tests for the browser-side AI Panel UI

**What it tests**:
- ✅ AI provider interface and implementations
- ✅ Provider manager and switching
- ✅ UI rendering and interactions
- ✅ Settings panel functionality
- ✅ API key management
- ✅ Automation controls
- ✅ Execution log and status indicators
- ✅ LocalStorage persistence

**How to run**:
```bash
cd /a/browser-ai/test
../test/run-test-server.sh
# Open http://localhost:8000/test/layer1-test.html
```

**Status**: ✅ 36 tests passing

---

#### `simple-demo.html`
**Purpose**: Interactive demo of the AI Panel UI

**What it tests**:
- Provider selection and switching
- Settings panel interaction
- UI responsiveness
- Visual feedback

**How to run**:
```bash
cd /a/browser-ai/test
../test/run-test-server.sh
# Open http://localhost:8000/test/simple-demo.html
```

**Status**: ✅ Fully functional

---

### **Automation Tests** (Layer 2)

See `../automation_service/` folder:

#### `automation_service/test_ping.py`
**Purpose**: Basic connectivity test for the C++ automation service

**What it tests**:
- ✅ Service starts and responds
- ✅ Native Messaging protocol works
- ✅ JSON serialization/deserialization
- ✅ Basic capabilities query

**How to run**:
```bash
cd /a/browser-ai/automation_service
python test_ping.py
```

---

#### `automation_service/test_automation.py`
**Purpose**: Comprehensive automation capabilities test

**What it tests**:
- ✅ Screen capture
- ✅ UI inspection
- ✅ Mouse movement and clicks
- ✅ Keyboard input and key combinations
- ✅ Text typing with Unicode support

**How to run**:
```bash
cd /a/browser-ai/automation_service
python test_automation.py
```

---

### **Backend Tests** (Layer 3)

See `../backend/` folder:

#### `backend/test_backend.py`
**Purpose**: Backend API health checks and provider availability

**What it tests**:
- ✅ Backend server is running
- ✅ Health endpoint responds
- ✅ Provider endpoints are accessible
- ✅ Ollama availability (if running)
- ✅ OpenAI endpoint (with API key)

**How to run**:
```bash
cd /a/browser-ai/backend
python test_backend.py
```

---

#### `backend/test_e2e.py`
**Purpose**: End-to-end backend test with dummy data

**What it tests**:
- ✅ Full request/response cycle
- ✅ AI provider routing
- ✅ Action generation and formatting
- ✅ Error handling

**How to run**:
```bash
# Terminal 1: Start backend
cd /a/browser-ai/backend
python server.py

# Terminal 2: Run test
cd /a/browser-ai/backend
python test_e2e.py
```

---

### **Full AI Automation Tests** (All Layers)

#### `test_ai_automation.py` ⭐
**Purpose**: **Complete end-to-end AI automation test** (VERIFIED WORKING)

**What it tests**:
- ✅ Opens Notepad via automation
- ✅ Sends request to Ollama AI
- ✅ AI generates typing actions
- ✅ Automation executes AI commands
- ✅ **Text appears on screen from AI!**

**How to run**:
```bash
# Terminal 1: Start backend
cd /a/browser-ai/backend
python server.py

# Terminal 2: Start Ollama (if not running)
ollama serve

# Terminal 3: Run AI automation test
cd /a/browser-ai/test
python test_ai_automation.py
```

**Expected result**: Notepad opens and AI-generated text types automatically!

**Status**: ✅ **VERIFIED - User confirmed working**

---

#### `demo_automation.py`
**Purpose**: Simple automation demo without AI (for quick verification)

**What it tests**:
- ✅ Automation service works
- ✅ Opens Notepad
- ✅ Types predefined text
- ✅ Keyboard shortcuts work

**How to run**:
```bash
cd /a/browser-ai/test
python demo_automation.py
```

**Expected result**: Notepad opens and predefined message types

**Status**: ✅ Working

---

## 🚀 Quick Test Commands

### **Test Everything (Recommended Order)**

```bash
# 1. Test browser UI (Layer 1)
cd /a/browser-ai/test
./run-test-server.sh
# Open http://localhost:8000/test/layer1-test.html

# 2. Test automation (Layer 2)
cd /a/browser-ai/test
python demo_automation.py

# 3. Test backend (Layer 3)
cd /a/browser-ai/backend
python test_backend.py

# 4. Test full AI automation (All layers)
# Start backend first, then:
cd /a/browser-ai/test
python test_ai_automation.py
```

---

## 📊 Test Status Summary

| Test | Layer | Status | What It Verifies |
|------|-------|--------|------------------|
| `layer1-test.html` | 1 | ✅ 36/36 | Browser UI components |
| `simple-demo.html` | 1 | ✅ Working | Interactive UI demo |
| `test_ping.py` | 2 | ✅ Working | Service connectivity |
| `test_automation.py` | 2 | ✅ Working | Desktop automation |
| `test_backend.py` | 3 | ✅ Working | Backend health |
| `test_e2e.py` | 3 | ✅ Working | Backend integration |
| `test_ai_automation.py` | 1+2+3 | ✅ **VERIFIED** | **Full AI automation** |
| `demo_automation.py` | 2 | ✅ Working | Quick automation demo |

---

## 🔧 Test Requirements

### Layer 1 (Browser UI):
- Web browser (any modern browser)
- Python 3 (for test server)

### Layer 2 (Automation):
- Windows OS
- Built C++ automation service (`automation_service/build/bin/Release/automation_service.exe`)
- Python 3

### Layer 3 (Backend):
- Python 3 with dependencies (`pip install -r backend/requirements.txt`)
- Ollama installed and running (for local AI)
- OR OpenAI API key in `.env` (for cloud AI)

---

## 📝 Notes

- All tests are non-destructive and safe to run
- Automation tests may take focus (close other windows before running)
- AI tests require either Ollama or OpenAI to be configured
- Run tests in order for best results (Layer 1 → 2 → 3)

---

## ✅ Test Maintenance

**When to add a new test**:
- New UI component or feature
- New automation action
- New AI provider
- Regression bug found

**When to update existing tests**:
- API changes
- New capabilities added
- Test failures need investigation

**When to remove tests**:
- Feature removed
- Test is redundant
- Test is debug/exploratory only

---

**Last Updated**: January 7, 2026  
**All Tests**: ✅ Passing and verified on Windows 11
