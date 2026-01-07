# 🤖 AI Provider Guide

**Browser AI** supports multiple AI providers. Choose based on your needs:

---

## 🎯 Quick Comparison

| Provider | Privacy | Cost | Speed | Quality | Setup Time |
|----------|---------|------|-------|---------|------------|
| **OpenAI** | ⚠️ Cloud | 💰 ~$0.03/req | ⚡ Fast | ⭐⭐⭐⭐⭐ | 5 min |
| **Ollama** | 🔒 100% Local | 🆓 FREE | 🐢 Slow | ⭐⭐⭐⭐ | 15 min |
| **Local LLM** | 🔒 100% Local | 🆓 FREE | 🐢 Very Slow | ⭐⭐⭐ | 30+ min |

---

## 🎨 Provider Options

### Option 1: OpenAI GPT-4 Vision (Cloud) ☁️

**Best for:**
- Highest quality results
- Fast response times
- Production use
- When privacy is less critical

**Pros:**
- ✅ Best AI quality available
- ✅ Very fast (2-5 seconds)
- ✅ Reliable and stable
- ✅ Well-documented API
- ✅ Easy to set up

**Cons:**
- ❌ Costs money (~$0.02-$0.05 per request)
- ❌ Data sent to OpenAI servers
- ❌ Requires internet connection
- ❌ API key required

**Setup:**

1. **Get API Key**
   - Go to https://platform.openai.com/api-keys
   - Create account (requires payment method)
   - Create new API key
   - Copy the key (starts with `sk-`)

2. **Configure Backend**
   ```bash
   cd backend
   cp env-template.txt .env
   # Edit .env and add:
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

3. **Start Backend**
   ```bash
   python server.py
   ```

4. **Select in Browser**
   - Open AI Panel settings
   - Select "OpenAI GPT-4 Vision"
   - Done! 🎉

**Cost Estimate:**
- $0.01275 per image
- $0.01 per 1K input tokens
- $0.03 per 1K output tokens
- **Total: ~$0.02-$0.05 per automation request**

---

### Option 2: Ollama (Local) 🔒

**Best for:**
- Privacy-conscious users
- Free usage
- Offline capability
- Development/testing

**Pros:**
- ✅ 100% private (never leaves your machine)
- ✅ FREE forever
- ✅ Works offline
- ✅ No API key needed
- ✅ Pretty good quality
- ✅ Easy to set up

**Cons:**
- ❌ Slower (5-30 seconds per request)
- ❌ Requires GPU for good speed
- ❌ Lower quality than OpenAI
- ❌ Larger disk space needed (~4-7GB per model)

**Setup:**

1. **Install Ollama**
   - Windows: Download from https://ollama.ai
   - Run installer
   - Ollama will start automatically

2. **Download Vision Model**
   ```bash
   # LLaVA (recommended, 4GB)
   ollama pull llava
   
   # OR BakLLaVA (alternative, 7GB)
   ollama pull bakllava
   ```

3. **Verify Installation**
   ```bash
   ollama list
   # Should show: llava
   ```

4. **Start Backend**
   ```bash
   cd backend
   python server.py
   ```

5. **Select in Browser**
   - Open AI Panel settings
   - Select "Ollama (Local & Private)"
   - Done! 🎉

**Performance Tips:**

- **For CPU-only (slow):**
  - First request: 30-60 seconds
  - Subsequent: 20-30 seconds
  - Use smaller models

- **With GPU (fast):**
  - First request: 5-10 seconds
  - Subsequent: 3-5 seconds
  - Much better quality possible

**Troubleshooting:**

```bash
# Check if Ollama is running:
curl http://localhost:11434/api/tags

# If not running, start it:
ollama serve

# Check models:
ollama list

