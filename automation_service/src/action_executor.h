#pragma once

#include "common.h"
#include "ui_automation.h"
#include "screen_capture.h"
#include "input_controller.h"
#include <nlohmann/json.hpp>
#include <memory>

using json = nlohmann::json;

/**
 * Action Executor
 * 
 * Executes automation actions by coordinating
 * UI automation, screen capture, and input control.
 */
class ActionExecutor {
public:
    ActionExecutor();
    ~ActionExecutor();
    
    // Initialize all subsystems
    bool Initialize();
    
    // Execute a single action
    json ExecuteAction(const json& action);
    
    // Execute multiple actions sequentially
    json ExecuteActions(const json& actions);
    
    // Get capabilities
    json GetCapabilities();
    
    // Capture screen and return base64 PNG
    json CaptureScreen();
    
    // Get UI tree
    json GetUITree();
    
    // Check if local LLM is available (future)
    json CheckLocalLLM();
    
private:
    std::unique_ptr<UIAutomation> uiAutomation_;
    std::unique_ptr<ScreenCapture> screenCapture_;
    std::unique_ptr<InputController> inputController_;
    
    bool initialized_;
    
    // Parse and execute specific action types
    json ExecuteClick(const json& params);
    json ExecuteType(const json& params);
    json ExecuteScroll(const json& params);
    json ExecutePressKeys(const json& params);
    json ExecuteWait(const json& params);
    
    // Parse mouse button from string
    MouseButton ParseMouseButton(const std::string& buttonStr);
    
    // Parse virtual key from string
    WORD ParseVirtualKey(const std::string& keyStr);
};

