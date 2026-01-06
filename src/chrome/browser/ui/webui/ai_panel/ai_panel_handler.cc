#include "chrome/browser/ui/webui/ai_panel/ai_panel_handler.h"
#include "base/values.h"

void AiPanelHandler::RegisterMessages() {
    web_ui()->RegisterMessageCallback(
        "ping",
        base:BindRepeating(&AiPanelHandler::HandlePing, base::Unretained(this)));
    }

void AiPanelHandler::HandlePing(const base::Value::List& args) {
    AllowJavascript();
    FireWebUIListener("pong", base::Value("pong from C++"));
}
