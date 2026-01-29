#include "chrome/browser/ui/views/side_panel/ai_panel/ai_panel_side_panel_coordinator.h"

#include "chrome/browser/ui/browser.h"
#include "chrome/browser/ui/views/side_panel/side_panel_entry.h"
#include "chrome/browser/ui/views/side_panel/side_panel_registry.h"
#include "chrome/browser/ui/views/side_panel/side_panel_web_ui_view.h"
#include "chrome/browser/ui/webui/ai_panel/ai_panel_ui.h"
#include "chrome/common/webui_url_constants.h"

AiPanelSidePanelCoordinator::AiPanelSidePanelCoordinator(Browser* browser)
    : browser_(browser) {}

AiPanelSidePanelCoordinator::~AiPanelSidePanelCoordinator() = default;

void AiPanelSidePanelCoordinator::CreateAndRegisterEntry(
    SidePanelRegistry* global_registry) {
  global_registry->Register(std::make_unique<SidePanelEntry>(
      SidePanelEntry::Key(SidePanelEntry::Id::kAIPanel),
      base::BindRepeating(
          &AiPanelSidePanelCoordinator::CreateAiPanelWebView,
          base::Unretained(this))));
}

std::unique_ptr<views::View>
AiPanelSidePanelCoordinator::CreateAiPanelWebView() {
  auto wrapper =
      std::make_unique<BubbleContentsWrapperT<AIPanelUI>>(
          GURL("chrome://ai-panel-side-panel.top-chrome/"),
          browser_->profile(),
          /*task_manager_string_id=*/0,
          /*webui_resizes_host=*/true,
          /*esc_closes_ui=*/false);
  wrapper->ReloadWebContents();

  auto view = std::make_unique<SidePanelWebUIViewT<AIPanelUI>>(
      browser_, base::NullCallback(), std::move(wrapper));
  return view;
}