# Test a model:
ollama run llava "Describe this image" < test.png
```

---

### Option 3: Local LLM (Native) 🔧

**Best for:**
- Maximum privacy
- Custom models
- Advanced users
- Research/development

**Pros:**
- ✅ 100% private
- ✅ FREE
- ✅ Full control
- ✅ Custom models
- ✅ Works offline

**Cons:**
- ❌ Most complex setup
- ❌ Slowest option
- ❌ Requires technical knowledge
- ❌ Quality varies by model
- ❌ Resource intensive

**Setup:**

1. **Build Automation Service**
   ```bash
   cd automation_service
   ./build.bat
   ```

2. **Configure for Local LLM**
   - Edit `automation_service/src/main.cpp`
   - Add local inference backend (llama.cpp, etc.)
   - Rebuild

3. **Register Native Messaging**
   ```bash
   cd automation_service
   ./register-manifest.bat
   ```

4. **Select in Browser**
   - Open AI Panel settings
   - Select "Local LLM (Privacy)"
   - Configure model path

**This option requires C++ development knowledge!**

---

## 🎚️ Choosing Your Provider

### For Most Users: OpenAI
If you're okay with cloud AI and can afford $5-10/month for occasional use.

### For Privacy Fans: Ollama
Best balance of privacy, ease of use, and quality.

### For Developers: All Three
Set up multiple providers and switch based on the task!

---

## 🔄 Switching Providers

**You can switch providers at any time:**

1. Click gear icon in AI Panel
2. Select different provider from dropdown
3. Provider is saved automatically
4. All actions will use new provider

**Example workflow:**

- **Development:** Use Ollama (free)
- **Testing:** Use OpenAI (quality validation)
- **Production:** Use whatever fits your needs

---

## 🔒 Privacy Comparison

### What Data is Shared?

| Provider | Screenshot | UI Tree | Your Prompts | Stored? | Duration |
|----------|------------|---------|--------------|---------|----------|
| **OpenAI** | ✓ Sent | ✓ Sent | ✓ Sent | Yes | 30 days |
| **Ollama** | ✗ Local | ✗ Local | ✗ Local | No | N/A |
| **Local LLM** | ✗ Local | ✗ Local | ✗ Local | No | N/A |

### Security Features

**All Providers:**
- ✅ HTTPS/secure connections
- ✅ No data in browser localStorage
- ✅ API keys stored server-side only
- ✅ Audit logging available

**Local Providers (Ollama/Local LLM):**
- ✅ Never touches the internet
- ✅ No third-party services
- ✅ You control all data
- ✅ Can be used offline

---

## 💰 Cost Analysis

### OpenAI Monthly Costs

**Light use** (10 requests/day):
- ~300 requests/month
- ~$6-15/month

**Moderate use** (50 requests/day):
- ~1,500 requests/month
- ~$30-75/month

**Heavy use** (200 requests/day):
- ~6,000 requests/month
- ~$120-300/month

### Ollama Costs

**Setup:**
- $0 (free download)

**Monthly:**
- $0 (no recurring costs)

**Hardware:**
- Works on any PC (slow without GPU)
- Much faster with GPU (but not required)

**Electricity:**
- ~0.5-2 kWh per hour of use
- ~$0.05-0.20 per hour (depending on rates)

---

## 🧪 Testing Providers

### Test OpenAI

```bash
cd backend
python test_backend.py
```

Expected output:
```
✅ Health check passed
✅ Providers list retrieved
✅ OpenAI: Received 3 actions
```

### Test Ollama

```bash
cd backend
python test_backend.py
```

Expected output:
```
✅ Health check passed
✅ Providers list retrieved
⏭️ OpenAI not configured (skipping)
✅ Ollama: Received 2 actions
```

---

## 🎓 Provider Architecture

### How It Works

```
┌─────────────┐
│   Browser   │ (AI Panel UI)
│   (Layer 1) │
└──────┬──────┘
       │
       ├─────────────┐
       │             │
