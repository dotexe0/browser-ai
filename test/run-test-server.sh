#!/bin/bash
# Simple test server for Layer 1 verification

echo "Starting test server on http://localhost:8000"
echo "Open http://localhost:8000/test/layer1-test.html in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd "$(dirname "$0")/.." || exit

# Try python3 first, then python, then fall back to php
if command -v python3 &> /dev/null; then
    python3 -m http.server 8000
elif command -v python &> /dev/null; then
    python -m http.server 8000
elif command -v php &> /dev/null; then
    php -S localhost:8000
else
    echo "Error: No suitable server found. Please install Python 3 or PHP."
    exit 1
fi

