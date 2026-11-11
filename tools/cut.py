"""Apply a cut list to the footage and remap the word timings.

usage: python3 cut.py <project> cuts.json
  reads  <project>/src.mp4, voice.wav, words.json
  writes <project>/cut.mp4, cut_voice.wav, cut_words.json   (timeline = the edited reel)
cuts.json: {"keep": [[start, end], ...]} in source seconds, ascending. Make it with beats.py --cuts
(auto-tighten pauses) or by hand (drop a flubbed take, reorder sentences — segments may be in any order).
"""
import json, os, subprocess, sys

P, cuts = sys.argv[1], json.load(open(sys.argv[2]))["keep"]
src, voice = f"{P}/src.mp4", f"{P}/voice.wav"
W = json.load(open(f"{P}/words.json"))["words"]

parts_v, parts_a, new_words, t = [], [], [], 0.0
for n, (a, b) in enumerate(cuts):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(a), "-to", str(b), "-i", src, "-an",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-r", "30", f"{P}/_seg{n}.mp4"], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(a), "-to", str(b), "-i", voice, "-c:a", "pcm_s16le", f"{P}/_seg{n}.wav"], check=True)
    parts_v.append(f"file '_seg{n}.mp4'"); parts_a.append(f"file '_seg{n}.wav'")
    for w in W:
        if w["start"] >= a - 0.02 and w["end"] <= b + 0.02:
            new_words.append({**w, "start": round(w["start"] - a + t, 3), "end": round(w["end"] - a + t, 3)})
    t += b - a
open(f"{P}/_v.txt", "w").write("\n".join(parts_v)); open(f"{P}/_a.txt", "w").write("\n".join(parts_a))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{P}/_v.txt", "-c", "copy", f"{P}/cut.mp4"], check=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{P}/_a.txt", "-c:a", "pcm_s16le", f"{P}/cut_voice.wav"], check=True)
for f in os.listdir(P):
    if f.startswith("_seg") or f in ("_v.txt", "_a.txt"): os.remove(f"{P}/{f}")
json.dump({"words": new_words, "text": " ".join(w["text"] for w in new_words)}, open(f"{P}/cut_words.json", "w"), indent=1)
print(f"cut.mp4 {t:.2f}s from {len(cuts)} segments, {len(new_words)} words")
