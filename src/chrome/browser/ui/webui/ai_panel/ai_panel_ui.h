#pragma once

#include "content/public/browser/web_ui_controller.h"

class AIPanelUI : public content::WebUIController {
    public:
        explicit AIPanelUI(content::WebUI* web_ui);
        ~AIPanelUI() override = default;
};

