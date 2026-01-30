# Eliminate Python Backend — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove the Python Flask backend entirely and move AI provider routing, credential storage, and async request management into the C++ automation service.

**Architecture:** The C++ automation service gains three new modules: `credential_store` (Windows Credential Manager for API keys), `ai_provider` (WinHTTP calls to OpenAI/Anthropic/Ollama), and `async_request` (background thread + polling for long AI calls). The browser JS is simplified to a thin Native Messaging client. The Python `backend/` directory is deleted entirely.

**Tech Stack:** C++17 (WinHTTP, wincred.h, std::thread), nlohmann/json, Windows SDK

---

## Task 1: Create CredentialStore

**Files:**
- Create: `automation_service/src/credential_store.h`
- Create: `automation_service/src/credential_store.cpp`

**Step 1: Create the header**

Create `automation_service/src/credential_store.h`:

```cpp
#pragma once

#include "common.h"
#include <string>

/**
 * Credential Store
 *
 * Wraps Windows Credential Manager (CredWrite/CredRead/CredDelete)
 * to securely store API keys for AI providers.
 * Keys are stored per-user, encrypted by the OS.
 */
class CredentialStore {
public:
    CredentialStore() = default;
    ~CredentialStore() = default;

    // Store an API key for a provider. Overwrites if exists.
    bool StoreKey(const std::string& provider, const std::string& apiKey);

    // Load an API key. Returns empty string if not found.
    std::string LoadKey(const std::string& provider);

    // Delete a stored key. Returns true if deleted or didn't exist.
    bool DeleteKey(const std::string& provider);

    // Check if a key exists for a provider.
    bool HasKey(const std::string& provider);

private:
    // Build the credential target name: "BrowserAI:<provider>"
    std::wstring MakeTarget(const std::string& provider) const;
};
```

**Step 2: Create the implementation**

Create `automation_service/src/credential_store.cpp`:

```cpp
#include "credential_store.h"
#include <wincred.h>

#pragma comment(lib, "Advapi32.lib")

std::wstring CredentialStore::MakeTarget(const std::string& provider) const {
    return L"BrowserAI:" + StringToWString(provider);
}

bool CredentialStore::StoreKey(const std::string& provider, const std::string& apiKey) {
    std::wstring target = MakeTarget(provider);

    CREDENTIALW cred = {};
    cred.Type = CRED_TYPE_GENERIC;
    cred.TargetName = const_cast<LPWSTR>(target.c_str());
    cred.CredentialBlobSize = static_cast<DWORD>(apiKey.size());
    cred.CredentialBlob = reinterpret_cast<LPBYTE>(const_cast<char*>(apiKey.data()));
    cred.Persist = CRED_PERSIST_LOCAL_MACHINE;

    std::wstring username = L"BrowserAI_" + StringToWString(provider);
    cred.UserName = const_cast<LPWSTR>(username.c_str());

    if (!CredWriteW(&cred, 0)) {
        LOG_ERROR(L"CredWriteW failed for " << target.c_str()
                  << L", error: " << GetLastError());
        return false;
    }

    LOG_INFO(L"Stored API key for " << StringToWString(provider).c_str());
    return true;
}

std::string CredentialStore::LoadKey(const std::string& provider) {
    std::wstring target = MakeTarget(provider);

    PCREDENTIALW pCred = nullptr;
    if (!CredReadW(target.c_str(), CRED_TYPE_GENERIC, 0, &pCred)) {
        return "";
    }

    std::string key(reinterpret_cast<char*>(pCred->CredentialBlob),
                    pCred->CredentialBlobSize);
    CredFree(pCred);
    return key;
}

bool CredentialStore::DeleteKey(const std::string& provider) {
    std::wstring target = MakeTarget(provider);
    if (!CredDeleteW(target.c_str(), CRED_TYPE_GENERIC, 0)) {
        DWORD err = GetLastError();
        if (err == ERROR_NOT_FOUND) {
            return true;  // Already gone
        }
        LOG_ERROR(L"CredDeleteW failed, error: " << err);
        return false;
    }
    return true;
}

bool CredentialStore::HasKey(const std::string& provider) {
    std::wstring target = MakeTarget(provider);
    PCREDENTIALW pCred = nullptr;
    if (!CredReadW(target.c_str(), CRED_TYPE_GENERIC, 0, &pCred)) {
        return false;
    }
    CredFree(pCred);
    return true;
}
```

**Step 3: Add to CMakeLists.txt**

In `automation_service/CMakeLists.txt`, add `src/credential_store.cpp` to SOURCES, `src/credential_store.h` to HEADERS, and `Advapi32` to target_link_libraries.

**Step 4: Build to verify compilation**

```bash
cd automation_service/build
cmake ..
cmake --build . --config Release
```

Expected: Compiles with no errors. `CredentialStore` is not yet called from anywhere.

**Step 5: Commit**

```bash
git add automation_service/src/credential_store.h automation_service/src/credential_store.cpp automation_service/CMakeLists.txt
git commit -m "feat: add CredentialStore for Windows Credential Manager API key storage"
```

---

## Task 2: Create HTTP client helper

**Files:**
- Create: `automation_service/src/http_client.h`
- Create: `automation_service/src/http_client.cpp`

This extracts and generalizes the WinHTTP boilerplate from `CheckLocalLLM()` into a reusable helper so all three AI providers can use it.

**Step 1: Create the header**

Create `automation_service/src/http_client.h`:

```cpp
#pragma once

#include "common.h"
#include <string>
#include <map>

/**
 * HTTP Client
 *
 * Simple WinHTTP wrapper for making GET/POST requests.
 * Used by AIProvider to call OpenAI, Anthropic, and Ollama APIs.
 */

struct HttpResponse {
    int statusCode;
    std::string body;
    std::string error;
    bool success;
};

class HttpClient {
public:
    HttpClient() = default;
    ~HttpClient() = default;

    // POST with JSON body and custom headers. Set useHttps=true for cloud APIs.
    HttpResponse Post(const std::wstring& host, int port, const std::wstring& path,
                      const std::string& body,
                      const std::map<std::string, std::string>& headers,
                      bool useHttps = false,
                      int timeoutMs = 60000);

    // GET with optional headers.
    HttpResponse Get(const std::wstring& host, int port, const std::wstring& path,
                     bool useHttps = false,
                     int timeoutMs = 5000);

private:
    // Read full response body from an open request handle
    std::string ReadResponseBody(void* hRequest);
};
```

