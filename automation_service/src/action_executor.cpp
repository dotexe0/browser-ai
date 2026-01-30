#include "action_executor.h"
#include <winhttp.h>
#include <set>

ActionExecutor::ActionExecutor() : initialized_(false) {
    uiAutomation_ = std::make_unique<UIAutomation>();
    screenCapture_ = std::make_unique<ScreenCapture>();
    inputController_ = std::make_unique<InputController>();
    credentialStore_ = std::make_unique<CredentialStore>();
    aiProvider_ = std::make_unique<AIProvider>(*credentialStore_);
    asyncManager_ = std::make_unique<AsyncRequestManager>();
}

ActionExecutor::~ActionExecutor() {
}

bool ActionExecutor::Initialize() {
    if (initialized_) {
        return true;
    }
    
    // Initialize UI Automation
    if (!uiAutomation_->Initialize()) {
        LOG_ERROR(L"Failed to initialize UIAutomation");
        return false;
    }
    
    // Initialize Screen Capture
    if (!screenCapture_->Initialize()) {
        LOG_ERROR(L"Failed to initialize Screen Capture");
        return false;
    }
    
    initialized_ = true;
    LOG_INFO(L"Action Executor initialized successfully");
    return true;
}

json ActionExecutor::GetCapabilities() {
    json llmCheck = CheckLocalLLM();
    bool llmAvailable = llmCheck.value("available", false);

    return {
        {"success", true},
        {"capabilities", {
            {"screen_capture", initialized_},
            {"ui_automation", initialized_},
            {"input_control", true},
            {"local_llm", llmAvailable}
        }},
        {"local_llm_info", llmCheck}
    };
}

json ActionExecutor::CaptureScreen() {
    if (!initialized_) {
        return {
            {"success", false},
            {"error", "Action executor not initialized"}
        };
    }
    
    try {
        // Capture screen
        ImageData pixels = screenCapture_->CaptureScreen();
        
        if (pixels.empty()) {
            return {
                {"success", false},
                {"error", "Failed to capture screen"}
            };
        }
        
        // Get dimensions
        int width, height;
        screenCapture_->GetScreenDimensions(width, height);
        
        // Encode to PNG base64
        std::string base64Image = screenCapture_->EncodeToPNG(pixels, width, height);
        
        return {
            {"success", true},
            {"screenshot", base64Image},
            {"width", width},
            {"height", height}
        };
        
    } catch (const std::exception& e) {
        return {
            {"success", false},
            {"error", e.what()}
        };
    }
}

json ActionExecutor::GetUITree() {
    if (!initialized_) {
        return {
            {"success", false},
            {"error", "Action executor not initialized"}
        };
    }
    
    try {
        json tree = uiAutomation_->GetUITree();
        
        return {
            {"success", true},
            {"uiTree", tree}
        };
        
    } catch (const std::exception& e) {
        return {
            {"success", false},
            {"error", e.what()}
        };
    }
}

json ActionExecutor::ExecuteAction(const json& action) {
    if (!initialized_) {
        return {
            {"success", false},
            {"error", "Action executor not initialized"}
        };
    }
    
    // Extract action type
    if (!action.contains("action")) {
        return {
            {"success", false},
            {"error", "Missing 'action' field"}
        };
    }
    
    std::string actionType = action["action"];
    json params = action.contains("params") ? action["params"] : json::object();
    
    // Route to appropriate handler
    try {
        if (actionType == "click") {
            return ExecuteClick(params);
        } else if (actionType == "type") {
            return ExecuteType(params);
        } else if (actionType == "scroll") {
            return ExecuteScroll(params);
        } else if (actionType == "press_keys") {
            return ExecutePressKeys(params);
        } else if (actionType == "wait") {
            return ExecuteWait(params);
        } else {
            return {
                {"success", false},
                {"error", "Unknown action type: " + actionType}
            };
        }
    } catch (const std::exception& e) {
        return {
            {"success", false},
            {"error", std::string("Action execution error: ") + e.what()}
        };
    }
}

json ActionExecutor::ExecuteActions(const json& actions) {
    if (!actions.is_array()) {
        return {
            {"success", false},
            {"error", "Actions must be an array"}
        };
    }
    
    json results = json::array();
    
    for (const auto& action : actions) {
        json result = ExecuteAction(action);
        results.push_back(result);
        
        // Stop on first failure
        if (!result["success"]) {
            break;
        }
    }
    
    return {
        {"success", true},
        {"results", results}
    };
}

