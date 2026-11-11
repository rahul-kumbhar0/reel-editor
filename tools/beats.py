"""Print the transcript as an edit sheet: sentences with timings, pauses and a suggested cut list.

usage: python3 beats.py words.json [--gap 0.45] [--cuts cuts.json]
  --gap   pauses longer than this (s) are listed as cut candidates (default 0.45)
  --cuts  write {"keep": [[s,e], ...]} that drops every pause > gap (tightened jump-cut edit)

Read the sheet, then decide the beats yourself: which sentence gets a card, a number, a comparison,
an image, a title. Keep the speaker's own words as R.at("...") anchors in index.html.
"""
import json, sys

args = sys.argv[1:]; gap = 0.45; cuts = None
if "--gap" in args: i = args.index("--gap"); gap = float(args[i + 1]); del args[i:i + 2]
if "--cuts" in args: i = args.index("--cuts"); cuts = args[i + 1]; del args[i:i + 2]
W = [w for w in json.load(open(args[0]))["words"] if w.get("type", "word") == "word"]

print(f"{len(W)} words, {W[-1]['end']:.2f}s, {len(W) / max(0.1, W[-1]['end']):.1f} words/s\n")
sent, out, pauses = [], [], []
for i, w in enumerate(W):
    sent.append(w)
    nxt = W[i + 1]["start"] if i + 1 < len(W) else None
    g = (nxt - w["end"]) if nxt is not None else 0
    if g > gap: pauses.append((w["end"], nxt, g))
    if w["text"].rstrip()[-1:] in ".?!" or g > 0.9 or nxt is None:
        out.append(sent); sent = []
for n, s in enumerate(out, 1):
    print(f"[{n:02}] {s[0]['start']:6.2f}-{s[-1]['end']:6.2f}  {' '.join(x['text'] for x in s)}")
print("\npauses > %.2fs:" % gap)
for a, b, g in pauses: print(f"   {a:6.2f} -> {b:6.2f}  ({g:.2f}s)")
if cuts:
    keep, start = [], 0.0
    for a, b, g in pauses:
        keep.append([round(start, 3), round(a + 0.12, 3)]); start = b - 0.10
    keep.append([round(start, 3), round(W[-1]["end"] + 0.6, 3)])
    json.dump({"keep": keep}, open(cuts, "w"), indent=1)
    print(f"\nwrote {cuts}: {len(keep)} segments, removes {sum(g - 0.22 for *_, g in pauses):.2f}s")