**Step 2: Create the implementation**

Create `automation_service/src/http_client.cpp`:

```cpp
#include "http_client.h"
#include <winhttp.h>
#include <vector>
#include <sstream>

#pragma comment(lib, "Winhttp.lib")

std::string HttpClient::ReadResponseBody(void* hRequest) {
    std::string body;
    DWORD bytesAvailable = 0;
    while (WinHttpQueryDataAvailable(static_cast<HINTERNET>(hRequest), &bytesAvailable)
           && bytesAvailable > 0) {
        std::vector<char> buf(bytesAvailable);
        DWORD bytesRead = 0;
        WinHttpReadData(static_cast<HINTERNET>(hRequest),
                        buf.data(), bytesAvailable, &bytesRead);
        body.append(buf.data(), bytesRead);
    }
    return body;
}

HttpResponse HttpClient::Post(const std::wstring& host, int port, const std::wstring& path,
                               const std::string& body,
                               const std::map<std::string, std::string>& headers,
                               bool useHttps, int timeoutMs) {
    HttpResponse resp = {0, "", "", false};

    HINTERNET hSession = WinHttpOpen(L"BrowserAI/1.0",
        WINHTTP_ACCESS_TYPE_NO_PROXY,
        WINHTTP_NO_PROXY_NAME, WINHTTP_NO_PROXY_BYPASS, 0);
    if (!hSession) {
        resp.error = "Failed to create HTTP session";
        return resp;
    }

    HINTERNET hConnect = WinHttpConnect(hSession, host.c_str(),
        static_cast<INTERNET_PORT>(port), 0);
    if (!hConnect) {
        WinHttpCloseHandle(hSession);
        resp.error = "Failed to connect to " + std::string(host.begin(), host.end());
        return resp;
    }

    DWORD flags = useHttps ? WINHTTP_FLAG_SECURE : 0;
    HINTERNET hRequest = WinHttpOpenRequest(hConnect, L"POST", path.c_str(),
        nullptr, WINHTTP_NO_REFERER, WINHTTP_DEFAULT_ACCEPT_TYPES, flags);
    if (!hRequest) {
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        resp.error = "Failed to create request";
        return resp;
    }

    // Set timeouts
    DWORD timeout = static_cast<DWORD>(timeoutMs);
    WinHttpSetOption(hRequest, WINHTTP_OPTION_CONNECT_TIMEOUT, &timeout, sizeof(timeout));
    WinHttpSetOption(hRequest, WINHTTP_OPTION_SEND_TIMEOUT, &timeout, sizeof(timeout));
    WinHttpSetOption(hRequest, WINHTTP_OPTION_RECEIVE_TIMEOUT, &timeout, sizeof(timeout));

    // Build header string
    std::wstring headerStr;
    for (const auto& [key, val] : headers) {
        headerStr += StringToWString(key) + L": " + StringToWString(val) + L"\r\n";
    }
    headerStr += L"Content-Type: application/json\r\n";

    BOOL sent = WinHttpSendRequest(hRequest,
        headerStr.c_str(), static_cast<DWORD>(headerStr.length()),
        const_cast<char*>(body.c_str()), static_cast<DWORD>(body.size()),
        static_cast<DWORD>(body.size()), 0);

    if (!sent || !WinHttpReceiveResponse(hRequest, nullptr)) {
        DWORD err = GetLastError();
        WinHttpCloseHandle(hRequest);
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        resp.error = "HTTP request failed (error " + std::to_string(err) + ")";
        return resp;
    }

    // Get status code
    DWORD statusCode = 0;
    DWORD statusSize = sizeof(statusCode);
    WinHttpQueryHeaders(hRequest,
        WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
        WINHTTP_HEADER_NAME_BY_INDEX, &statusCode, &statusSize,
        WINHTTP_NO_HEADER_INDEX);
    resp.statusCode = static_cast<int>(statusCode);

    // Read body
    resp.body = ReadResponseBody(hRequest);

    WinHttpCloseHandle(hRequest);
    WinHttpCloseHandle(hConnect);
    WinHttpCloseHandle(hSession);

    resp.success = (resp.statusCode >= 200 && resp.statusCode < 300);
    if (!resp.success && resp.error.empty()) {
        resp.error = "HTTP " + std::to_string(resp.statusCode);
    }
    return resp;
}

HttpResponse HttpClient::Get(const std::wstring& host, int port, const std::wstring& path,
                              bool useHttps, int timeoutMs) {
    HttpResponse resp = {0, "", "", false};

    HINTERNET hSession = WinHttpOpen(L"BrowserAI/1.0",
        WINHTTP_ACCESS_TYPE_NO_PROXY,
        WINHTTP_NO_PROXY_NAME, WINHTTP_NO_PROXY_BYPASS, 0);
    if (!hSession) {
        resp.error = "Failed to create HTTP session";
        return resp;
    }

    HINTERNET hConnect = WinHttpConnect(hSession, host.c_str(),
        static_cast<INTERNET_PORT>(port), 0);
    if (!hConnect) {
        WinHttpCloseHandle(hSession);
        resp.error = "Failed to connect";
        return resp;
    }

    DWORD flags = useHttps ? WINHTTP_FLAG_SECURE : 0;
    HINTERNET hRequest = WinHttpOpenRequest(hConnect, L"GET", path.c_str(),
        nullptr, WINHTTP_NO_REFERER, WINHTTP_DEFAULT_ACCEPT_TYPES, flags);
    if (!hRequest) {
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        resp.error = "Failed to create request";
        return resp;
    }

    DWORD timeout = static_cast<DWORD>(timeoutMs);
    WinHttpSetOption(hRequest, WINHTTP_OPTION_CONNECT_TIMEOUT, &timeout, sizeof(timeout));
    WinHttpSetOption(hRequest, WINHTTP_OPTION_RECEIVE_TIMEOUT, &timeout, sizeof(timeout));

    BOOL sent = WinHttpSendRequest(hRequest, WINHTTP_NO_ADDITIONAL_HEADERS, 0,
        WINHTTP_NO_REQUEST_DATA, 0, 0, 0);

    if (!sent || !WinHttpReceiveResponse(hRequest, nullptr)) {
        WinHttpCloseHandle(hRequest);
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        resp.error = "HTTP GET request failed";
        return resp;
    }

    DWORD statusCode = 0;
    DWORD statusSize = sizeof(statusCode);
    WinHttpQueryHeaders(hRequest,
        WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
        WINHTTP_HEADER_NAME_BY_INDEX, &statusCode, &statusSize,
        WINHTTP_NO_HEADER_INDEX);
    resp.statusCode = static_cast<int>(statusCode);

    resp.body = ReadResponseBody(hRequest);

    WinHttpCloseHandle(hRequest);
    WinHttpCloseHandle(hConnect);
    WinHttpCloseHandle(hSession);

    resp.success = (resp.statusCode >= 200 && resp.statusCode < 300);
    return resp;
}
```

