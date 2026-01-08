#!/bin/bash
# Sync changes from chromium source tree back to repo

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CHROMIUM_SRC="$SCRIPT_DIR/chromium/src"

if [ ! -d "$CHROMIUM_SRC" ]; then
    echo "Error: Chromium source not found at $CHROMIUM_SRC"
    exit 1
fi

echo "Syncing files from chromium source tree..."

# Sync specific directories back to repo
# Using cp -r since rsync may not be available on all systems
mkdir -p "$SCRIPT_DIR/src/chrome/browser/ui/webui/ai_panel/"
mkdir -p "$SCRIPT_DIR/src/chrome/browser/ui/views/side_panel/"

if [ -d "$CHROMIUM_SRC/chrome/browser/ui/webui/ai_panel/" ]; then
    cp -r "$CHROMIUM_SRC/chrome/browser/ui/webui/ai_panel/"* "$SCRIPT_DIR/src/chrome/browser/ui/webui/ai_panel/" 2>/dev/null || true
fi

if [ -d "$CHROMIUM_SRC/chrome/browser/ui/views/side_panel/" ]; then
    cp -r "$CHROMIUM_SRC/chrome/browser/ui/views/side_panel/"* "$SCRIPT_DIR/src/chrome/browser/ui/views/side_panel/" 2>/dev/null || echo "Note: side_panel directory not found yet"
fi

echo "✓ Sync complete!"
echo ""
echo "Changes synced to: $SCRIPT_DIR/src/"
echo "Review changes with: git status"