json ActionExecutor::ExecuteClick(const json& params) {
    if (!params.contains("x") || !params.contains("y")) {
        return {{"success", false}, {"error", "Missing x or y coordinates"}};
    }
    
    int x = params["x"];
    int y = params["y"];

    int screenW, screenH;
    screenCapture_->GetScreenDimensions(screenW, screenH);
    if (x < 0 || y < 0 || x >= screenW || y >= screenH) {
        return {{"success", false}, {"error", "Coordinates out of screen bounds"}};
    }

    MouseButton button = MouseButton::Left;
    if (params.contains("button")) {
        button = ParseMouseButton(params["button"]);
    }
    
    bool doubleClick = params.contains("double") && params["double"].get<bool>();
    
    if (doubleClick) {
        inputController_->DoubleClick(x, y, button);
    } else {
        inputController_->Click(x, y, button);
    }
    
    return {{"success", true}, {"action", "click"}};
}

json ActionExecutor::ExecuteType(const json& params) {
    if (!params.contains("text")) {
        return {{"success", false}, {"error", "Missing text parameter"}};
    }
    
    std::string text = params["text"];
    if (text.length() > 10000) {
        return {{"success", false}, {"error", "Text too long (max 10000 chars)"}};
    }
    std::wstring wtext = StringToWString(text);
    
    inputController_->TypeText(wtext);
    
    return {{"success", true}, {"action", "type"}};
}

json ActionExecutor::ExecuteScroll(const json& params) {
    if (!params.contains("delta")) {
        return {{"success", false}, {"error", "Missing delta parameter"}};
    }
    
    int delta = params["delta"];
    int x = params.contains("x") ? params["x"].get<int>() : -1;
    int y = params.contains("y") ? params["y"].get<int>() : -1;
    
    inputController_->Scroll(delta, x, y);
    
    return {{"success", true}, {"action", "scroll"}};
}

json ActionExecutor::ExecutePressKeys(const json& params) {
    if (!params.contains("keys")) {
        return {{"success", false}, {"error", "Missing keys parameter"}};
    }
    
    std::vector<WORD> keys;
    for (const auto& keyStr : params["keys"]) {
        keys.push_back(ParseVirtualKey(keyStr));
    }
    
    inputController_->PressKeys(keys);
    
    return {{"success", true}, {"action", "press_keys"}};
}

json ActionExecutor::ExecuteWait(const json& params) {
    if (!params.contains("ms")) {
        return {{"success", false}, {"error", "Missing ms parameter"}};
    }
    
    int ms = params["ms"];
    if (ms < 0 || ms > 30000) {
        return {{"success", false}, {"error", "Wait duration must be 0-30000ms"}};
    }
    inputController_->Wait(ms);
    
    return {{"success", true}, {"action", "wait"}};
}

MouseButton ActionExecutor::ParseMouseButton(const std::string& buttonStr) {
    if (buttonStr == "right") return MouseButton::Right;
    if (buttonStr == "middle") return MouseButton::Middle;
    return MouseButton::Left;
}

WORD ActionExecutor::ParseVirtualKey(const std::string& keyStr) {
    // Map common key names to virtual key codes
    if (keyStr == "ctrl") return VK_CONTROL;
    if (keyStr == "shift") return VK_SHIFT;
    if (keyStr == "alt") return VK_MENU;
    if (keyStr == "enter") return VK_RETURN;
    if (keyStr == "tab") return VK_TAB;
    if (keyStr == "escape") return VK_ESCAPE;
    if (keyStr == "space") return VK_SPACE;
    if (keyStr == "delete") return VK_DELETE;
    if (keyStr == "backspace") return VK_BACK;
    
    // Windows keys
    if (keyStr == "LWin" || keyStr == "lwin") return VK_LWIN;
    if (keyStr == "RWin" || keyStr == "rwin") return VK_RWIN;
    if (keyStr == "win") return VK_LWIN;  // Default to left Win key
    
    // Function keys
    if (keyStr == "F1") return VK_F1;
    if (keyStr == "F2") return VK_F2;
    if (keyStr == "F3") return VK_F3;
    if (keyStr == "F4") return VK_F4;
    if (keyStr == "F5") return VK_F5;
    if (keyStr == "F6") return VK_F6;
    if (keyStr == "F7") return VK_F7;
    if (keyStr == "F8") return VK_F8;
    if (keyStr == "F9") return VK_F9;
    if (keyStr == "F10") return VK_F10;
    if (keyStr == "F11") return VK_F11;
    if (keyStr == "F12") return VK_F12;
    
    // Arrow keys
    if (keyStr == "left") return VK_LEFT;
    if (keyStr == "right") return VK_RIGHT;
    if (keyStr == "up") return VK_UP;
    if (keyStr == "down") return VK_DOWN;
    
    // Single character
    if (keyStr.length() == 1) {
        return VkKeyScan(keyStr[0]) & 0xFF;
    }
    
    return 0;
}