**Step 3: Add to CMakeLists.txt**

Add `src/http_client.cpp` to SOURCES and `src/http_client.h` to HEADERS. (Winhttp is already linked from earlier.)

**Step 4: Build**

```bash
cd automation_service/build
cmake ..
cmake --build . --config Release
```

Expected: Compiles. `HttpClient` not called yet.

**Step 5: Commit**

```bash
git add automation_service/src/http_client.h automation_service/src/http_client.cpp automation_service/CMakeLists.txt
git commit -m "feat: add HttpClient WinHTTP wrapper for AI provider API calls"
```

---

## Task 3: Create AIProvider

**Files:**
- Create: `automation_service/src/ai_provider.h`
- Create: `automation_service/src/ai_provider.cpp`

Ports `call_openai()`, `call_anthropic()`, `call_ollama()` from `backend/server.py` into C++.

**Step 1: Create the header**

Create `automation_service/src/ai_provider.h`:

```cpp
#pragma once

#include "common.h"
#include "http_client.h"
#include "credential_store.h"
#include <nlohmann/json.hpp>
#include <string>

using json = nlohmann::json;

/**
 * AI Provider
 *
 * Routes AI requests to OpenAI, Anthropic, or Ollama.
 * Owns the system prompt, builds provider-specific payloads,
 * and parses AI text responses into action arrays.
 */
class AIProvider {
public:
    AIProvider(CredentialStore& credStore);
    ~AIProvider() = default;

    // Main entry point: get actions from an AI provider.
    // screenshotBase64 and uiTree are captured internally by caller.
    json GetActions(const std::string& provider,
                    const std::string& screenshotBase64,
                    const json& uiTree,
                    const std::string& userRequest);

    // Get status of all providers (which have keys configured, which are available)
    json GetProviderStatus();

private:
    CredentialStore& credStore_;
    HttpClient http_;

    json CallOpenAI(const std::string& apiKey,
                    const std::string& screenshot,
                    const json& uiTree,
                    const std::string& request);

    json CallAnthropic(const std::string& apiKey,
                       const std::string& screenshot,
                       const json& uiTree,
                       const std::string& request);

    json CallOllama(const std::string& screenshot,
                    const json& uiTree,
                    const std::string& request);

    // Parse AI text response into validated action array.
    // Strips markdown fences, parses JSON, validates each action.
    json ParseActionsFromResponse(const std::string& responseText);

    // Validate a single action (bounds, types, limits)
    bool ValidateAction(const json& action);

    // The system prompt shared by all providers
    static const std::string SYSTEM_PROMPT;
};
```

**Step 2: Create the implementation**

Create `automation_service/src/ai_provider.cpp`:

