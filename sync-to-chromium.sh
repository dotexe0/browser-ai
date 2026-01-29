#!/bin/bash
# Sync custom files to chromium source tree and patch for AI Panel integration.
# Usage: ./sync-to-chromium.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CHROMIUM_SRC="$SCRIPT_DIR/chromium/src"

if [ ! -d "$CHROMIUM_SRC" ]; then
    echo "Error: Chromium source not found at $CHROMIUM_SRC"
    echo "Please fetch chromium source first."
    exit 1
fi

echo "=========================================="
echo "  Syncing AI Panel to Chromium"
echo "=========================================="
echo ""

# Step 1: Copy source files (C++ headers, implementations, BUILD.gn)
echo "[1/3] Copying source files..."
cp -r "$SCRIPT_DIR/src/"* "$CHROMIUM_SRC/"
echo "  Copied src/ -> chromium/src/"

# Step 2: Copy resource files to the GRD-expected location
# browser_resources.grd references: resources/side_panel/ai_panel/*
# Relative to chrome/browser/, so the target is:
#   chromium/src/chrome/browser/resources/side_panel/ai_panel/
echo ""
echo "[2/3] Copying resource files..."
RESOURCES_SRC="$SCRIPT_DIR/src/chrome/browser/ui/webui/ai_panel/resources"
RESOURCES_DST="$CHROMIUM_SRC/chrome/browser/resources/side_panel/ai_panel"

mkdir -p "$RESOURCES_DST"
cp "$RESOURCES_SRC/"*.html "$RESOURCES_DST/" 2>/dev/null || true
cp "$RESOURCES_SRC/"*.js "$RESOURCES_DST/" 2>/dev/null || true
cp "$RESOURCES_SRC/"*.css "$RESOURCES_DST/" 2>/dev/null || true
echo "  Copied resources -> chrome/browser/resources/side_panel/ai_panel/"

# Step 3: Patch existing Chromium source files
echo ""
echo "[3/3] Patching Chromium source files..."
python3 "$SCRIPT_DIR/patch-chromium.py"

echo ""
echo "=========================================="
echo "  Sync complete! Next steps:"
echo "    cd chromium/src"
echo "    gn gen out/Default"
echo "    autoninja -C out/Default chrome"
echo "=========================================="
