# Quick Start Guide: Browser AI

Get your Atlas-like desktop automation system running in 3 simple steps!

## 🎯 What You're Building

A Chromium browser with AI-powered desktop automation:
- 🤖 OpenAI GPT-4 Vision analyzes your screen
- 👀 Captures screenshots and inspects UI elements
- 🖱️ Controls mouse and keyboard to automate tasks
- 🔒 Optional local LLM for privacy

---

## ✅ Current Status

### Layer 1: Browser Architecture ✓ COMPLETE
- AI provider system (OpenAI + Local LLM)
- Modern automation UI
- Settings and configuration
- **Status**: Tested and working ✓

### Layer 2: Automation Service ✓ COMPLETE
- Windows UIAutomation wrapper
- Screen capture (GPU-accelerated)
- Mouse/keyboard control
- Native Messaging protocol
- **Status**: Complete and tested ✓

### Layer 3: AI Integration ✓ COMPLETE
- Provider-agnostic architecture
- OpenAI GPT-4 Vision support (cloud)
- Ollama support (local, private, free)
- Backend proxy server
- Easy provider switching
- **Status**: Code complete, needs testing

---

## 🚀 Next Steps (Pick Your Path)

### Path A: Quick Test (No Chromium Build)

**Time**: 15 minutes  
**Goal**: Test the automation service standalone

```cmd
# 1. Install Visual Studio (if not installed)
#    https://visualstudio.microsoft.com/downloads/
#    Select: Desktop development with C++

# 2. Build the service
cd automation_service
build.bat

# 3. Test it
test-service.bat
```

**Expected output**:
```json
{"success":true,"message":"pong","version":"1.0.0"}
{"success":true,"capabilities":{...}}
```

✅ If you see this, Layer 2 is working!

---

### Path B: Full Integration (With Chromium)

**Time**: Several hours (Chromium build is slow)  
**Goal**: Complete working AI browser

#### Step 1: Build Automation Service (15 min)

```cmd
cd automation_service
build.bat
register-manifest.bat
test-service.bat
```

#### Step 2: Get Chromium Source (~30-60 min)

```cmd
# Install depot_tools
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
set PATH=%PATH%;%CD%\depot_tools

# Get Chromium (large download!)
cd chromium
fetch --nohooks chromium
cd src
gclient sync
gclient runhooks
```

#### Step 3: Integrate AI Panel (~5 min)

```cmd
# Copy our files to Chromium
cd ..\..
.\sync-to-chromium.bat

# Update Chromium build files
# See: INTEGRATION.md for detailed steps
```

#### Step 4: Build Chromium (~2-4 hours)

```cmd
cd chromium\src
gn gen out\Default
autoninja -C out\Default chrome
```

#### Step 5: Test!

```cmd
out\Default\chrome.exe --enable-features=AIPanel
# Navigate to: chrome://ai-panel
```

---

## 🧪 Testing Layer 1 (Browser UI)

**No Chromium build needed!**

```cmd
# Start test server
cd test
.\run-test-server.sh  # or use Git Bash

# Open browser to:
http://localhost:8000/test/layer1-test.html
```

**What it tests**:
- ✓ AI Provider interface
- ✓ OpenAI provider setup
- ✓ Local LLM provider structure
- ✓ Provider management
- ✓ UI rendering

**Expected**: 30+ tests pass ✓

---

## 📋 Prerequisites

### For Layer 2 Build (Windows)

- ✅ Windows 10/11
- ✅ Visual Studio 2019+ with C++ desktop development
- ✅ CMake 3.20+ (included with VS or install separately)
- ✅ Git

### For Chromium Build (Optional)

- ✅ All of the above, plus:
- ✅ ~100GB free disk space
- ✅ 16GB+ RAM
- ✅ Fast internet connection
- ✅ Several hours for initial build
- ✅ depot_tools

---

## 🎬 Recommended Workflow

### Week 1: Test Layers Independently

1. **Day 1-2**: Test Layer 1 (browser UI)
   - Run test server
   - Verify all tests pass
   - Explore the UI

2. **Day 3-4**: Build Layer 2 (automation service)
   - Install Visual Studio if needed
   - Build the C++ service
   - Test standalone (mouse control, typing, etc.)

3. **Day 5**: Setup Layer 3 (AI Integration)
   - **Option A: OpenAI** (fastest, $0.03/req)
     ```bash
     cd backend
     setup.bat
     # Edit .env, add OPENAI_API_KEY=sk-...
     python server.py
     python test_backend.py
     ```
   - **Option B: Ollama** (free, private)
     ```bash
     # Install from https://ollama.ai
     ollama pull llava
     cd backend
     python server.py
     python test_backend.py
     ```
   - **Option C: Both!** (recommended)
     - Set up both providers
     - Switch between them in UI
     - Compare quality vs. privacy tradeoffs

### Week 2: Full Integration (Optional)

4. **Days 1-3**: Build Chromium
   - Download Chromium source
   - Integrate AI Panel
   - Build (takes hours!)

5. **Day 4**: End-to-end testing
   - Test chrome://ai-panel
   - Capture real screenshots
   - Execute automation

6. **Day 5**: Automate!
   - Try real-world automation tasks
   - Refine and iterate

---

## 🔍 Troubleshooting Quick Links

### Build Issues
- [SETUP.md](automation_service/SETUP.md) - Complete setup guide
- [README.md](automation_service/README.md) - Technical details

### Browser Issues
- [test/README.md](test/README.md) - Test documentation
- Check browser console (F12)

### Integration Issues
- Check Native Messaging registration
- Verify manifest.json path
- Check Chrome version compatibility

---

## 📚 Documentation Index

- **[README.md](README.md)** - Main project overview
- **[SETUP.md](automation_service/SETUP.md)** - Layer 2 setup guide (START HERE)
- **[automation_service/README.md](automation_service/README.md)** - C++ service technical docs
- **[test/README.md](test/README.md)** - Testing guide
- **[Architecture Plan](c:\Users\dotex\.cursor\plans\atlas-like_desktop_automation_system_f25cd790.plan.md)** - Full design document

---

## 🎯 Current Recommended Path

**Start here** → Build Layer 2 → Test standalone → Add OpenAI key → Enjoy automation!

```cmd
cd automation_service
.\build.bat          # Build the service
.\register-manifest.bat  # Register with Chrome
.\test-service.bat    # Test it works
```

Then test Layer 1 in browser:
```cmd
cd test
.\run-test-server.sh
# Open: http://localhost:8000/test/layer1-test.html
```

**Building Chromium is optional** - Layer 1 + Layer 2 can work via Native Messaging without rebuilding Chromium if you use the test UI!

---

## 💡 Tips

1. **Start small** - Test layers independently first
2. **Use test UI** - Faster than building Chromium
3. **Check logs** - Service logs to stderr
4. **Get API key** - OpenAI API key needed for AI features
5. **Be patient** - Chromium builds take hours

---

## 🆘 Getting Help

1. Check relevant README in each directory
2. Review SETUP.md troubleshooting section
3. Check browser console for errors
4. Verify all prerequisites are installed
5. Try a clean rebuild

---

## 🎉 Success Criteria

You'll know it's working when:

✅ Layer 1 tests pass (30+ tests)  
✅ Layer 2 builds without errors  
✅ `test-service.bat` shows JSON responses  
✅ OpenAI API key is configured  
✅ Test UI can connect to services  
✅ (Optional) chrome://ai-panel loads  

**You're ready to automate!** 🚀