```cpp
#include "ai_provider.h"
#include <sstream>
#include <algorithm>
#include <set>

const std::string AIProvider::SYSTEM_PROMPT = R"(You are a desktop automation assistant. Analyze the screenshot and UI tree, then return a JSON array of actions to accomplish the user's request.

Available actions:
- click: {"action": "click", "params": {"x": 100, "y": 200}, "confidence": 0.9}
- type: {"action": "type", "params": {"text": "hello"}, "confidence": 0.9}
- press_keys: {"action": "press_keys", "params": {"keys": ["ctrl", "s"]}, "confidence": 0.9}
- scroll: {"action": "scroll", "params": {"delta": -3, "x": 500, "y": 400}, "confidence": 0.9}
- wait: {"action": "wait", "params": {"ms": 1000}, "confidence": 0.9}

UI TREE USAGE:
- Search for elements by name/type in the UI tree
- Use element 'bounds' {x, y, width, height} to calculate click coordinates
- Click center of element: x + width/2, y + height/2

Return ONLY a JSON array of actions. No explanations or other text.)";


AIProvider::AIProvider(CredentialStore& credStore)
    : credStore_(credStore) {}


json AIProvider::GetActions(const std::string& provider,
                            const std::string& screenshotBase64,
                            const json& uiTree,
                            const std::string& userRequest) {
    if (provider == "openai") {
        std::string key = credStore_.LoadKey("openai");
        if (key.empty()) {
            return {{"success", false}, {"error", "OpenAI API key not configured. Add via Settings."}};
        }
        return CallOpenAI(key, screenshotBase64, uiTree, userRequest);
    }

    if (provider == "anthropic") {
        std::string key = credStore_.LoadKey("anthropic");
        if (key.empty()) {
            return {{"success", false}, {"error", "Anthropic API key not configured. Add via Settings."}};
        }
        return CallAnthropic(key, screenshotBase64, uiTree, userRequest);
    }

    if (provider == "ollama") {
        return CallOllama(screenshotBase64, uiTree, userRequest);
    }

    return {{"success", false}, {"error", "Unknown provider: " + provider}};
}


json AIProvider::GetProviderStatus() {
    // Check Ollama availability via HTTP GET
    HttpResponse ollamaResp = http_.Get(L"localhost", 11434, L"/api/tags");

    return {
        {"success", true},
        {"providers", {
            {"openai", {
                {"has_key", credStore_.HasKey("openai")},
                {"type", "cloud"}
            }},
            {"anthropic", {
                {"has_key", credStore_.HasKey("anthropic")},
                {"type", "cloud"}
            }},
            {"ollama", {
                {"has_key", false},
                {"type", "local"},
                {"available", ollamaResp.success}
            }}
        }}
    };
}


json AIProvider::CallOpenAI(const std::string& apiKey,
                             const std::string& screenshot,
                             const json& uiTree,
                             const std::string& request) {
    json payload = {
        {"model", "gpt-4o"},
        {"max_tokens", 1000},
        {"messages", json::array({
            {{"role", "system"}, {"content", SYSTEM_PROMPT}},
            {{"role", "user"}, {"content", json::array({
                {{"type", "text"},
                 {"text", "User request: " + request + "\n\nUI Tree: " + uiTree.dump(2)}},
                {{"type", "image_url"},
                 {"image_url", {{"url", "data:image/png;base64," + screenshot}}}}
            })}}
        })}
    };

    std::map<std::string, std::string> headers = {
        {"Authorization", "Bearer " + apiKey}
    };

    HttpResponse resp = http_.Post(L"api.openai.com", 443,
        L"/v1/chat/completions", payload.dump(), headers, true);

    if (!resp.success) {
        std::string errMsg = "OpenAI API error: " + resp.error;
        if (resp.statusCode == 401) errMsg = "Invalid OpenAI API key. Update via Settings.";
        if (resp.statusCode == 429) errMsg = "OpenAI rate limit exceeded. Try again later.";
        return {{"success", false}, {"error", errMsg}};
    }

    try {
        json result = json::parse(resp.body);
        std::string content = result["choices"][0]["message"]["content"];
        return ParseActionsFromResponse(content);
    } catch (const std::exception& e) {
        return {{"success", false}, {"error", std::string("Failed to parse OpenAI response: ") + e.what()}};
    }
}


json AIProvider::CallAnthropic(const std::string& apiKey,
                                const std::string& screenshot,
                                const json& uiTree,
                                const std::string& request) {
    json payload = {
        {"model", "claude-sonnet-4-20250514"},
        {"max_tokens", 1024},
        {"messages", json::array({
            {{"role", "user"}, {"content", json::array({
                {{"type", "image"},
                 {"source", {{"type", "base64"}, {"media_type", "image/png"}, {"data", screenshot}}}},
                {{"type", "text"},
                 {"text", SYSTEM_PROMPT + "\n\nUser request: " + request + "\n\nUI Tree: " + uiTree.dump()}}
            })}}
        })}
    };

    std::map<std::string, std::string> headers = {
        {"x-api-key", apiKey},
        {"anthropic-version", "2023-06-01"}
    };

    HttpResponse resp = http_.Post(L"api.anthropic.com", 443,
        L"/v1/messages", payload.dump(), headers, true);

    if (!resp.success) {
        std::string errMsg = "Anthropic API error: " + resp.error;
        if (resp.statusCode == 401) errMsg = "Invalid Anthropic API key. Update via Settings.";
        if (resp.statusCode == 429) errMsg = "Anthropic rate limit exceeded. Try again later.";
        return {{"success", false}, {"error", errMsg}};
    }

    try {
        json result = json::parse(resp.body);
        std::string content = result["content"][0]["text"];
        return ParseActionsFromResponse(content);
    } catch (const std::exception& e) {
        return {{"success", false}, {"error", std::string("Failed to parse Anthropic response: ") + e.what()}};
    }
}


json AIProvider::CallOllama(const std::string& screenshot,
                             const json& uiTree,
                             const std::string& request) {
    std::string prompt = SYSTEM_PROMPT + "\n\nUser request: " + request
                         + "\n\nUI Tree:\n" + uiTree.dump(2);

    json payload = {
        {"model", "llava"},
        {"prompt", prompt},
        {"stream", false}
    };

    if (!screenshot.empty()) {
        payload["images"] = json::array({screenshot});
    }

    HttpResponse resp = http_.Post(L"localhost", 11434,
        L"/api/generate", payload.dump(), {}, false, 120000);  // 2min timeout for local inference

    if (!resp.success) {
        return {{"success", false},
                {"error", "Ollama error: " + resp.error + ". Is Ollama running?"}};
    }

    try {
        json result = json::parse(resp.body);
        std::string content = result.value("response", "");
        return ParseActionsFromResponse(content);
    } catch (const std::exception& e) {
        return {{"success", false}, {"error", std::string("Failed to parse Ollama response: ") + e.what()}};
    }
}


json AIProvider::ParseActionsFromResponse(const std::string& responseText) {
    std::string text = responseText;

    // Trim whitespace
    auto ltrim = text.find_first_not_of(" \t\n\r");
    if (ltrim != std::string::npos) text = text.substr(ltrim);
    auto rtrim = text.find_last_not_of(" \t\n\r");
    if (rtrim != std::string::npos) text = text.substr(0, rtrim + 1);

    // Strip markdown code fences
    if (text.rfind("```", 0) == 0) {
        auto firstNewline = text.find('\n');
        if (firstNewline != std::string::npos) {
            text = text.substr(firstNewline + 1);
        }
        auto lastFence = text.rfind("```");
        if (lastFence != std::string::npos) {
            text = text.substr(0, lastFence);
        }
        // Trim again
        ltrim = text.find_first_not_of(" \t\n\r");
        if (ltrim != std::string::npos) text = text.substr(ltrim);
        rtrim = text.find_last_not_of(" \t\n\r");
        if (rtrim != std::string::npos) text = text.substr(0, rtrim + 1);
    }

    // Parse JSON
    json actions;
    try {
        actions = json::parse(text);
    } catch (...) {
        return {{"success", false},
                {"error", "AI did not return valid JSON"},
                {"raw_response", responseText}};
    }

    if (!actions.is_array()) {
        return {{"success", false},
                {"error", "AI response is not an array of actions"},
                {"raw_response", responseText}};
    }

    // Validate each action
    json validated = json::array();
    static const std::set<std::string> validTypes = {"click", "type", "scroll", "press_keys", "wait"};

    for (const auto& action : actions) {
        if (!action.is_object()) continue;
        if (!action.contains("action")) continue;
        std::string type = action["action"];
        if (validTypes.find(type) == validTypes.end()) continue;
        if (!ValidateAction(action)) continue;

        // Add default confidence if missing
        json validated_action = action;
        if (!validated_action.contains("confidence")) {
            validated_action["confidence"] = 0.7;
        }
        validated.push_back(validated_action);
    }

    if (validated.empty()) {
        return {{"success", false},
                {"error", "AI returned no valid actions"},
                {"raw_response", responseText}};
    }

    return {{"success", true}, {"actions", validated}};
}


