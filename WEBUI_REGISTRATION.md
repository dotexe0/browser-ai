# 🔧 Registering chrome://ai-panel WebUI

## Problem
`chrome://ai-panel` gives `ERR_INVALID_URL` because the WebUI isn't registered.

## Solution
Modern Chromium requires:
1. WebUIConfig class
2. URL constant definition
3. Resource registration
4. Config registration in factory

## Steps to Fix

### 1. Define URL Constant

**File**: `chrome/common/webui_url_constants.h`
```cpp
// Add this with other constants
inline constexpr char kChromeUIAIPanelHost[] = "ai-panel";
```

**File**: `chrome/common/webui_url_constants.cc`
```cpp
// Add this with other URLs
const char kChromeUIAIPanelURL[] = "chrome://ai-panel/";
```

### 2. Update ai_panel_ui.h

```cpp
#pragma once

#include "content/public/browser/web_ui_controller.h"
#include "content/public/browser/webui_config.h"
#include "content/public/common/url_constants.h"

class AIPanelUI : public content::WebUIController {
public:
    explicit AIPanelUI(content::WebUI* web_ui);
    ~AIPanelUI() override = default;
};

// WebUIConfig for registering chrome://ai-panel
class AIPanelUIConfig : public content::DefaultWebUIConfig<AIPanelUI> {
public:
    AIPanelUIConfig()
        : DefaultWebUIConfig(content::kChromeUIScheme, 
                           "ai-panel") {}  // host name
};
```

### 3. Register Resources

**File**: `chrome/browser/browser_resources.grd`

Add inside `<includes>` section:
```xml
<include name="IDR_AI_PANEL_HTML" file="resources\ai_panel\resources\ai_panel.html" type="BINDATA" />
```

Add inside `<structures>` section:
```xml
<structure name="IDR_AI_PANEL_JS" file="resources\ai_panel\resources\ai_panel.js" type="chrome_html" />
<structure name="IDR_AI_PANEL_CSS" file="resources\ai_panel\resources\ai_panel.css" type="chrome_html" />
<structure name="IDR_AI_PANEL_PROVIDER_INTERFACE_JS" file="resources\ai_panel\resources\ai_provider_interface.js" type="chrome_html" />
<structure name="IDR_AI_PANEL_OPENAI_PROVIDER_JS" file="resources\ai_panel\resources\openai_provider.js" type="chrome_html" />
<structure name="IDR_AI_PANEL_LOCAL_LLM_PROVIDER_JS" file="resources\ai_panel\resources\local_llm_provider.js" type="chrome_html" />
<structure name="IDR_AI_PANEL_OLLAMA_PROVIDER_JS" file="resources\ai_panel\resources\ollama_provider.js" type="chrome_html" />
<structure name="IDR_AI_PANEL_PROVIDER_MANAGER_JS" file="resources\ai_panel\resources\ai_provider_manager.js" type="chrome_html" />
```

### 4. Update ai_panel_ui.cc

```cpp
#include "chrome/browser/ui/webui/ai_panel/ai_panel_ui.h"
#include "chrome/browser/ui/webui/ai_panel/ai_panel_handler.h"
#include "chrome/common/webui_url_constants.h"
#include "chrome/grit/browser_resources.h"
#include "content/public/browser/web_ui.h"
#include "content/public/browser/web_ui_data_source.h"

AIPanelUI::AIPanelUI(content::WebUI* web_ui) : WebUIController(web_ui) {
    content::WebUIDataSource* source =
        content::WebUIDataSource::CreateAndAdd(
            web_ui->GetWebContents()->GetBrowserContext(),
            chrome::kChromeUIAIPanelHost);

    // Add resources
    source->AddResourcePath("ai_panel.js", IDR_AI_PANEL_JS);
    source->AddResourcePath("ai_panel.css", IDR_AI_PANEL_CSS);
    source->AddResourcePath("ai_provider_interface.js", IDR_AI_PANEL_PROVIDER_INTERFACE_JS);
    source->AddResourcePath("openai_provider.js", IDR_AI_PANEL_OPENAI_PROVIDER_JS);
    source->AddResourcePath("local_llm_provider.js", IDR_AI_PANEL_LOCAL_LLM_PROVIDER_JS);
    source->AddResourcePath("ollama_provider.js", IDR_AI_PANEL_OLLAMA_PROVIDER_JS);
    source->AddResourcePath("ai_provider_manager.js", IDR_AI_PANEL_PROVIDER_MANAGER_JS);
    source->SetDefaultResource(IDR_AI_PANEL_HTML);

    web_ui->AddMessageHandler(std::make_unique<AIPanelHandler>());
}
```

### 5. Register WebUI Config

The config should auto-register if it's defined. The `DefaultWebUIConfig` base class handles registration.

Alternatively, ensure it's added to the WebUI registry in `chrome/browser/ui/webui/chrome_web_ui_controller_factory.cc` if needed.

## Quick Fix for Testing

**Simpler approach** - Just update the existing files to use proper constants and ensure resources are in grd file.

The key files that MUST be updated:
1. `ai_panel_ui.h` - Add WebUIConfig class
2. `ai_panel_ui.cc` - Use chrome::kChromeUIAIPanelHost
3. `browser_resources.grd` - Register all resources
4. `webui_url_constants.h` - Define host constant

## Rebuild Command

After making changes:
```bash
cd A:\browser-ai\chromium\src
autoninja -C out\Default chrome
```

This will be fast since it's just recompiling changed files.

