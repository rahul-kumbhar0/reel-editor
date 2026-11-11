#!/usr/bin/env bash
# QA a finished reel: stream info + contact sheet (one frame every 3 s). Then READ the sheet image.
# usage: qa.sh <reel.mp4> <sheet.png>
set -euo pipefail
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate:format=duration,size -of default=nw=1 "$1"
ffmpeg -y -loglevel error -i "$1" -vf "fps=1/3,scale=216:-1,tile=6x4:padding=4:color=white" -frames:v 1 "$2"
echo "contact sheet: $2"