bool AIProvider::ValidateAction(const json& action) {
    std::string type = action["action"];
    json params = action.value("params", json::object());

    if (type == "click") {
        if (!params.contains("x") || !params.contains("y")) return false;
        auto x = params["x"];
        auto y = params["y"];
        if (!x.is_number() || !y.is_number()) return false;
        if (x.get<double>() < 0 || x.get<double>() > 10000) return false;
        if (y.get<double>() < 0 || y.get<double>() > 10000) return false;
    }

    if (type == "type") {
        if (!params.contains("text")) return false;
        if (!params["text"].is_string()) return false;
        std::string text = params["text"];
        if (text.empty() || text.length() > 10000) return false;
    }

    if (type == "wait") {
        if (!params.contains("ms")) return false;
        if (!params["ms"].is_number()) return false;
        double ms = params["ms"].get<double>();
        if (ms < 0 || ms > 30000) return false;
    }

    if (type == "scroll") {
        if (!params.contains("delta")) return false;
        if (!params["delta"].is_number()) return false;
    }

    if (type == "press_keys") {
        if (!params.contains("keys")) return false;
        if (!params["keys"].is_array() || params["keys"].empty()) return false;
    }

    return true;
}
```

**Step 3: Add to CMakeLists.txt**

Add `src/ai_provider.cpp` to SOURCES and `src/ai_provider.h` to HEADERS.

**Step 4: Build**

```bash
cd automation_service/build
cmake ..
cmake --build . --config Release
```

Expected: Compiles. Not yet wired up.

**Step 5: Commit**

```bash
git add automation_service/src/ai_provider.h automation_service/src/ai_provider.cpp automation_service/CMakeLists.txt
git commit -m "feat: add AIProvider with OpenAI, Anthropic, and Ollama support via WinHTTP"
```

---

## Task 4: Create AsyncRequestManager

**Files:**
- Create: `automation_service/src/async_request.h`
- Create: `automation_service/src/async_request.cpp`

**Step 1: Create the header**

Create `automation_service/src/async_request.h`:

```cpp
#pragma once

#include "common.h"
#include <nlohmann/json.hpp>
#include <string>
#include <map>
#include <queue>
#include <mutex>
#include <thread>
#include <functional>
#include <atomic>
#include <condition_variable>
#include <chrono>
#include <random>

using json = nlohmann::json;

/**
 * Async Request Manager
 *
 * Manages background execution of long-running AI requests.
 * Single worker thread processes one request at a time.
 * Browser polls for results via request IDs.
 */
class AsyncRequestManager {
public:
    AsyncRequestManager();
    ~AsyncRequestManager();

    // Submit work. Returns a request_id immediately.
    std::string Submit(std::function<json()> work);

    // Poll for result. Returns status and result if complete.
    json Poll(const std::string& requestId);

    // Cancel a pending or in-progress request.
    json Cancel(const std::string& requestId);

    // Shut down the worker thread.
    void Shutdown();

private:
    struct Request {
        std::string id;
        std::string status;  // "queued", "processing", "complete", "error", "cancelled"
        json result;
        std::atomic<bool> cancelFlag{false};
        std::function<json()> work;
        std::chrono::steady_clock::time_point completedAt;
    };

    std::mutex mutex_;
    std::condition_variable cv_;
    std::map<std::string, std::shared_ptr<Request>> requests_;
    std::queue<std::shared_ptr<Request>> workQueue_;
    std::thread workerThread_;
    std::atomic<bool> running_{true};

    void WorkerLoop();
    void CleanupStale();
    std::string GenerateId();
};
```

**Step 2: Create the implementation**

Create `automation_service/src/async_request.cpp`:

```cpp
#include "async_request.h"
#include <sstream>
#include <iomanip>

AsyncRequestManager::AsyncRequestManager() {
    workerThread_ = std::thread(&AsyncRequestManager::WorkerLoop, this);
}

AsyncRequestManager::~AsyncRequestManager() {
    Shutdown();
}

void AsyncRequestManager::Shutdown() {
    running_ = false;
    cv_.notify_all();
    if (workerThread_.joinable()) {
        workerThread_.join();
    }
}

std::string AsyncRequestManager::GenerateId() {
    static std::mt19937 rng(std::random_device{}());
    static const char chars[] = "abcdefghijklmnopqrstuvwxyz0123456789";
    std::string id;
    id.reserve(8);
    for (int i = 0; i < 8; ++i) {
        id += chars[rng() % (sizeof(chars) - 1)];
    }
    return id;
}

std::string AsyncRequestManager::Submit(std::function<json()> work) {
    std::lock_guard<std::mutex> lock(mutex_);

    CleanupStale();

    auto req = std::make_shared<Request>();
    req->id = GenerateId();
    req->status = "queued";
    req->work = std::move(work);

    requests_[req->id] = req;
    workQueue_.push(req);
    cv_.notify_one();

    return req->id;
}

json AsyncRequestManager::Poll(const std::string& requestId) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = requests_.find(requestId);
    if (it == requests_.end()) {
        return {{"request_id", requestId}, {"status", "not_found"}};
    }

    auto& req = it->second;
    json response = {{"request_id", requestId}, {"status", req->status}};

    if (req->status == "complete" || req->status == "error") {
        response["result"] = req->result;
        // Merge actions into top level for convenience
        if (req->result.contains("actions")) {
            response["actions"] = req->result["actions"];
        }
        if (req->result.contains("error")) {
            response["error"] = req->result["error"];
        }
    }

    return response;
}

json AsyncRequestManager::Cancel(const std::string& requestId) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = requests_.find(requestId);
    if (it == requests_.end()) {
        return {{"request_id", requestId}, {"status", "not_found"}};
    }

    auto& req = it->second;
    if (req->status == "queued") {
        req->status = "cancelled";
    } else if (req->status == "processing") {
        req->cancelFlag = true;
        // Worker will check the flag and discard result
    }
    // If already complete/error/cancelled, no-op

    return {{"request_id", requestId}, {"status", req->status}};
}

