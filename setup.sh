#!/usr/bin/env bash
# One-time setup. usage: bash setup.sh [workspace=/home/claude/reel-work]
# Installs playwright (matches the sandbox Chromium when present), Python deps, and the offline ASR
# model (NVIDIA Parakeet via sherpa-onnx, ~480 MB from GitHub releases — the sandbox blocks Hugging Face).
set -euo pipefail
W=${1:-$HOME/reel-work}; E=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$W/projects" "$HOME/models"
cd "$E"
[ -f package.json ] || npm init -y >/dev/null
[ -d node_modules/playwright ] || npm i -s playwright@1.56.1 >/dev/null 2>&1   # render.mjs resolves playwright from the engine dir
pip install -q --break-system-packages sherpa-onnx "rembg[cpu]" onnxruntime numpy scipy pillow 2>&1 | grep -v -i warn || true
M=$HOME/models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8
if [ ! -f "$M/encoder.int8.onnx" ]; then
  echo "downloading Parakeet ASR model (~480MB)..."
  curl -sS -L -o "$HOME/models/parakeet.tar.bz2" https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2
  tar xjf "$HOME/models/parakeet.tar.bz2" -C "$HOME/models" && rm "$HOME/models/parakeet.tar.bz2"
fi
# fonts (woff2 are not in the repo): pull from fontsource via npm
if [ ! -f "$E/engine/fonts/inter-latin-700-normal.woff2" ]; then
  mkdir -p "$E/engine/fonts"; (cd "$E" && npm i -s @fontsource/inter@5 @fontsource/instrument-serif@5 @fontsource/jetbrains-mono@5 >/dev/null 2>&1)
  for w in 500 600 700 800 900; do cp "$E/node_modules/@fontsource/inter/files/inter-latin-$w-normal.woff2" "$E/engine/fonts/"; done
  cp "$E/node_modules/@fontsource/instrument-serif/files/instrument-serif-latin-400-italic.woff2" "$E/engine/fonts/"
  for w in 500 700; do cp "$E/node_modules/@fontsource/jetbrains-mono/files/jetbrains-mono-latin-$w-normal.woff2" "$E/engine/fonts/"; done
fi
command -v ffmpeg >/dev/null || { echo "ffmpeg missing"; exit 1; }
chmod +x "$E"/tools/*.sh
echo "ready. engine=$E workspace=$W  (new project: bash $E/tools/new.sh <style> $W/projects/<slug>)"
