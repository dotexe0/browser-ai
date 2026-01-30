# Eliminate Python Backend — Merge AI Provider Routing into C++ Service

**Goal:** Remove the Python Flask backend entirely. Move all AI provider routing, API key management, and request validation into the C++ automation service. The final architecture is: one browser + one native exe, zero external dependencies.

**Decision log:**
- API keys stored in Windows Credential Manager (never touch the browser)
- All three providers supported: OpenAI, Anthropic, Ollama
- C++ owns all AI logic (system prompts, API formatting, JSON parsing)
- Async request model with background thread + polling (avoids blocking Native Messaging)
- Python backend deleted entirely (no preservation for dev/testing)
- Browser JS simplified to thin Native Messaging client

---

## Architecture

### Before (3 processes)

```
Browser → HTTP → Python Flask → HTTP → AI APIs
                      ↓
               subprocess → automation_service.exe
```

### After (1 process)

```
Browser → Native Messaging → automation_service.exe → HTTP → AI APIs
                                     ↓                          ↓
                              Desktop Automation         Ollama / OpenAI / Anthropic
                              (DXGI, SendInput,
                               UIAutomation)
```

---

## New C++ Components

### `ai_provider.h` / `ai_provider.cpp`

All AI API communication. Replaces `call_openai()`, `call_anthropic()`, and `call_ollama()` from `server.py`.

```cpp
class AIProvider {
public:
    // Send screenshot + UI tree + user request to provider, get actions back
    json GetActions(const std::string& provider,
                    const std::string& screenshotBase64,
                    const json& uiTree,
                    const std::string& userRequest);

private:
    json CallOpenAI(const std::string& screenshot, const json& uiTree, const std::string& request);
    json CallAnthropic(const std::string& screenshot, const json& uiTree, const std::string& request);
    json CallOllama(const std::string& screenshot, const json& uiTree, const std::string& request);

    // Generic WinHTTP helper
    std::string HttpPost(const std::wstring& host, int port, const std::wstring& path,
                         const std::string& body, const std::map<std::string, std::string>& headers,
                         bool useHttps);

    // Parse AI text response into action array
    json ParseActionsFromResponse(const std::string& responseText);

    // System prompt (shared across providers)
    static const std::string SYSTEM_PROMPT;
};
```

### `credential_store.h` / `credential_store.cpp`

Windows Credential Manager wrapper. Replaces `.env` file and localStorage encryption.

```cpp
class CredentialStore {
public:
    bool StoreKey(const std::string& provider, const std::string& apiKey);
    std::string LoadKey(const std::string& provider);
    bool DeleteKey(const std::string& provider);
    bool HasKey(const std::string& provider);
};
```

Uses `CredWriteW` / `CredReadW` / `CredDeleteW` from `wincred.h`. Target names prefixed with `BrowserAI:openai`, `BrowserAI:anthropic`, etc.

### `async_request.h` / `async_request.cpp`

Background thread + polling infrastructure for long-running AI requests.

```cpp
class AsyncRequestManager {
public:
    // Submit work, returns request_id immediately
    std::string Submit(std::function<json()> work);

    // Check status and retrieve result
    json Poll(const std::string& requestId);

    // Cancel a pending/processing request
    bool Cancel(const std::string& requestId);

private:
    struct Request {
        std::string id;
        std::string status;  // "pending", "processing", "complete", "error", "cancelled"
        json result;
        std::atomic<bool> cancelFlag;
    };

    std::mutex mutex_;
    std::map<std::string, std::shared_ptr<Request>> requests_;
    std::thread workerThread_;
    std::queue<std::shared_ptr<Request>> workQueue_;

    void WorkerLoop();
    void CleanupStale();  // Remove results older than 5 minutes
};
```

Single worker thread. One AI request at a time. Second request gets `{"status": "queued"}`.

---

## Modified Components

### `action_executor.h` / `action_executor.cpp`

New members:

```cpp
std::unique_ptr<AIProvider> aiProvider_;
std::unique_ptr<CredentialStore> credentialStore_;
std::unique_ptr<AsyncRequestManager> asyncManager_;
```

New methods:

```cpp
json RequestActions(const json& params);    // submit async AI request
json PollRequest(const json& params);       // check status
json CancelRequest(const json& params);     // cancel pending
json StoreApiKey(const json& params);       // store key in Credential Manager
json GetProviderStatus(const json& params); // report configured providers
```

### `main.cpp`

Register new Native Messaging handlers:

```cpp
messaging.RegisterHandler("get_actions", [&](const json& msg) -> json {
    return executor->RequestActions(msg);
});
messaging.RegisterHandler("poll", [&](const json& msg) -> json {
    return executor->PollRequest(msg);
});
messaging.RegisterHandler("cancel", [&](const json& msg) -> json {
    return executor->CancelRequest(msg);
});
messaging.RegisterHandler("store_api_key", [&](const json& msg) -> json {
    return executor->StoreApiKey(msg);
});
messaging.RegisterHandler("get_provider_status", [&](const json& msg) -> json {
    return executor->GetProviderStatus(msg);
});
```

### `CMakeLists.txt`

Add new source files and link `Advapi32` (for Credential Manager):

```cmake
set(SOURCES
    # ... existing ...
    src/ai_provider.cpp
    src/credential_store.cpp
    src/async_request.cpp
)

target_link_libraries(automation_service
    # ... existing ...
    Advapi32   # For Windows Credential Manager
)
```

