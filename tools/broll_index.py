"""Index a folder of your own B-roll so it can be searched in plain English.

usage: python3 broll_index.py index <broll-dir> [index.json]     # build/refresh the index
       python3 broll_index.py search index.json "gym morning sunrise" [--top 5]
       python3 broll_index.py sheet index.json sheet.png              # contact sheet of every clip (look at it once,
                                                                      # then add descriptions with `describe`)
       python3 broll_index.py describe index.json <file> "two people shaking hands in an office"

The index stores per clip: path, duration, size, one thumbnail (thumbs/), and a free-text
description (from the filename at first; add better ones after viewing the sheet). Search is
keyword overlap over filename + description + folder names — simple, fast, no model needed. Claude
reads the top hits and picks the clip that fits the sentence being spoken.
"""
import json, os, re, subprocess, sys

cmd, *a = sys.argv[1:]
VID = (".mp4", ".mov", ".mkv", ".webm", ".m4v")
tok = lambda s: set(re.findall(r"[a-z0-9]+", s.lower()))

if cmd == "index":
    root = a[0]; out = a[1] if len(a) > 1 else os.path.join(root, "broll_index.json")
    old = {c["path"]: c for c in json.load(open(out))["clips"]} if os.path.exists(out) else {}
    thumbs = os.path.join(os.path.dirname(out) or ".", "thumbs"); os.makedirs(thumbs, exist_ok=True)
    clips = []
    for d, _, fs in os.walk(root):
        for f in sorted(fs):
            if not f.lower().endswith(VID): continue
            p = os.path.join(d, f)
            dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip()
            th = os.path.join(thumbs, re.sub(r"\W+", "_", os.path.relpath(p, root)) + ".jpg")
            if not os.path.exists(th):
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(min(1.0, float(dur or 1) / 2)), "-i", p, "-frames:v", "1", "-vf", "scale=320:-1", th])
            desc = old.get(p, {}).get("description") or re.sub(r"[_\-.]+", " ", os.path.splitext(os.path.relpath(p, root))[0])
            clips.append({"path": p, "duration": round(float(dur or 0), 2), "thumb": th, "description": desc})
    json.dump({"root": root, "clips": clips}, open(out, "w"), indent=1); print(f"indexed {len(clips)} clips -> {out}")
elif cmd == "search":
    idx = json.load(open(a[0])); q = tok(a[1]); top = int(a[a.index("--top") + 1]) if "--top" in a else 5
    scored = sorted(idx["clips"], key=lambda c: -len(q & tok(c["description"] + " " + c["path"])))
    for c in scored[:top]:
        hit = len(q & tok(c["description"] + " " + c["path"]))
        if hit == 0: break
        print(f"{hit:2}  {c['duration']:6.1f}s  {c['path']}\n     {c['description']}")
elif cmd == "sheet":
    idx = json.load(open(a[0])); ths = [c["thumb"] for c in idx["clips"] if os.path.exists(c["thumb"])]
    lst = "/tmp/_broll_list.txt"; open(lst, "w").write("".join(f"file '{os.path.abspath(t)}'\n" for t in ths))
    cols = 6; rows = -(-len(ths) // cols)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-vf", f"scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2,tile={cols}x{rows}:padding=4:color=white", "-frames:v", "1", a[1]])
    for i, c in enumerate(idx["clips"]): print(i, os.path.basename(c["path"]))
    print("sheet:", a[1], "(clips are numbered left-to-right, top-to-bottom)")
elif cmd == "describe":
    idx = json.load(open(a[0])); hit = [c for c in idx["clips"] if c["path"].endswith(a[1]) or os.path.basename(c["path"]) == a[1]]
    for c in hit: c["description"] = a[2]
    json.dump(idx, open(a[0], "w"), indent=1); print(f"updated {len(hit)} clip(s)")
