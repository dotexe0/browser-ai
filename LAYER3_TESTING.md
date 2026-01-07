# 🧪 Layer 3 Testing Guide

Testing the AI integration (provider-agnostic)

---

## 📋 Prerequisites

Before testing Layer 3, ensure Layers 1 & 2 are working:

- ✅ Layer 1: Browser UI functional
- ✅ Layer 2: Automation service built and tested

---

## 🎯 What We're Testing

Layer 3 connects the Browser UI (Layer 1) to AI providers via:
- Backend proxy server (for cloud/Ollama)
- Native Messaging (for local LLM)

**Goal**: Get AI to generate automation actions from screenshots + prompts

---

## 🚀 Setup & Testing

### Phase 1: Backend Setup (5-15 minutes)

#### 1.1 Install Dependencies

```bash
cd backend
setup.bat
```

This will:
- Install Python dependencies (Flask, requests, etc.)
- Create `.env` from template
- Show next steps

#### 1.2 Choose Your Provider

**Option A: OpenAI (Fastest Test) ☁️**

**Setup Time:** 5 minutes  
**Cost:** ~$0.03 per test  
**Quality:** Best

```bash
# 1. Get API key
# Go to: https://platform.openai.com/api-keys
# Create account, add payment method, create key

# 2. Edit .env file
notepad .env

# 3. Add your key:
OPENAI_API_KEY=sk-your-actual-key-here

# Save and close
```

**Option B: Ollama (Free & Private) 🔒**

**Setup Time:** 15 minutes  
**Cost:** FREE  
**Quality:** Good

```bash
# 1. Install Ollama
# Download from: https://ollama.ai
# Run installer (will start automatically)

# 2. Download vision model
ollama pull llava

# This downloads ~4GB, takes 5-10 minutes

# 3. Verify installation
ollama list
# Should show: llava

# 4. Test it works
curl http://localhost:11434/api/tags
```

**Option C: Both (Recommended!)**

Set up both providers, then you can switch between them!

---

### Phase 2: Test Backend (2 minutes)

#### 2.1 Start Server

Open a new terminal:

```bash
cd backend
python server.py
```

You should see:

```
🚀 Provider-Agnostic AI Proxy Server
======================================================================

Configured providers:
  ✓ OpenAI GPT-4 Vision (cloud)
  ✓ Ollama (local) - check if running

Starting server on http://localhost:5000
======================================================================
```

**Leave this terminal open!**

#### 2.2 Test Providers

Open another terminal:

```bash
cd backend
python test_backend.py
```

Expected output:

```
🧪 Backend Proxy Server Tests
======================================================================

1. Testing health endpoint...
   ✅ Health check passed

2. Testing providers list...
   ✅ OpenAI GPT-4 Vision (cloud)
   ✅ Ollama (Local) (local) 🔒 [full]
   ✅ Providers list retrieved

3. Testing OpenAI provider...
   ✅ Received 3 actions:
      1. click: {'x': 110, 'y': 150}
      2. wait: {'ms': 500}
      3. type: {'text': 'Hello'}

4. Testing Ollama provider...
   ✅ Received 2 actions:
      1. click: {'x': 110, 'y': 150}

======================================================================
📊 Test Summary
======================================================================
   ✅ PASS - Health Check
   ✅ PASS - Providers List
   ✅ PASS - OpenAI Provider
   ✅ PASS - Ollama Provider

   4/4 tests passed
======================================================================
```

---

### Phase 3: Browser Integration (5 minutes)

#### 3.1 Update AI Panel

The browser-side code is already updated! Just need to import Ollama provider.

Edit `src/chrome/browser/ui/webui/ai_panel/resources/ai_panel.html`:

Find the `<script>` section and ensure it imports:

```html
<script type="module">
  import { AIProvider } from './ai_provider_interface.js';
  import { OpenAIProvider } from './openai_provider.js';
  import { OllamaProvider } from './ollama_provider.js';
  import { LocalLLMProvider } from './local_llm_provider.js';
  import { AIProviderManager } from './ai_provider_manager.js';
  // ... rest of code
</script>
```

#### 3.2 Test in Browser

```bash
# Start test server (in a new terminal)
cd test
bash run-test-server.sh

# Or on Windows:
cd test
python -m http.server 8000
```

Open browser to: http://localhost:8000/test/simple-demo.html

**Test Steps:**

1. Click the gear icon (⚙️) to open settings

2. Check provider dropdown - should show:
   - OpenAI GPT-4 Vision
   - Ollama (Local & Private)
   - Local LLM (Privacy)

3. Select a provider:
   - **If using OpenAI**: No API key needed (backend has it)
   - **If using Ollama**: Just select it (no key needed)

4. Status should show: "✅ Provider configured"

---

### Phase 4: End-to-End Test (The Big Test!) 🎉

#### 4.1 Prepare Test Environment

Make sure you have:
- ✅ Backend server running (`python server.py`)
- ✅ Browser UI open (`simple-demo.html`)
- ✅ Automation service running (if using Native Messaging)
- ✅ A simple app open to test on (e.g., Notepad)

#### 4.2 Run Full Automation

In the browser UI:

1. **Enter a command:**
   ```
   Open Notepad and type "Hello from AI!"
   ```