┌──────▼─────┐  ┌───▼──────────┐
│   Backend  │  │    Native    │
│   Proxy    │  │  Messaging   │
│  (Layer 3) │  │  (Layer 2)   │
└──────┬─────┘  └───┬──────────┘
       │            │
   ┌───┴─────┐     │
   │         │     │
┌──▼───┐  ┌─▼──┐  ▼
│OpenAI│  │Oll-│  Local
│ API  │  │ama │  LLM
└──────┘  └────┘
```

### Why Backend Proxy?

**Security:**
- ✅ API keys never in browser
- ✅ Keys can't be extracted by users
- ✅ Centralized key management

**Flexibility:**
- ✅ Easy to add new providers
- ✅ Can switch without browser changes
- ✅ Rate limiting, caching, logging

**Privacy:**
- ✅ Filter sensitive data before sending
- ✅ Audit all requests
- ✅ Can add encryption

---

## 🔮 Future Providers

We're planning to add:

- [ ] **Anthropic Claude** (cloud, OpenAI alternative)
- [ ] **Google Gemini** (cloud, Google's AI)
- [ ] **LM Studio** (local, GUI for models)
- [ ] **Azure OpenAI** (enterprise, Microsoft)
- [ ] **Hugging Face** (cloud/local, open models)
- [ ] **Custom API** (bring your own provider!)

**Want to add a provider?** PRs welcome!

---

## 🤝 Recommendations

### For Getting Started

1. **Start with OpenAI** (easiest, best quality)
   - Get something working quickly
   - Validate your use case
   - See if it's worth investing more time

2. **Then Try Ollama** (free, private)
   - See if quality is good enough
   - Test performance on your hardware
   - Decide if you need cloud AI

3. **Use Both** (best of both worlds)
   - OpenAI for important tasks
   - Ollama for privacy-sensitive tasks
   - Switch freely in the UI

### For Production

- **Need reliability:** OpenAI
- **Need privacy:** Ollama
- **Need both:** Run Ollama, failover to OpenAI
- **Enterprise:** Consider Azure OpenAI (not yet supported)

---

## 📚 Additional Resources

### OpenAI
- API Docs: https://platform.openai.com/docs/guides/vision
- Pricing: https://openai.com/pricing
- Rate Limits: https://platform.openai.com/docs/guides/rate-limits

### Ollama
- Website: https://ollama.ai
- Model Library: https://ollama.ai/library
- GitHub: https://github.com/ollama/ollama
- Discord: https://discord.gg/ollama

### Local LLMs
- llama.cpp: https://github.com/ggerganov/llama.cpp
- LLaVA: https://llava-vl.github.io/
- CogVLM: https://github.com/THUDM/CogVLM
- Qwen-VL: https://github.com/QwenLM/Qwen-VL

---

## ❓ FAQ

### Q: Which provider should I use?

**A:** Start with OpenAI if you can afford it (~$10/month light use). Switch to Ollama if you want free and private.

### Q: Can I use multiple providers?

**A:** Yes! Set up as many as you want and switch in the UI.

### Q: Is my data safe with OpenAI?

**A:** OpenAI stores data for 30 days for abuse monitoring. After that, it's deleted. Read their privacy policy: https://openai.com/policies/privacy-policy

### Q: How much faster is Ollama with a GPU?

**A:** 5-10x faster. CPU: 20-30 sec/request, GPU: 2-5 sec/request.

### Q: Can I use Ollama on a laptop?

**A:** Yes, but it will be slow without a dedicated GPU. Still faster than waiting for cloud API if you have no internet!

### Q: What's the best Ollama model?

**A:** `llava` (4GB) for most users. `bakllava` (7GB) for better quality if you have space.

### Q: Can I add my own AI provider?

**A:** Yes! See `backend/README.md` for instructions on adding custom providers.

### Q: Does this work offline?

**A:** OpenAI requires internet. Ollama and Local LLM work 100% offline.

---

**Questions?** Open an issue or check the main README!

