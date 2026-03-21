#!/bin/bash

echo "=== Installing system dependencies ==="
sudo apt-get update -qq
sudo apt-get install -y -qq ffmpeg > /dev/null 2>&1 || echo "Warning: ffmpeg install failed"

echo "=== Installing Deno (required for YouTube downloads) ==="
curl -fsSL https://deno.land/install.sh | DENO_INSTALL="$HOME/.deno" sh -s -- --yes 2>/dev/null || echo "Warning: Deno install failed"
echo 'export PATH="$HOME/.deno/bin:$PATH"' >> ~/.bashrc

echo "=== Installing Python dependencies (this may take a few minutes) ==="
pip install -q gradio scenedetect[opencv] opencv-python numpy yt-dlp Pillow scikit-learn google-api-python-client faster-whisper 2>&1 | tail -5
pip install -q torch torchvision transformers 2>&1 | tail -5 || echo "Warning: torch install failed (shot classification will use CPU fallback)"

echo ""
echo "============================================"
echo "  Setup complete!"
echo "  Scene Ripper will launch automatically."
echo "  Click the port 7860 link to open it."
echo "============================================"