2. **Click "Execute"**

3. **What should happen:**
   - Browser captures screenshot (you should see it in preview)
   - Browser gets UI tree from automation service
   - Browser sends to backend proxy
   - Backend forwards to AI (OpenAI or Ollama)
   - AI analyzes image + UI tree
   - AI returns actions like:
     ```json
     [
       {"action": "press_keys", "params": {"keys": ["LWin", "R"]}},
       {"action": "wait", "params": {"ms": 500}},
       {"action": "type", "params": {"text": "notepad"}},
       {"action": "press_keys", "params": {"keys": ["Return"]}},
       {"action": "wait", "params": {"ms": 1000}},
       {"action": "type", "params": {"text": "Hello from AI!"}}
     ]
     ```
   - Browser shows actions in "Action Review" panel
   - Click "Confirm & Execute"
   - Automation service executes actions
   - Notepad opens, text appears!

4. **Verify in logs:**
   - Browser console should show provider calls
   - Backend terminal should show API requests
   - Automation service should log actions

---

## 🐛 Troubleshooting

### Backend Issues

#### "ModuleNotFoundError: No module named 'flask'"

```bash
cd backend
pip install -r requirements.txt
```

#### "OpenAI API key not configured"

1. Check `.env` file exists
2. Verify key format: `OPENAI_API_KEY=sk-...`
3. Restart backend server

#### "Connection refused to localhost:5000"

- Backend server not running
- Start it: `python server.py`

### Ollama Issues

#### "Ollama error: Is Ollama running?"

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it:
ollama serve
```

#### "llava model not found"

```bash
ollama pull llava
# Wait for ~4GB download
```

#### "Ollama very slow (30+ seconds)"

- First request is always slow (model loading)
- Subsequent requests faster
- If you have a GPU, it will be much faster automatically

### Browser Issues

#### "Provider not showing in dropdown"

1. Check browser console for errors
2. Verify `ollama_provider.js` imported correctly
3. Hard refresh browser (Ctrl+Shift+R)

#### "Screenshot not capturing"

- Automation service must be running
- Check Native Messaging registration
- Try Layer 2 tests first (`test_automation.py`)

#### "Actions not executing"

- Backend server must be running
- Check provider configuration
- Look for errors in browser console
- Check backend server logs

---

## 📊 Test Results

### Expected Timings

| Provider | First Request | Subsequent | Quality |
|----------|--------------|------------|---------|
| OpenAI | 3-5 seconds | 2-4 seconds | ⭐⭐⭐⭐⭐ |
| Ollama (CPU) | 20-30 seconds | 15-25 seconds | ⭐⭐⭐⭐ |
| Ollama (GPU) | 5-10 seconds | 3-5 seconds | ⭐⭐⭐⭐ |

### Quality Comparison

**OpenAI:**
- ✅ Very accurate coordinates
- ✅ Good action sequencing
- ✅ Handles complex requests
- ✅ Rarely fails

**Ollama:**
- ✅ Decent coordinate accuracy
- ✅ Good for simple tasks
- ⚠️ May need prompt tuning
- ⚠️ Can be inconsistent

---

## 🎓 Advanced Testing

### Test Different Prompts

Try various complexity levels:

**Simple:**
```
Click the text editor
Type "Hello World"
```

**Medium:**
```
Open Notepad and write a short poem
```

**Complex:**
```
Open Chrome, navigate to Google, and search for "AI automation"
```

### Test Error Handling

Try invalid requests:

```
Do something impossible
[Should gracefully fail with error message]
```

### Test Provider Switching

1. Use OpenAI for a request
2. Switch to Ollama in settings
3. Try same request
4. Compare results!

---

## 📈 Success Criteria

Layer 3 is working if:

- ✅ Backend server starts without errors
- ✅ Test suite passes (all providers tested)
- ✅ Browser can list providers
- ✅ Can switch between providers
- ✅ AI returns valid action arrays
- ✅ Actions have correct format
- ✅ Simple automations work end-to-end

---

## 🎉 When All Tests Pass

You'll have:

- ✅ Working AI integration
- ✅ Choice of cloud (OpenAI) or local (Ollama)
- ✅ Provider switching in UI
- ✅ Full automation pipeline: UI → AI → Actions → Execution

**Next Steps:**
- Fine-tune prompts for better quality
- Add action preview UI
- Implement safety features (Layer 4)
- Test more complex workflows

---

## 🔬 Detailed Logging

For debugging, enable verbose logging:

**Backend:**
```python
# Edit server.py
app.run(host='0.0.0.0', port=5000, debug=True)
```

**Browser:**
```javascript
// In browser console:
localStorage.setItem('debug_ai_panel', 'true');
// Refresh page
```

**Automation Service:**
```bash
# Run with debug output
automation_service.exe > debug.log 2>&1
```

---

## 📚 Additional Resources

- **Provider Comparison:** See `PROVIDERS.md`
- **Backend API:** See `backend/README.md`
- **Architecture:** See main `README.md`
- **Layer 2 Testing:** See `TESTING.md`

---

**Questions?** Check the main README or open an issue!

**Success?** Move on to Layer 4 (safety features)!

