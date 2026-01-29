# Chromium Integration Guide

After syncing files with `./sync-to-chromium.sh`, apply these changes directly in `chromium/src/`.

## 1. Add Side Panel Entry ID

**File:** `chrome/browser/ui/views/side_panel/side_panel_entry_id.h`

Add to the `SIDE_PANEL_ENTRY_IDS` macro:

```cpp
V(kAIPanel, kActionSidePanelShowAIPanel, "AIPanel") \
```

## 2. Add Action ID

**File:** `chrome/browser/ui/actions/chrome_action_id.h`

Add to the action ID enum:

```cpp
kActionSidePanelShowAIPanel,
```

## 3. Register WebUI Config

**File:** `chrome/browser/ui/webui/chrome_web_ui_configs.cc`

Add include:
```cpp
#include "chrome/browser/ui/webui/ai_panel/ai_panel_ui.h"
```

Add in the registration function:
```cpp
map.AddWebUIConfig(std::make_unique<AIPanelUIConfig>());
```

## 4. Create Coordinator in BrowserWindowFeatures

**File:** `chrome/browser/ui/browser_window/internal/browser_window_features.cc`

Add include:
```cpp
#include "chrome/browser/ui/views/side_panel/ai_panel/ai_panel_side_panel_coordinator.h"
```

Add member in header (`browser_window_features.h`):
```cpp
std::unique_ptr<AiPanelSidePanelCoordinator> ai_panel_side_panel_coordinator_;
```

Add accessor:
```cpp
AiPanelSidePanelCoordinator* ai_panel_side_panel_coordinator() {
  return ai_panel_side_panel_coordinator_.get();
}
```

Add creation in the Init or construction:
```cpp
ai_panel_side_panel_coordinator_ =
    std::make_unique<AiPanelSidePanelCoordinator>(browser);
```

## 5. Register in PopulateGlobalEntries

**File:** `chrome/browser/ui/views/side_panel/side_panel_util.cc`

Add include:
```cpp
#include "chrome/browser/ui/views/side_panel/ai_panel/ai_panel_side_panel_coordinator.h"
```

Add in `PopulateGlobalEntries()`:
```cpp
browser->browser_window_features()
    ->ai_panel_side_panel_coordinator()
    ->CreateAndRegisterEntry(window_registry);
```

## 6. Add to BUILD.gn

**File:** `chrome/browser/ui/views/side_panel/BUILD.gn`

Add to deps:
```gn
"//chrome/browser/ui/webui/ai_panel:ai_panel_side_panel",
```

## 7. Register Resources in GRD

**File:** `chrome/browser/browser_resources.grd`

Add resource entries for all JS/CSS/HTML files:
```xml
<include name="IDR_AI_PANEL_HTML" file="resources/side_panel/ai_panel/ai_panel.html" type="BINDATA" />
<include name="IDR_AI_PANEL_JS" file="resources/side_panel/ai_panel/ai_panel.js" type="BINDATA" />
<include name="IDR_AI_PANEL_CSS" file="resources/side_panel/ai_panel/ai_panel.css" type="BINDATA" />
<include name="IDR_AI_PANEL_PROVIDER_INTERFACE_JS" file="resources/side_panel/ai_panel/ai_provider_interface.js" type="BINDATA" />
<include name="IDR_AI_PANEL_OPENAI_PROVIDER_JS" file="resources/side_panel/ai_panel/openai_provider.js" type="BINDATA" />
<include name="IDR_AI_PANEL_OLLAMA_PROVIDER_JS" file="resources/side_panel/ai_panel/ollama_provider.js" type="BINDATA" />
<include name="IDR_AI_PANEL_ANTHROPIC_PROVIDER_JS" file="resources/side_panel/ai_panel/anthropic_provider.js" type="BINDATA" />
<include name="IDR_AI_PANEL_LOCAL_LLM_PROVIDER_JS" file="resources/side_panel/ai_panel/local_llm_provider.js" type="BINDATA" />
<include name="IDR_AI_PANEL_PROVIDER_MANAGER_JS" file="resources/side_panel/ai_panel/ai_provider_manager.js" type="BINDATA" />
<include name="IDR_AI_PANEL_NATIVE_MESSAGING_JS" file="resources/side_panel/ai_panel/native_messaging_helper.js" type="BINDATA" />
```

## 8. Build

```bash
cd chromium/src
gn gen out/Default
autoninja -C out/Default chrome
```

## 9. Test

Launch Chrome and click the side panel icon in the toolbar. Select "AI Automation" from the dropdown.
