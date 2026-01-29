#ifndef CHROME_BROWSER_UI_VIEWS_SIDE_PANEL_AI_PANEL_AI_PANEL_SIDE_PANEL_COORDINATOR_H_
#define CHROME_BROWSER_UI_VIEWS_SIDE_PANEL_AI_PANEL_AI_PANEL_SIDE_PANEL_COORDINATOR_H_

#include <memory>
#include "base/memory/raw_ptr.h"
#include "chrome/browser/ui/views/side_panel/side_panel_entry.h"

class Browser;
class SidePanelRegistry;

namespace views {
class View;
}

class AiPanelSidePanelCoordinator {
 public:
  explicit AiPanelSidePanelCoordinator(Browser* browser);
  ~AiPanelSidePanelCoordinator();

  AiPanelSidePanelCoordinator(const AiPanelSidePanelCoordinator&) = delete;
  AiPanelSidePanelCoordinator& operator=(const AiPanelSidePanelCoordinator&) = delete;

  void CreateAndRegisterEntry(SidePanelRegistry* global_registry);

 private:
  std::unique_ptr<views::View> CreateAiPanelWebView();

  raw_ptr<Browser> browser_;
};

#endif  // CHROME_BROWSER_UI_VIEWS_SIDE_PANEL_AI_PANEL_AI_PANEL_SIDE_PANEL_COORDINATOR_H_
