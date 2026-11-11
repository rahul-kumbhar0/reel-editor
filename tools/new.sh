#!/usr/bin/env bash
# Start a project from a style pack. usage: new.sh <style-name> <project-dir>
# Copies the style's index.html + the shared engine into the project (engine/ is a symlink so brand
# token edits in the repo propagate; copy it instead if you want the project self-contained).
set -euo pipefail
E=$(cd "$(dirname "$0")/.." && pwd); S=$E/styles/$1; P=$2
[ -f "$S/index.html" ] || { echo "no such style: $1 (see $E/styles/)"; exit 1; }
mkdir -p "$P"
cp "$S/index.html" "$P/index.html"; [ -f "$S/style.css" ] && cp "$S/style.css" "$P/style.css"
ln -sfn "$E/engine" "$P/engine"
[ -f "$P/display.json" ] || echo '{"merge":[],"replace":{}}' > "$P/display.json"
echo "project $P from style $1 — next: ingest.sh <raw clip> $P"
