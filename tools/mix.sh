#!/usr/bin/env bash
# Mix voice + SFX (+ optional music, ducked under the voice) to -14 LUFS and mux onto the video.
# usage: mix.sh <video.mp4> <voice.mp3|none> <sfx.wav> <music.wav|none> <duration> <out.mp4> [music_gain=0.17]
set -euo pipefail
VIDEO=$1 VOICE=$2 SFX=$3 MUSIC=$4 DUR=$5 OUT=$6 MG=${7:-0.17}
TMP=$(mktemp -d)
VOICE_CHAIN="aresample=48000,highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=2,apad=whole_dur=$DUR"
if [[ "$VOICE" == none ]]; then ffmpeg -y -loglevel error -f lavfi -i "anullsrc=r=48000:cl=mono" -t "$DUR" "$TMP/v.wav"; VOICE="$TMP/v.wav"; fi
if [[ "$MUSIC" != none ]]; then
  ffmpeg -y -loglevel error -i "$VOICE" -i "$SFX" -i "$MUSIC" -filter_complex "\
[0:a]$VOICE_CHAIN,asplit=2[v][key];\
[2:a]volume=$MG[m];[m][key]sidechaincompress=threshold=0.03:ratio=6:attack=25:release=400[md];\
[1:a]volume=0.55[s];\
[v][md][s]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,atrim=0:$DUR[a]" \
  -map "[a]" -ac 2 "$TMP/mix.wav"
else
  ffmpeg -y -loglevel error -i "$VOICE" -i "$SFX" -filter_complex "\
[0:a]$VOICE_CHAIN[v];[1:a]volume=0.55[s];\
[v][s]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,atrim=0:$DUR[a]" \
  -map "[a]" -ac 2 "$TMP/mix.wav"
fi
ffmpeg -y -loglevel error -i "$VIDEO" -i "$TMP/mix.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 \
  -movflags +faststart -shortest "$OUT"
echo "wrote $OUT"; ffmpeg -hide_banner -i "$OUT" -af ebur128 -f null - 2>&1 | grep -A2 "Integrated loudness" | grep "I:" || true
rm -rf "$TMP"
