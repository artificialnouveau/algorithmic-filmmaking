#!/bin/bash
set -e

echo "=== Installing system dependencies ==="
sudo apt-get update -qq
sudo apt-get install -y -qq ffmpeg > /dev/null 2>&1

echo "=== Installing Deno (required for YouTube downloads) ==="
curl -fsSL https://deno.land/install.sh | sh > /dev/null 2>&1
echo 'export PATH="$HOME/.deno/bin:$PATH"' >> ~/.bashrc
export PATH="$HOME/.deno/bin:$PATH"

echo "=== Installing Python dependencies ==="
pip install -q gradio
pip install -q -r requirements-web.txt

echo ""
echo "============================================"
echo "  Setup complete!"
echo ""
echo "  To launch Scene Ripper, run:"
echo "    python -m web.app"
echo ""
echo "  Then open the 'Ports' tab and click"
echo "  the forwarded URL for port 7860."
echo "============================================"
