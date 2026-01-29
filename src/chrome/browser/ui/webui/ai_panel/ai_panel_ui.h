#ifndef CHROME_BROWSER_UI_WEBUI_AI_PANEL_AI_PANEL_UI_H_
#define CHROME_BROWSER_UI_WEBUI_AI_PANEL_AI_PANEL_UI_H_

#include "content/public/browser/web_ui_controller.h"
#include "content/public/browser/webui_config.h"
#include "content/public/common/url_constants.h"

class AIPanelUI : public content::WebUIController {
 public:
  explicit AIPanelUI(content::WebUI* web_ui);
  ~AIPanelUI() override = default;
};

class AIPanelUIConfig : public content::DefaultWebUIConfig<AIPanelUI> {
 public:
  AIPanelUIConfig()
      : DefaultWebUIConfig(content::kChromeUIScheme,
                           "ai-panel-side-panel.top-chrome") {}
};

#endif  // CHROME_BROWSER_UI_WEBUI_AI_PANEL_AI_PANEL_UI_H_
