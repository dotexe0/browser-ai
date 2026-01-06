#pragma once

#include "content/public/browser/web_ui_message_handler.h"

class AiPanelHandler : public content::WebUIMessageHandler {
    public:
    AiPanelHandler() = default;
    ~AiPanelHandler() override = default;

    void RegisterMessages() override;
    void HandlePing(const base::Value::List& args);
}
