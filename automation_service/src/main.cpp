#include "native_messaging.h"
#include "action_executor.h"
#include <iostream>
#include <memory>

/**
 * Browser AI Automation Service
 * 
 * Native Messaging host for desktop automation.
 * Communicates with browser via stdin/stdout JSON protocol.
 */

int main(int argc, char* argv[]) {
    // stdout is used for Native Messaging, stderr for logging
    LOG_INFO(L"Browser AI Automation Service starting...");
    
    // Initialize action executor
    auto executor = std::make_unique<ActionExecutor>();
    
    if (!executor->Initialize()) {
        LOG_ERROR(L"Failed to initialize action executor");
        return 1;
    }
    
    LOG_INFO(L"Action executor initialized");
    
    // Create Native Messaging handler
    NativeMessaging messaging;
    
    // Register handlers
    messaging.RegisterHandler("get_capabilities", [&](const json& msg) -> json {
        return executor->GetCapabilities();
    });
    
    messaging.RegisterHandler("capture_screen", [&](const json& msg) -> json {
        return executor->CaptureScreen();
    });
    
    messaging.RegisterHandler("inspect_ui", [&](const json& msg) -> json {
        return executor->GetUITree();
    });
    
    messaging.RegisterHandler("execute_action", [&](const json& msg) -> json {
        if (!msg.contains("params")) {
            return {{"success", false}, {"error", "Missing params"}};
        }
        return executor->ExecuteAction(msg["params"]);
    });
    
    messaging.RegisterHandler("execute_actions", [&](const json& msg) -> json {
        if (!msg.contains("params") || !msg["params"].contains("actions")) {
            return {{"success", false}, {"error", "Missing actions array"}};
        }
        return executor->ExecuteActions(msg["params"]["actions"]);
    });
    
    messaging.RegisterHandler("check_local_llm", [&](const json& msg) -> json {
        return executor->CheckLocalLLM();
    });
    
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

    messaging.RegisterHandler("ping", [&](const json& msg) -> json {
        return {
            {"success", true},
            {"message", "pong"},
            {"version", "1.0.0"}
        };
    });
    
    LOG_INFO(L"Handlers registered, entering message loop");
    
    // Run message loop
    messaging.Run();
    
    LOG_INFO(L"Automation service shutting down");
    return 0;
}

