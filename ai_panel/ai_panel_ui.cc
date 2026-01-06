#include "chrome/browser/ui/webui/ai_panel/ai_panel_ui.h"
#include "chrome/browser/ui/webui/ai_panel/ai_panel_handler.h"
#include "content/public/browser/web_ui.h"
#include "content/public/browser/web_ui_data_source.h"

AiPanelUI::AiPanelUI(content::WebUI* web_ui) : WebUIController(web_ui) {
    auto* source = content::WebUIDataSource::Create("ai-panel");

    source->AddResourcePath("ai_panel.js", IDR_AI_PANEL_JS);
    source->AddResourcePath("ai_panel.css", IDR_AI_PANEL_CSS);
    source->SetDefaultResource(IDR_AI_PANEL_HTML);

    content::WebUIDataSource::Add(web_ui->GetWebContents()->GetBrowserContext(), source);
    web_ui->AddMessageHandler(std::make_unique<AiPanelHandler>());
}
