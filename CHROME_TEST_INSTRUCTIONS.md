# Testing Chrome → Backend Integration

## Current Status
✅ **C++ HTTP Call to Backend**: IMPLEMENTED  
✅ **Backend Server**: RUNNING on localhost:5000  
⏳ **Automation Service**: Not yet wired  

---

## Test 1: AI Action Generation (No Execution)

This tests if the browser can call the backend and get AI-generated actions.

### Steps:

1. **Ensure Backend is Running**
   ```bash
   cd A:/browser-ai/backend
   python server.py
   ```
   Should show: "Running on http://127.0.0.1:5000"

2. **Launch Chrome**
   - Navigate to: `chrome://ai-panel`
   - Open DevTools (F12)

3. **Configure Provider**
   - Click settings gear ⚙️
   - Select "Ollama (Local)" from dropdown
   - Close settings

4. **Execute Test Request**
   - Enter in text box: "open calculator"
   - Click "Execute Automation"

5. **Expected Output in Console**
   ```
   [TIME] Executing: open calculator
   [TIME] Using provider: ollama
   [TIME] AI returned X actions
   [TIME] Action: press_keys - {"keys":["LWin","R"]}
   [TIME] Action: type - {"text":"calc"}
   ... etc ...
   ```

6. **Check Backend Logs**
   Should see POST request to `/api/get-actions`

---

## Test 2: Manual Action Execution

Once Test 1 works, manually execute actions using Python:

```bash
cd A:/browser-ai/automation_service
echo '{"action":"click","params":{"x":100,"y":100}}' | ./build/bin/Release/automation_service.exe
```

---

## Next Step: Wire Automation

Two options:

### Option A: Backend Executes (Simpler)
- Backend calls automation service after getting AI actions
- Returns execution result to browser

### Option B: Browser Executes (More Control)
- Backend returns actions to browser
- C++ handler calls automation service
- Gives user chance to approve actions

**Recommendation**: Start with Option A

---

##Current State

```
Browser (chrome://ai-panel)
  ↓ WebUI Bridge ✅
C++ Handler
  ↓ HTTP POST ✅
Python Backend (localhost:5000)
  ↓ AI Processing ✅
Actions JSON
  ↓ ❌ NOT YET WIRED
Automation Service ✅ (works standalone)
```

---

## Expected Errors

If you see:
- **"Backend connection not yet implemented"** - Old version, rebuild Chrome
- **"Failed to connect to backend"** - Backend not running, start server.py
- **HTTP timeout** - Backend crashed, check server.py logs
- **"Invalid JSON"** - Backend returned error, check server.py logs

---

**Ready to test!** Start with Test 1.
