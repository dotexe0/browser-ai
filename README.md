# browser-ai

A Chromium-based browser with integrated AI panel functionality.

## Overview

This project adds a custom AI panel interface to Chromium. The AI panel provides an integrated AI assistant experience directly within the browser UI.

## Project Structure

```
src/                            # Mirrored chromium/src structure
└── chrome/
    └── browser/
        └── ui/
            ├── webui/
            │   └── ai_panel/           # AI Panel WebUI
            │       ├── ai_panel_ui.h
            │       ├── ai_panel_ui.cc
            │       ├── ai_panel_handler.h
            │       ├── ai_panel_handler.cc
            │       └── resources/
            │           ├── ai_panel.html
            │           ├── ai_panel.css
            │           └── ai_panel.js
            └── views/
                └── side_panel/         # Side panel integration
                    └── (your changes here)

sync-to-chromium.sh             # Script to copy files to chromium/src
sync-from-chromium.sh           # Script to copy changes back from chromium/src
```

## Features

- **AI Panel UI**: Custom WebUI controller for the AI panel
- **AI Panel Handler**: Backend handler for AI panel interactions
- **Side Panel Integration**: Integration with Chrome's side panel system
- **Modern UI**: HTML/CSS/JS resources for the AI panel interface

## Installation

### Prerequisites

- Follow the standard [Chromium build prerequisites](https://chromium.googlesource.com/chromium/src/+/main/docs/windows_build_instructions.md) for your platform
- depot_tools installed and configured
- Git
- Bash (Git Bash on Windows)

### Setup

1. **Clone this repository:**
   ```bash
   git clone https://github.com/dotexe0/browser-ai.git
   cd browser-ai
   ```

2. **Get the Chromium source:**
   ```bash
   # Fetch depot_tools if you don't have it
   git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
   export PATH="$PATH:${PWD}/depot_tools"  # Linux/Mac
   # set PATH=%PATH%;%CD%\depot_tools       # Windows cmd
   
   # Create chromium directory and fetch source
   mkdir chromium
   cd chromium
   fetch --nohooks chromium
   cd src
   ```

3. **Sync custom files to Chromium:**
   ```bash
   # From the browser-ai directory
   cd ../..  # back to browser-ai root
   
   # Make the sync script executable
   chmod +x sync-to-chromium.sh
   
   # Sync files to chromium
   ./sync-to-chromium.sh
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

## Development Workflow

### Making Changes

**Option 1: Work directly in chromium/src (Recommended for development)**

1. Make your changes in `chromium/src/chrome/browser/ui/...`
2. Build and test your changes
3. When ready to commit, sync changes back to the repo:
   ```bash
   ./sync-from-chromium.sh
   ```
4. Review and commit:
   ```bash
   git status
   git add src/
   git commit -m "Your commit message"
   git push origin main
   ```

**Option 2: Work in src/ directory and sync**

1. Make changes in the `src/` directory
2. Sync to chromium:
   ```bash
   ./sync-to-chromium.sh
   ```
3. Build and test in chromium/src
4. Commit changes from src/ directory:
   ```bash
   git add src/
   git commit -m "Your commit message"
   git push origin main
   ```

### Adding New Files

When you add new files to `chromium/src/chrome/browser/ui/`:

1. Create the same file in your repo's `src/chrome/browser/ui/` directory
2. Or work in chromium and sync back with `./sync-from-chromium.sh`
3. Update the sync scripts if you add new directories

### Testing

```bash
# Run Chromium tests
cd chromium/src
out/Default/unit_tests --gtest_filter="AIPanelUI*"
```

## Why This Structure?

The `src/` directory mirrors the chromium source tree structure, allowing:

✅ **Easy syncing** between your repo and chromium source  
✅ **Track only your custom changes**, not the entire chromium codebase  
✅ **Clear organization** of what files you've modified  
✅ **Version control** for your changes without conflicts  
✅ **Easy collaboration** - others can apply your changes to their chromium checkout

The sync scripts automate file copying between your tracked `src/` directory and the ignored `chromium/src/` directory.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes in the `src/` directory
4. Test thoroughly with a Chromium build
5. Submit a pull request

## Roadmap

- [x] AI Panel WebUI structure
- [x] AI Panel handler implementation
- [ ] Side panel integration
- [ ] AI backend service integration
- [ ] Keyboard shortcuts for panel access
- [ ] Panel theming
- [ ] Unit tests
- [ ] Integration tests

## License

This project is based on Chromium, which is licensed under the BSD license. The AI panel code follows the same license.

## Acknowledgments

- Built on top of the [Chromium project](https://www.chromium.org/)
- Uses Chromium's WebUI framework for the AI panel interface

## Resources

- [Chromium WebUI Documentation](https://chromium.googlesource.com/chromium/src/+/main/docs/webui_explainer.md)
- [Chromium Build Instructions](https://chromium.googlesource.com/chromium/src/+/main/docs/README.md)
- [Depot Tools Tutorial](https://commondatastorage.googleapis.com/chrome-infra-docs/flat/depot_tools/docs/html/depot_tools_tutorial.html)