void AsyncRequestManager::WorkerLoop() {
    LOG_INFO(L"AsyncRequestManager worker thread started");

    while (running_) {
        std::shared_ptr<Request> req;

        {
            std::unique_lock<std::mutex> lock(mutex_);
            cv_.wait(lock, [this] { return !running_ || !workQueue_.empty(); });

            if (!running_) break;
            if (workQueue_.empty()) continue;

            req = workQueue_.front();
            workQueue_.pop();

            if (req->status == "cancelled") continue;
            req->status = "processing";
        }

        // Execute work outside lock
        try {
            json result = req->work();

            std::lock_guard<std::mutex> lock(mutex_);
            if (req->cancelFlag) {
                req->status = "cancelled";
            } else {
                req->status = result.value("success", false) ? "complete" : "error";
                req->result = result;
            }
        } catch (const std::exception& e) {
            std::lock_guard<std::mutex> lock(mutex_);
            req->status = "error";
            req->result = {{"success", false}, {"error", e.what()}};
        }

        req->completedAt = std::chrono::steady_clock::now();
    }

    LOG_INFO(L"AsyncRequestManager worker thread stopped");
}

void AsyncRequestManager::CleanupStale() {
    // Called under lock. Remove completed/error/cancelled entries older than 5 minutes.
    auto now = std::chrono::steady_clock::now();
    auto cutoff = std::chrono::minutes(5);

    for (auto it = requests_.begin(); it != requests_.end(); ) {
        auto& req = it->second;
        bool isFinished = (req->status == "complete" || req->status == "error" || req->status == "cancelled");
        if (isFinished && (now - req->completedAt) > cutoff) {
            it = requests_.erase(it);
        } else {
            ++it;
        }
    }
}
```

**Step 3: Add to CMakeLists.txt**

Add `src/async_request.cpp` to SOURCES and `src/async_request.h` to HEADERS.

**Step 4: Build**

```bash
cd automation_service/build
cmake ..
cmake --build . --config Release
```

Expected: Compiles. Not yet wired up.

**Step 5: Commit**

```bash
git add automation_service/src/async_request.h automation_service/src/async_request.cpp automation_service/CMakeLists.txt
git commit -m "feat: add AsyncRequestManager for background AI request processing"
```

---

## Task 5: Wire everything into ActionExecutor and main.cpp

**Files:**
- Modify: `automation_service/src/action_executor.h`
- Modify: `automation_service/src/action_executor.cpp`
- Modify: `automation_service/src/main.cpp`

**Step 1: Update action_executor.h**

Add includes and new members/methods. The new header should be:

```cpp
#pragma once

#include "common.h"
#include "ui_automation.h"
#include "screen_capture.h"
#include "input_controller.h"
#include "credential_store.h"
#include "ai_provider.h"
#include "async_request.h"
#include <nlohmann/json.hpp>
#include <memory>

using json = nlohmann::json;

class ActionExecutor {
public:
    ActionExecutor();
    ~ActionExecutor();

    bool Initialize();

    // Existing handlers (sync)
    json ExecuteAction(const json& action);
    json ExecuteActions(const json& actions);
    json GetCapabilities();
    json CaptureScreen();
    json GetUITree();
    json CheckLocalLLM();

    // New handlers
    json RequestActions(const json& params);      // async: submit AI request
    json PollRequest(const json& params);          // async: check status
    json CancelRequest(const json& params);        // async: cancel
    json StoreApiKey(const json& params);          // sync: store key
    json DeleteApiKey(const json& params);         // sync: delete key
    json GetProviderStatus(const json& params);    // sync: provider info

private:
    std::unique_ptr<UIAutomation> uiAutomation_;
    std::unique_ptr<ScreenCapture> screenCapture_;
    std::unique_ptr<InputController> inputController_;
    std::unique_ptr<CredentialStore> credentialStore_;
    std::unique_ptr<AIProvider> aiProvider_;
    std::unique_ptr<AsyncRequestManager> asyncManager_;

    bool initialized_;

    json ExecuteClick(const json& params);
    json ExecuteType(const json& params);
    json ExecuteScroll(const json& params);
    json ExecutePressKeys(const json& params);
    json ExecuteWait(const json& params);
    MouseButton ParseMouseButton(const std::string& buttonStr);
    WORD ParseVirtualKey(const std::string& keyStr);
};
```

**Step 2: Update action_executor.cpp — constructor and Initialize**

Update the constructor to create the new objects:

```cpp
ActionExecutor::ActionExecutor() : initialized_(false) {
    uiAutomation_ = std::make_unique<UIAutomation>();
    screenCapture_ = std::make_unique<ScreenCapture>();
    inputController_ = std::make_unique<InputController>();
    credentialStore_ = std::make_unique<CredentialStore>();
    aiProvider_ = std::make_unique<AIProvider>(*credentialStore_);
    asyncManager_ = std::make_unique<AsyncRequestManager>();
}
```

**Step 3: Add new handler methods to action_executor.cpp**

Append these methods:

```cpp
json ActionExecutor::RequestActions(const json& params) {
    // Validate
    if (!params.contains("provider") || !params.contains("user_request")) {
        return {{"success", false}, {"error", "Missing provider or user_request"}};
    }

    std::string provider = params["provider"];
    std::string userRequest = params["user_request"];

    if (userRequest.empty() || userRequest.length() > 5000) {
        return {{"success", false}, {"error", "user_request must be 1-5000 chars"}};
    }

    static const std::set<std::string> validProviders = {"openai", "anthropic", "ollama"};
    if (validProviders.find(provider) == validProviders.end()) {
        return {{"success", false}, {"error", "Unknown provider: " + provider}};
    }

    // Capture references for the lambda
    auto* executor = this;

    std::string requestId = asyncManager_->Submit([executor, provider, userRequest]() -> json {
        // Capture screen
        std::string screenshot;
        json uiTree;

        try {
            ImageData pixels = executor->screenCapture_->CaptureScreen();
            if (!pixels.empty()) {
                int w, h;
                executor->screenCapture_->GetScreenDimensions(w, h);
                screenshot = executor->screenCapture_->EncodeToPNG(pixels, w, h);
            }
        } catch (...) {
            LOG_ERROR(L"Screen capture failed during RequestActions");
        }

        try {
            uiTree = executor->uiAutomation_->GetUITree();
        } catch (...) {
            LOG_ERROR(L"UI tree capture failed during RequestActions");
            uiTree = json::object();
        }

        return executor->aiProvider_->GetActions(provider, screenshot, uiTree, userRequest);
    });

    return {{"request_id", requestId}, {"status", "queued"}};
}

