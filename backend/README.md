# 🤖 Provider-Agnostic AI Backend

A flexible proxy server that supports **multiple AI providers** with a single API.

---

## 🎯 Supported Providers

### Option 1: OpenAI GPT-4 Vision (Cloud) ☁️
**Best for**: Highest quality, most reliable
**Privacy**: Data sent to OpenAI servers
**Cost**: ~$0.02-0.05 per request
**Setup time**: 5 minutes

### Option 2: Anthropic Claude (Cloud) ☁️
**Best for**: Alternative to OpenAI, good privacy policies
**Privacy**: Data sent to Anthropic servers
**Cost**: Similar to OpenAI
**Setup time**: 5 minutes

### Option 3: Ollama (Local) 🔒
**Best for**: Privacy, free, offline use
**Privacy**: 100% local, never leaves your machine
**Cost**: FREE!
**Setup time**: 15 minutes

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Choose Your Provider(s)

#### Option A: OpenAI (Easiest)

1. Get API key from https://platform.openai.com/api-keys
2. Copy `env-template.txt` to `.env`:
   ```bash
   cp env-template.txt .env
   ```
3. Edit `.env` and add your key:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

#### Option B: Ollama (Most Private)

1. Install Ollama from https://ollama.ai
2. Pull the vision model:
   ```bash
   ollama pull llava
   ```
3. That's it! No API key needed.

#### Option C: Both (Recommended!)

Set up both options above. You can switch between them in the browser UI!

### 3. Start the Server

```bash
python server.py
```

You should see:

```
🚀 Provider-Agnostic AI Proxy Server
======================================================================

Configured providers:
  ✓ OpenAI GPT-4 Vision (cloud)
  ✓ Ollama (local) - check if running

Endpoints:
  GET  /api/health - Health check
  GET  /api/providers - List available providers
  POST /api/get-actions - Get AI actions
  POST /api/add-provider - Add custom provider

Starting server on http://localhost:5000
======================================================================
```

### 4. Verify It Works

Open a new terminal:

```bash
# Check health
curl http://localhost:5000/api/health

# Should return:
{
  "status": "ok",
  "providers": {
    "openai": true,
    "anthropic": false,
    "ollama": true
  }
}
```

---

## 📖 API Reference

### GET /api/health

Health check. Returns status of all providers.

**Response:**
```json
{
  "status": "ok",
  "providers": {
    "openai": true,
    "anthropic": false,
    "ollama": true
  }
}
```

### GET /api/providers

List available providers.

**Response:**
```json
{
  "providers": [
    {
      "id": "openai",
      "name": "OpenAI GPT-4 Vision",
      "type": "cloud",
      "requires_key": true,
      "configured": true
    },
    {
      "id": "ollama",
      "name": "Ollama (Local)",
      "type": "local",
      "requires_key": false,
      "configured": true,
      "privacy": "full"
    }
  ]
}
```

### POST /api/get-actions

Get automation actions from AI.

**Request:**
```json
{
  "provider": "openai",
  "screenshot": "base64_encoded_png_data",
  "ui_tree": {
    "windows": [...]
  },
  "user_request": "Open Notepad and type hello"
}
```

**Response:**
```json
{
  "success": true,
  "actions": [
    {
      "action": "press_keys",
      "params": {
        "keys": ["LWin", "R"]
      },
      "confidence": 0.9
    },
    {
      "action": "wait",
      "params": {
        "ms": 500
      }
    },
    {
      "action": "type",
      "params": {
        "text": "notepad"
      }
    },
    {
      "action": "press_keys",
      "params": {
        "keys": ["Return"]
      }
    },
    {
      "action": "wait",
      "params": {
        "ms": 1000
      }
    },
    {
      "action": "type",
      "params": {
        "text": "hello"
      }
    }
  ]
}
```

### POST /api/add-provider

Add or update a custom provider.

**Request:**
```json
{
  "id": "custom_ai",
  "config": {
    "api_key": "your-key",
    "endpoint": "https://api.example.com/v1/chat",
    "model": "custom-model-v1"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Provider custom_ai added"
}
```

---

## 🔧 Advanced Configuration

### Using Anthropic Claude

1. Get API key from https://console.anthropic.com
2. Add to `.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```
3. Restart server
4. Select "Anthropic Claude" in browser UI

### Using Different Ollama Models

By default, we use `llava` (vision model). To use a different model:

1. Edit `.env`:
   ```
   OLLAMA_MODEL=bakllava  # Alternative vision model
   ```
2. Pull the model:
   ```bash
   ollama pull bakllava
   ```
3. Restart server

### Custom Ollama Endpoint

If Ollama is running on a different machine:

```
OLLAMA_ENDPOINT=http://192.168.1.100:11434/api/generate
```

---

## 🔒 Security & Privacy

### API Key Security

- ✅ API keys stored in `.env` (server-side only)
- ✅ Never sent to browser
- ✅ Not logged or cached
- ✅ `.env` in `.gitignore` (never committed)

### Privacy Levels

| Provider | Privacy Level | Data Storage |
|----------|--------------|--------------|
| **Ollama** | 🔒 Full | Local only |
| **OpenAI** | ⚠️ Moderate | Stored 30 days |
| **Anthropic** | ⚠️ Moderate | Stored per TOS |

