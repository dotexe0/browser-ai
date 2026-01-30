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