json ActionExecutor::PollRequest(const json& params) {
    if (!params.contains("request_id")) {
        return {{"success", false}, {"error", "Missing request_id"}};
    }
    return asyncManager_->Poll(params["request_id"]);
}

json ActionExecutor::CancelRequest(const json& params) {
    if (!params.contains("request_id")) {
        return {{"success", false}, {"error", "Missing request_id"}};
    }
    return asyncManager_->Cancel(params["request_id"]);
}

json ActionExecutor::StoreApiKey(const json& params) {
    if (!params.contains("provider") || !params.contains("api_key")) {
        return {{"success", false}, {"error", "Missing provider or api_key"}};
    }

    std::string provider = params["provider"];
    std::string apiKey = params["api_key"];

    if (provider != "openai" && provider != "anthropic") {
        return {{"success", false}, {"error", "Only openai and anthropic keys are stored"}};
    }

    if (apiKey.empty() || apiKey.length() > 500) {
        return {{"success", false}, {"error", "Invalid API key length"}};
    }

    bool ok = credentialStore_->StoreKey(provider, apiKey);
    return {{"success", ok}};
}

json ActionExecutor::DeleteApiKey(const json& params) {
    if (!params.contains("provider")) {
        return {{"success", false}, {"error", "Missing provider"}};
    }
    bool ok = credentialStore_->DeleteKey(params["provider"]);
    return {{"success", ok}};
}

json ActionExecutor::GetProviderStatus(const json& params) {
    return aiProvider_->GetProviderStatus();
}
```

**Step 4: Refactor CheckLocalLLM to use HttpClient**

Replace the existing `CheckLocalLLM()` body to use the shared `HttpClient` instead of raw WinHTTP. (Optional cleanup — the existing code works. Can be a follow-up.)

**Step 5: Update main.cpp — register new handlers**

Add after the existing handler registrations:

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

    messaging.RegisterHandler("delete_api_key", [&](const json& msg) -> json {
        return executor->DeleteApiKey(msg);
    });

    messaging.RegisterHandler("get_provider_status", [&](const json& msg) -> json {
        return executor->GetProviderStatus(msg);
    });
```

**Step 6: Build**

```bash
cd automation_service/build
cmake ..
cmake --build . --config Release
```

Expected: Compiles and links. All new handlers registered.

**Step 7: Commit**

```bash
git add automation_service/src/action_executor.h automation_service/src/action_executor.cpp automation_service/src/main.cpp
git commit -m "feat: wire AI providers, credentials, and async requests into automation service"
```

---

## Task 6: Simplify browser JavaScript

**Files:**
- Rewrite: `src/chrome/browser/ui/webui/ai_panel/resources/ai_provider_manager.js`
- Modify: `src/chrome/browser/ui/webui/ai_panel/resources/ai_panel.js`
- Modify: `src/chrome/browser/ui/webui/ai_panel/resources/native_messaging_helper.js`
- Delete: `src/chrome/browser/ui/webui/ai_panel/resources/openai_provider.js`
- Delete: `src/chrome/browser/ui/webui/ai_panel/resources/anthropic_provider.js`
- Delete: `src/chrome/browser/ui/webui/ai_panel/resources/ollama_provider.js`
- Delete: `src/chrome/browser/ui/webui/ai_panel/resources/local_llm_provider.js`
- Delete: `src/chrome/browser/ui/webui/ai_panel/resources/ai_provider_interface.js`

**Step 1: Add new methods to NativeMessagingHelper**

Add to `native_messaging_helper.js`:

```javascript
  /**
   * Store an API key in the C++ service (Windows Credential Manager)
   */
  async storeApiKey(provider, apiKey) {
    const response = await this.sendMessage({
      action: 'store_api_key', provider, api_key: apiKey
    });
    if (!response || !response.success) {
      throw new Error(response?.error || 'Failed to store API key');
    }
    return response;
  }

  /**
   * Delete an API key
   */
  async deleteApiKey(provider) {
    return this.sendMessage({action: 'delete_api_key', provider});
  }

  /**
   * Get provider status (which have keys, which are available)
   */
  async getProviderStatus() {
    return this.sendMessage({action: 'get_provider_status'});
  }

  /**
   * Request AI actions (async — returns request_id)
   */
  async requestActions(provider, userRequest) {
    return this.sendMessage({
      action: 'get_actions', provider, user_request: userRequest
    });
  }

  /**
   * Poll for async request result
   */
  async pollRequest(requestId) {
    return this.sendMessage({action: 'poll', request_id: requestId});
  }

  /**
   * Cancel an async request
   */
  async cancelRequest(requestId) {
    return this.sendMessage({action: 'cancel', request_id: requestId});
  }

  /**
   * Poll until a request completes. Returns the final result.
   * @param {string} requestId
   * @param {number} intervalMs - polling interval (default 500ms)
   * @param {number} timeoutMs - max wait time (default 120000ms)
   */
  async pollUntilComplete(requestId, intervalMs = 500, timeoutMs = 120000) {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const result = await this.pollRequest(requestId);
      if (result.status === 'complete' || result.status === 'error' || result.status === 'cancelled') {
        return result;
      }
      await new Promise(r => setTimeout(r, intervalMs));
    }
    // Timeout — try to cancel
    await this.cancelRequest(requestId);
    throw new Error('AI request timed out');
  }
```

**Step 2: Rewrite ai_provider_manager.js**

Replace the entire file with:

