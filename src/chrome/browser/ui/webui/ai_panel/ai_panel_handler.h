#ifndef CHROME_BROWSER_UI_WEBUI_AI_PANEL_AI_PANEL_HANDLER_H_
#define CHROME_BROWSER_UI_WEBUI_AI_PANEL_AI_PANEL_HANDLER_H_

#include <string>
#include "content/public/browser/web_ui_message_handler.h"

class AiPanelHandler : public content::WebUIMessageHandler {
 public:
  AiPanelHandler() = default;
  ~AiPanelHandler() override = default;

  void RegisterMessages() override;

 private:
  void HandlePing(const base::Value::List& args);
  void HandleCallBackend(const base::Value::List& args);
  void HandleExecuteActions(const base::Value::List& args);

  // HTTP helper: POST JSON to localhost:5000 at the given path, return response
  std::string HttpPost(const std::string& path, const std::string& json_body);
};

#endif  // CHROME_BROWSER_UI_WEBUI_AI_PANEL_AI_PANEL_HANDLER_H_