**For maximum privacy**: Use Ollama (local model)

---

## 🧪 Testing

### Test OpenAI Provider

```bash
# Make sure server is running, then:
python test_openai.py
```

### Test Ollama Provider

```bash
# Make sure Ollama is running:
ollama list  # Should show llava

# Test:
python test_ollama.py
```

---

## 🐛 Troubleshooting

### "OpenAI API key not configured"

- Check `.env` file exists
- Verify `OPENAI_API_KEY=sk-...` is set
- Restart server after editing `.env`

### "Ollama error: Is Ollama running?"

```bash
# Check if Ollama is running:
curl http://localhost:11434/api/tags

# If not running, start it:
ollama serve

# Check if llava model is installed:
ollama list

# If not installed:
ollama pull llava
```

### "Failed to parse AI response"

- AI providers sometimes return explanatory text instead of pure JSON
- Try adding more specific instructions in your prompt
- Check server logs for raw response
- Local models (Ollama) may need prompt tuning

### Port 5000 Already in Use

```bash
# Find what's using port 5000:
netstat -ano | findstr :5000

# Option 1: Kill the process
taskkill /PID <pid> /F

# Option 2: Use a different port
# Edit server.py, change:
app.run(host='0.0.0.0', port=5001, debug=True)
```

---

## 📊 Performance

### Response Times (typical)

| Provider | First Request | Subsequent |
|----------|--------------|------------|
| OpenAI | 3-5 seconds | 2-4 seconds |
| Anthropic | 3-5 seconds | 2-4 seconds |
| Ollama (CPU) | 10-30 seconds | 10-30 seconds |
| Ollama (GPU) | 2-5 seconds | 2-5 seconds |

### Tips for Faster Local Inference

1. **Use GPU acceleration** (if available)
   ```bash
   # Ollama automatically uses GPU if available
   ollama pull llava
   ```

2. **Use smaller models**
   ```bash
   ollama pull llava:7b  # Smaller = faster
   ```

3. **Reduce image resolution**
   - Capture at lower DPI
   - Resize before sending

---

## 🎓 Adding Custom Providers

Want to use a different AI provider? Easy!

### 1. Add Provider Function

Edit `server.py`:

```python
def call_custom_provider(screenshot_base64, ui_tree, user_request):
    """Call your custom AI provider"""
    
    # Your API call logic here
    response = requests.post(
        'https://api.example.com/v1/inference',
        json={
            'image': screenshot_base64,
            'prompt': user_request,
            'context': ui_tree
        }
    )
    
    # Parse response
    actions = response.json()['actions']
    
    return {'success': True, 'actions': actions}
```

### 2. Register Provider

```python
PROVIDERS['custom'] = {
    'api_key': os.getenv('CUSTOM_API_KEY', ''),
    'endpoint': 'https://api.example.com/v1/inference',
    'model': 'custom-vision-v1'
}
```

### 3. Add Route Handler

```python
@app.route('/api/get-actions', methods=['POST'])
def get_actions():
    # ... existing code ...
    
    elif provider == 'custom':
        result = call_custom_provider(screenshot, ui_tree, user_request)
    
    return jsonify(result)
```

### 4. Create Browser Provider

```javascript
class CustomProvider extends AIProvider {
  constructor() {
    super('Custom AI Provider', false);
    this.providerId = 'custom';
  }
  
  async getActions(params) {
    // Use same backend proxy
    return await this.callBackend(params);
  }
}
```

Done! 🎉

---

## 📚 Resources

- **OpenAI API**: https://platform.openai.com/docs/guides/vision
- **Anthropic API**: https://docs.anthropic.com/
- **Ollama**: https://ollama.ai
- **Vision Models**: https://ollama.ai/library?q=vision

---

## ⚡ Performance Tips

### For Cloud Providers (OpenAI/Anthropic)

1. **Compress images** before sending
2. **Cache UI tree** if screen hasn't changed
3. **Batch requests** when possible
4. **Use streaming** for faster feedback (future feature)

### For Local Models (Ollama)

1. **Use GPU** if available (10x faster)
2. **Choose appropriate model size**:
   - `llava:7b` - Fastest, good for simple tasks
   - `llava:13b` - Balanced
   - `llava:34b` - Best quality, slower
3. **Warm up model** with a test request on startup
4. **Keep Ollama running** in the background

---

## 🔮 Future Enhancements

- [ ] Streaming responses for real-time feedback
- [ ] Request batching for efficiency
- [ ] Response caching for repeated tasks
- [ ] Multi-provider voting (consensus across AIs)
- [ ] Custom model fine-tuning
- [ ] Provider auto-failover
- [ ] Cost tracking and budgets
- [ ] Performance metrics dashboard

---

## 🤝 Contributing

Want to add support for more providers? PRs welcome!

Examples of providers to add:
- LM Studio (local)
- Google Gemini (cloud)
- Azure OpenAI (enterprise)
- Hugging Face Inference API
- Your custom model!

---

**Questions?** Check the main project README or open an issue!

