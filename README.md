# browser-ai

A Chromium-based browser with integrated AI panel functionality.

## Overview

This project adds a custom AI panel interface to Chromium. The AI panel provides an integrated AI assistant experience directly within the browser UI.

## Project Structure

```
ai_panel/                       # AI Panel source code
├── ai_panel_ui.h               # WebUI controller header
├── ai_panel_ui.cc              # WebUI controller implementation
├── ai_panel_handler.h          # Backend handler header
├── ai_panel_handler.cc         # Backend handler implementation
└── resources/                  # Frontend resources
    ├── ai_panel.html           # Panel HTML structure
    ├── ai_panel.css            # Panel styles
    └── ai_panel.js             # Panel JavaScript
```

## Features

- **AI Panel UI**: Custom WebUI controller for the AI panel
- **AI Panel Handler**: Backend handler for AI panel interactions
- **Modern UI**: HTML/CSS/JS resources for the AI panel interface

## Installation

### Prerequisites

- Follow the standard [Chromium build prerequisites](https://chromium.googlesource.com/chromium/src/+/main/docs/windows_build_instructions.md) for your platform
- depot_tools installed and configured
- Git

### Setup

1. **Clone this repository:**
   ```bash
   git clone https://github.com/dotexe0/browser-ai.git
   cd browser-ai
   ```

2. **Get the Chromium source:**
   ```bash
   # Fetch depot_tools
   git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
   export PATH="$PATH:${PWD}/depot_tools"  # Linux/Mac
   # set PATH=%PATH%;%CD%\depot_tools       # Windows cmd
   
   # Create chromium directory and fetch source
   mkdir chromium
   cd chromium
   fetch --nohooks chromium
   cd src
   ```

3. **Install the AI panel into Chromium:**
   ```bash
   # From the browser-ai directory
   cd ../..  # back to browser-ai root
   
   # Copy AI panel files to Chromium source
   cp -r ai_panel/* chromium/src/chrome/browser/ui/webui/ai_panel/
   ```

4. **Sync dependencies:**
   ```bash
   cd chromium/src
   gclient sync
   gclient runhooks
   ```

5. **Configure the build:**
   
   You'll need to integrate the AI panel into the Chromium build system:
   
   a. Add to `chrome/browser/ui/webui/BUILD.gn`:
   ```gn
   # Add to sources list
   "webui/ai_panel/ai_panel_handler.cc",
   "webui/ai_panel/ai_panel_handler.h",
   "webui/ai_panel/ai_panel_ui.cc",
   "webui/ai_panel/ai_panel_ui.h",
   ```
   
   b. Register the WebUI in `chrome/browser/ui/webui/chrome_web_ui_controller_factory.cc`:
   ```cpp
   #include "chrome/browser/ui/webui/ai_panel/ai_panel_ui.h"
   
   // In GetWebUIType or similar function:
   if (url.host() == "ai-panel")
     return &NewWebUI<AIPanelUI>;
   ```

6. **Generate build files:**
   ```bash
   gn gen out/Default
   # Or for a release build:
   gn gen out/Default --args='is_debug=false'
   ```

7. **Build Chromium:**
   ```bash
   autoninja -C out/Default chrome
   ```

### Running

After building, you can run the browser:
```bash
# Windows
out/Default/chrome.exe

# Linux
out/Default/chrome

# Mac
out/Default/Chromium.app/Contents/MacOS/Chromium
```

To access the AI panel, navigate to:
```
chrome://ai-panel
```

## Development

### Architecture

The AI panel is implemented as a WebUI component using Chromium's WebUI framework:

- **AIPanelUI**: Main UI controller that sets up the WebUI and registers message handlers
- **AIPanelHandler**: Handles communication between the WebUI (frontend) and the browser backend
- **Resources**: HTML, CSS, and JavaScript for the panel's user interface

### Making Changes

1. Modify files in the `ai_panel/` directory
2. Copy updated files to your Chromium checkout:
   ```bash
   cp -r ai_panel/* chromium/src/chrome/browser/ui/webui/ai_panel/
   ```
3. Rebuild:
   ```bash
   cd chromium/src
   autoninja -C out/Default chrome
   ```

### Testing

```bash
# Run Chromium tests
cd chromium/src
out/Default/unit_tests --gtest_filter="AIPanelUI*"
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes to the files in the `ai_panel/` directory
4. Test thoroughly with a Chromium build
5. Submit a pull request

## Roadmap

- [ ] Complete AI panel handler implementation
- [ ] Add WebUI resources (HTML/CSS/JS)
- [ ] Integrate AI backend service
- [ ] Add keyboard shortcuts for panel access
- [ ] Implement panel theming
- [ ] Add unit tests
- [ ] Add integration tests

## License

This project is based on Chromium, which is licensed under the BSD license. The AI panel code follows the same license.

## Acknowledgments

- Built on top of the [Chromium project](https://www.chromium.org/)
- Uses Chromium's WebUI framework for the AI panel interface

## Resources

- [Chromium WebUI Documentation](https://chromium.googlesource.com/chromium/src/+/main/docs/webui_explainer.md)
- [Chromium Build Instructions](https://chromium.googlesource.com/chromium/src/+/main/docs/README.md)
- [Depot Tools Tutorial](https://commondatastorage.googleapis.com/chrome-infra-docs/flat/depot_tools/docs/html/depot_tools_tutorial.html)
