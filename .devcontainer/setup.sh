#!/bin/bash
set -e

echo "=== Installing system dependencies ==="
sudo apt-get update -qq
sudo apt-get install -y -qq ffmpeg > /dev/null 2>&1

echo "=== Installing Deno (required for YouTube downloads) ==="
curl -fsSL https://deno.land/install.sh | DENO_INSTALL="$HOME/.deno" sh -s -- --yes 2>/dev/null
echo 'export PATH="$HOME/.deno/bin:$PATH"' >> ~/.bashrc
export PATH="$HOME/.deno/bin:$PATH"

echo "=== Installing Python dependencies ==="
pip install -q -r requirements-web.txt

echo ""
echo "============================================"
echo "  Setup complete!"
echo "  Scene Ripper will launch automatically."
echo "  Click the port 7860 link to open it."
echo "============================================"
