#!/usr/bin/env bash
# Normalise a raw talking-head clip for editing.
# usage: ingest.sh <raw.mp4|mov> <project-dir>
# writes <project>/src.mp4 (1080x1920 30fps h264, cover-cropped), <project>/src.wav (16k mono, for ASR),
#        <project>/voice.wav (48k, the clean speech track used in the final mix)
set -euo pipefail
RAW=$1 P=$2; mkdir -p "$P"
ffmpeg -y -loglevel error -i "$RAW" \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p" \
  -c:v libx264 -preset fast -crf 18 -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$P/src.mp4"
ffmpeg -y -loglevel error -i "$P/src.mp4" -vn -ac 1 -ar 16000 -sample_fmt s16 "$P/src.wav"
ffmpeg -y -loglevel error -i "$P/src.mp4" -vn -ac 1 -ar 48000 \
  -af "highpass=f=80,lowpass=f=12000,afftdn=nf=-25,acompressor=threshold=-18dB:ratio=2.5:attack=5:release=120:makeup=2,loudnorm=I=-16:TP=-1.5:LRA=9" "$P/voice.wav"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$P/src.mp4" | xargs printf "ingested %s -> %s (%.2fs)\n" "$RAW" "$P/src.mp4"
