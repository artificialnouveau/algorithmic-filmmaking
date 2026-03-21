#!/bin/bash
set -e

echo "=== Installing system dependencies ==="
sudo apt-get update -qq
sudo apt-get install -y -qq ffmpeg > /dev/null 2>&1

echo "=== Installing Python dependencies ==="
pip install -q -r requirements-web.txt

echo ""
echo "============================================"
echo "  Setup complete!"
echo "  Scene Ripper will launch automatically."
echo "  Click the port 7860 link to open it."
echo "============================================"