json ActionExecutor::CheckLocalLLM() {
    // Check if Ollama is running by hitting its /api/tags endpoint
    HINTERNET hSession = WinHttpOpen(
        L"BrowserAI/1.0",
        WINHTTP_ACCESS_TYPE_NO_PROXY,
        WINHTTP_NO_PROXY_NAME,
        WINHTTP_NO_PROXY_BYPASS,
        0);

    if (!hSession) {
        return {{"success", true}, {"available", false},
                {"error", "Failed to create HTTP session"}};
    }

    HINTERNET hConnect = WinHttpConnect(
        hSession, L"localhost",
        11434,  // Ollama default port
        0);

    if (!hConnect) {
        WinHttpCloseHandle(hSession);
        return {{"success", true}, {"available", false},
                {"error", "Cannot connect to Ollama (port 11434)"}};
    }

    HINTERNET hRequest = WinHttpOpenRequest(
        hConnect, L"GET", L"/api/tags",
        nullptr, WINHTTP_NO_REFERER,
        WINHTTP_DEFAULT_ACCEPT_TYPES, 0);

    if (!hRequest) {
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        return {{"success", true}, {"available", false},
                {"error", "Failed to create HTTP request"}};
    }

    // Set a short timeout (3 seconds)
    DWORD timeout = 3000;
    WinHttpSetOption(hRequest, WINHTTP_OPTION_CONNECT_TIMEOUT, &timeout, sizeof(timeout));
    WinHttpSetOption(hRequest, WINHTTP_OPTION_RECEIVE_TIMEOUT, &timeout, sizeof(timeout));

    BOOL sent = WinHttpSendRequest(hRequest, WINHTTP_NO_ADDITIONAL_HEADERS, 0,
                                    WINHTTP_NO_REQUEST_DATA, 0, 0, 0);

    if (!sent || !WinHttpReceiveResponse(hRequest, nullptr)) {
        WinHttpCloseHandle(hRequest);
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        return {{"success", true}, {"available", false},
                {"error", "Ollama is not running on localhost:11434"}};
    }

    // Read response body
    std::string responseBody;
    DWORD bytesAvailable = 0;
    while (WinHttpQueryDataAvailable(hRequest, &bytesAvailable) && bytesAvailable > 0) {
        std::vector<char> buf(bytesAvailable);
        DWORD bytesRead = 0;
        WinHttpReadData(hRequest, buf.data(), bytesAvailable, &bytesRead);
        responseBody.append(buf.data(), bytesRead);
    }

    WinHttpCloseHandle(hRequest);
    WinHttpCloseHandle(hConnect);
    WinHttpCloseHandle(hSession);

    // Parse Ollama response to list available models
    json result = {{"success", true}, {"available", true}};
    try {
        json ollamaResp = json::parse(responseBody);
        if (ollamaResp.contains("models") && ollamaResp["models"].is_array()) {
            json models = json::array();
            for (const auto& model : ollamaResp["models"]) {
                std::string name = model.value("name", "unknown");
                models.push_back(name);
            }
            result["models"] = models;
            result["model_count"] = models.size();

            // Check for vision-capable models
            bool hasVision = false;
            for (const auto& model : ollamaResp["models"]) {
                std::string name = model.value("name", "");
                if (name.find("llava") != std::string::npos ||
                    name.find("cogagent") != std::string::npos ||
                    name.find("bakllava") != std::string::npos ||
                    name.find("moondream") != std::string::npos) {
                    hasVision = true;
                    break;
                }
            }
            result["has_vision_model"] = hasVision;
        }
    } catch (...) {
        // Ollama responded but we can't parse — still available
        result["models"] = json::array();
        result["model_count"] = 0;
        result["has_vision_model"] = false;
    }

    return result;
}

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

json ActionExecutor::GetProviderStatus(const json& /*params*/) {
    return aiProvider_->GetProviderStatus();
}