```javascript
/**
 * AI Provider Manager
 *
 * Thin wrapper over NativeMessagingHelper for AI provider operations.
 * All AI logic (prompts, API calls, key storage) lives in the C++ service.
 */
class AIProviderManager {
  constructor(nativeMessaging) {
    this.native = nativeMessaging;
    this.activeProvider = 'ollama';
    this.providerStatus = {};
    this.ready = this.initialize();
  }

  async initialize() {
    try {
      const status = await this.native.getProviderStatus();
      if (status.success) {
        this.providerStatus = status.providers;
      }
      // Pick the best available provider
      const saved = localStorage.getItem('ai_provider_preference');
      if (saved && this.providerStatus[saved]) {
        this.activeProvider = saved;
      }
    } catch (e) {
      console.error('Failed to initialize provider manager:', e);
    }
  }

  getActiveProvider() {
    return this.activeProvider;
  }

  setActiveProvider(provider) {
    this.activeProvider = provider;
    localStorage.setItem('ai_provider_preference', provider);
  }

  getProviderStatus() {
    return this.providerStatus;
  }

  async refreshStatus() {
    try {
      const status = await this.native.getProviderStatus();
      if (status.success) {
        this.providerStatus = status.providers;
      }
    } catch (e) {
      console.error('Failed to refresh provider status:', e);
    }
    return this.providerStatus;
  }

  async storeApiKey(provider, apiKey) {
    await this.native.storeApiKey(provider, apiKey);
    await this.refreshStatus();
  }

  async deleteApiKey(provider) {
    await this.native.deleteApiKey(provider);
    await this.refreshStatus();
  }

  /**
   * Request AI actions. Returns actions array.
   * Handles async polling internally.
   */
  async getActions(userRequest) {
    const { request_id } = await this.native.requestActions(
      this.activeProvider, userRequest
    );
    return this.native.pollUntilComplete(request_id);
  }

  async cancelRequest(requestId) {
    return this.native.cancelRequest(requestId);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AIProviderManager };
}
```

**Step 3: Update ai_panel.js**

Key changes to make:
- Constructor creates `NativeMessagingHelper` first, passes to `AIProviderManager`
- `executeAutomation()` calls `this.providerManager.getActions(userRequest)` instead of HTTP fetch
- `saveApiKey()` calls `this.providerManager.storeApiKey(provider, key)`
- Remove all `_keyEncrypt` references
- Remove `updateProviderStatus()` HTTP calls, replace with `this.providerManager.refreshStatus()`
- Remove the `sanitizeRequest()` method (validation now happens in C++)
- Simplify `confirmAndExecuteActions()` to call `this.native.executeActions()`

The DOMContentLoaded handler becomes:

```javascript
document.addEventListener('DOMContentLoaded', async () => {
  const native = new NativeMessagingHelper();
  const panel = new AutomationPanel(native);
  await panel.providerManager.ready;
  panel.initializeUI();
  panel.updateProviderStatus();
  window.automationPanel = panel;
});
```

**Step 4: Delete the old provider JS files**

```bash
rm src/chrome/browser/ui/webui/ai_panel/resources/openai_provider.js
rm src/chrome/browser/ui/webui/ai_panel/resources/anthropic_provider.js
rm src/chrome/browser/ui/webui/ai_panel/resources/ollama_provider.js
rm src/chrome/browser/ui/webui/ai_panel/resources/local_llm_provider.js
rm src/chrome/browser/ui/webui/ai_panel/resources/ai_provider_interface.js
```

**Step 5: Commit**

```bash
git add -A src/chrome/browser/ui/webui/ai_panel/resources/
git commit -m "feat: simplify browser JS to thin Native Messaging client, delete provider classes"
```

---

## Task 7: Delete Python backend and dead code

**Files:**
- Delete: `backend/` (entire directory)
- Delete: `automation_service/third_party/stb/stb_image_write.h`

**Step 1: Remove files**

```bash
rm -rf backend/
rm automation_service/third_party/stb/stb_image_write.h
```

**Step 2: Commit**

```bash
git add -A
git commit -m "chore: delete Python backend and unused stb_image_write stub"
```

---

## Task 8: Update documentation

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Update CLAUDE.md**

Update the Architecture section to reflect the new two-process model. Remove all references to the Python backend, Flask, pip, `.env` files. Update build commands to remove the backend section. Update testing section to remove backend tests. Update the architecture diagram to:

```
Browser (chrome://ai-panel)
    ↓ Native Messaging (stdin/stdout JSON)
C++ Automation Service (automation_service.exe)
    ├── Screen Capture (DXGI/D3D11)
    ├── Input Control (SendInput)
    ├── UI Inspection (UIAutomation)
    ├── AI Providers (OpenAI, Anthropic, Ollama via WinHTTP)
    ├── Credential Store (Windows Credential Manager)
    └── Async Requests (background thread + polling)
```

Update the Dependencies section to remove Python/Flask/requests.

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for new architecture without Python backend"
```

---

## Task 9: Final build and smoke test

**Step 1: Clean rebuild**

```bash
cd automation_service/build
cmake ..
cmake --build . --config Release
```

Expected: Compiles with no errors.

**Step 2: Test ping**

```bash
cd automation_service
python test_ping.py
```

Expected: Ping test passes. (Note: test_ping.py uses subprocess to talk to the exe, doesn't need Python backend.)

**Step 3: Test new handlers manually**

Write a simple Python test script `automation_service/test_new_handlers.py` that sends Native Messaging format messages:

- `{"action": "get_provider_status"}` → expect providers with has_key fields
- `{"action": "store_api_key", "provider": "openai", "api_key": "sk-test123"}` → expect success
- `{"action": "get_provider_status"}` → expect openai.has_key = true
- `{"action": "delete_api_key", "provider": "openai"}` → expect success
- `{"action": "get_actions", "provider": "ollama", "user_request": "Open Notepad"}` → expect request_id
- `{"action": "poll", "request_id": "<from above>"}` → expect status

**Step 4: Commit test script**

```bash
git add automation_service/test_new_handlers.py
git commit -m "test: add smoke test for new Native Messaging handlers"
```

---

## Summary

| Task | What | Files |
|------|------|-------|
| 1 | CredentialStore (Windows Credential Manager) | credential_store.h/cpp |
| 2 | HttpClient (WinHTTP wrapper) | http_client.h/cpp |
| 3 | AIProvider (OpenAI, Anthropic, Ollama) | ai_provider.h/cpp |
| 4 | AsyncRequestManager (background thread + polling) | async_request.h/cpp |
| 5 | Wire into ActionExecutor + main.cpp | action_executor.h/cpp, main.cpp |
| 6 | Simplify browser JS | ai_provider_manager.js, ai_panel.js, native_messaging_helper.js, delete 5 files |
| 7 | Delete Python backend + dead code | rm backend/, rm stb stub |
| 8 | Update docs | CLAUDE.md |
| 9 | Final build + smoke test | rebuild, test_new_handlers.py |
