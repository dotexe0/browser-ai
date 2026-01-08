#!/bin/bash
# Sync custom files from repo to chromium source tree

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CHROMIUM_SRC="$SCRIPT_DIR/chromium/src"

if [ ! -d "$CHROMIUM_SRC" ]; then
    echo "Error: Chromium source not found at $CHROMIUM_SRC"
    echo "Please fetch chromium source first."
    exit 1
fi

echo "Syncing files to chromium source tree..."

# Sync all files from src/ to chromium/src/
# Using cp -r since rsync may not be available on all systems
cp -r "$SCRIPT_DIR/src/"* "$CHROMIUM_SRC/"

echo "✓ Sync complete!"
echo ""
echo "Files synced to: $CHROMIUM_SRC"


