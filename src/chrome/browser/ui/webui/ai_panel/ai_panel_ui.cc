#include "chrome/browser/ui/webui/ai_panel/ai_panel_ui.h"
#include "chrome/browser/ui/webui/ai_panel/ai_panel_handler.h"
#include "content/public/browser/web_ui.h"
#include "content/public/browser/web_ui_data_source.h"
#include "services/network/public/mojom/content_security_policy.mojom.h"

AIPanelUI::AIPanelUI(content::WebUI* web_ui) : WebUIController(web_ui) {
    auto* source = content::WebUIDataSource::CreateAndAdd(
        web_ui->GetWebContents()->GetBrowserContext(),
        "ai-panel-side-panel.top-chrome");

    // Allow JS to fetch from the local backend and Ollama servers
    source->OverrideContentSecurityPolicy(
        network::mojom::CSPDirectiveName::ConnectSrc,
        "connect-src http://localhost:5000 http://localhost:11434 'self';");

    source->AddResourcePath("ai_panel.js", IDR_AI_PANEL_JS);
    source->AddResourcePath("ai_panel.css", IDR_AI_PANEL_CSS);
    source->AddResourcePath("ai_provider_interface.js", IDR_AI_PANEL_PROVIDER_INTERFACE_JS);
    source->AddResourcePath("openai_provider.js", IDR_AI_PANEL_OPENAI_PROVIDER_JS);
    source->AddResourcePath("ollama_provider.js", IDR_AI_PANEL_OLLAMA_PROVIDER_JS);
    source->AddResourcePath("anthropic_provider.js", IDR_AI_PANEL_ANTHROPIC_PROVIDER_JS);
    source->AddResourcePath("local_llm_provider.js", IDR_AI_PANEL_LOCAL_LLM_PROVIDER_JS);
    source->AddResourcePath("ai_provider_manager.js", IDR_AI_PANEL_PROVIDER_MANAGER_JS);
    source->AddResourcePath("native_messaging_helper.js", IDR_AI_PANEL_NATIVE_MESSAGING_JS);
    source->SetDefaultResource(IDR_AI_PANEL_HTML);

    web_ui->AddMessageHandler(std::make_unique<AiPanelHandler>());
}
