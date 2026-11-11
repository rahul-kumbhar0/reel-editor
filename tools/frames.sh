#!/usr/bin/env bash
# Extract the edited footage as a JPEG frame sequence the HTML page can show per frame.
# usage: frames.sh <cut.mp4> <out-dir>      ->  <out-dir>/00000.jpg ... (1080x1920 @30fps)
set -euo pipefail
mkdir -p "$2"; rm -f "$2"/*.jpg
ffmpeg -y -loglevel error -i "$1" -vf "fps=30,scale=1080:1920" -start_number 0 -q:v 3 "$2/%05d.jpg"
N=$(ls "$2" | wc -l); echo "$N frames in $2  (set FOOTAGE.count=$N)"
