#include "action_executor.h"

ActionExecutor::ActionExecutor() : initialized_(false) {
    uiAutomation_ = std::make_unique<UIAutomation>();
    screenCapture_ = std::make_unique<ScreenCapture>();
    inputController_ = std::make_unique<InputController>();
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
    return {
        {"success", true},
        {"capabilities", {
            {"screen_capture", initialized_},
            {"ui_automation", initialized_},
            {"input_control", true},
            {"local_llm", false}  // Not yet implemented
        }}
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
    // Stub for future implementation
    return {
        {"success", true},
        {"available", false},
        {"error", "Local LLM not yet implemented"}
    };
}