---

## Native Messaging Protocol

### New messages

```json
// Store API key (sync)
→ {"action": "store_api_key", "provider": "openai", "api_key": "sk-..."}
← {"success": true}

// Check which providers are configured (sync)
→ {"action": "get_provider_status"}
← {"success": true, "providers": {
     "openai": {"configured": true, "has_key": true},
     "anthropic": {"configured": false, "has_key": false},
     "ollama": {"configured": true, "has_key": false, "available": true}
   }}

// Request AI actions (async — returns immediately)
→ {"action": "get_actions", "provider": "openai", "user_request": "Open Notepad"}
← {"request_id": "a1b2c3", "status": "pending"}

// Poll for result
→ {"action": "poll", "request_id": "a1b2c3"}
← {"request_id": "a1b2c3", "status": "complete", "actions": [...]}

// Cancel
→ {"action": "cancel", "request_id": "a1b2c3"}
← {"request_id": "a1b2c3", "status": "cancelled"}
```

### Unchanged messages (all sync)

`ping`, `get_capabilities`, `capture_screen`, `inspect_ui`, `execute_action`, `execute_actions`, `check_local_llm`

### Key optimization

`get_actions` no longer requires the browser to send a screenshot. The C++ service captures the screen and UI tree internally since it has direct access. This eliminates a full round-trip of base64 screenshot data over Native Messaging.

Optional: browser can pass `"include_screenshot": false` for UI-tree-only reasoning.

---

## Browser JS Changes

### `ai_provider_manager.js` — rewritten

Becomes a thin Native Messaging client:

```javascript
class AIProviderManager {
    async getActions(provider, userRequest) {
        const {request_id} = await this.sendMessage({
            action: 'get_actions', provider, user_request: userRequest
        });
        return this.pollUntilComplete(request_id);
    }

    async storeApiKey(provider, key) {
        return this.sendMessage({
            action: 'store_api_key', provider, api_key: key
        });
    }

    async getProviderStatus() {
        return this.sendMessage({action: 'get_provider_status'});
    }

    async cancelRequest(requestId) {
        return this.sendMessage({action: 'cancel', request_id: requestId});
    }
}
```

### `ai_panel.js` — simplified

- Remove separate capture → send → receive flow
- Single "execute" button sends `get_actions`, polls, displays results
- Settings panel for key entry sends `store_api_key` to C++ service
- No encryption code, no localStorage key handling

### Deleted JS files

- `openai_provider.js`
- `anthropic_provider.js`
- `ollama_provider.js`
- `local_llm_provider.js`
- `ai_provider_interface.js`

---

## Error Handling

### WinHTTP failures
- Connection refused (Ollama not running) → `{"success": false, "error": "Ollama is not running on localhost:11434"}`
- Timeout → 60s for cloud APIs. Return `{"status": "error", "error": "Request timed out"}`
- Invalid API key (401/403) → `"Invalid API key for openai. Update via settings."`
- Rate limited by provider (429) → return the error, let browser show it

### Credential Manager failures
- `CredWrite` fails → return error, suggest running as admin
- Key not found → `{"has_key": false}`, browser shows setup prompt

### Async request edge cases
- Poll for non-existent request_id → `{"status": "not_found"}`
- Browser disconnects mid-request → worker finishes, stale results cleaned after 5 minutes
- Multiple `get_actions` requests → queued, one at a time
- Cancel during HTTP call → cancel flag set, HTTP finishes but result discarded

### AI response parsing
- Markdown-fenced JSON (```json ... ```) → strip fences
- Prose instead of JSON → `{"success": false, "error": "AI did not return valid actions", "raw_response": "..."}`
- Empty array → valid, no actions

### Action validation
Same rules already in C++: coordinate bounds, text length (10k), wait duration (0-30s). Applied to AI responses before returning to browser.

---

## Migration Steps

1. Build new C++ components: `ai_provider`, `credential_store`, `async_request`
2. Update `action_executor` and `main.cpp` — wire up new handlers
3. Rebuild and test — verify all new Native Messaging handlers work
4. Simplify browser JS — replace provider classes with thin Native Messaging client, add settings panel for key management
5. Remove localStorage encryption — `_keyEncrypt` goes away, keys never touch browser
6. Delete Python backend — entire `backend/` directory
7. Delete dead code — `stb_image_write.h` stub, individual JS provider files
8. Update CLAUDE.md and docs — reflect new architecture

---

## Files Created
- `automation_service/src/ai_provider.h`
- `automation_service/src/ai_provider.cpp`
- `automation_service/src/credential_store.h`
- `automation_service/src/credential_store.cpp`
- `automation_service/src/async_request.h`
- `automation_service/src/async_request.cpp`

## Files Modified
- `automation_service/src/action_executor.h`
- `automation_service/src/action_executor.cpp`
- `automation_service/src/main.cpp`
- `automation_service/CMakeLists.txt`
- `src/chrome/browser/ui/webui/ai_panel/resources/ai_panel.js`
- `src/chrome/browser/ui/webui/ai_panel/resources/ai_provider_manager.js`
- `CLAUDE.md`

## Files Deleted
- `backend/` (entire directory)
- `src/.../openai_provider.js`
- `src/.../anthropic_provider.js`
- `src/.../ollama_provider.js`
- `src/.../local_llm_provider.js`
- `src/.../ai_provider_interface.js`
- `automation_service/third_party/stb/stb_image_write.h`
