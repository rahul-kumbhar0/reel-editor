"""Word timings (ElevenLabs transcript words.json) -> caption pages (captions.js) + .srt

usage: python3 captions.py words.json captions.js captions.srt [display.json] [--max N]
  --max N  max words per caption page (default 4). Use 5-6 for fast talkers (>3.5 words/s) so each
           kinetic-headline phrase stays readable for ~1 s.

display.json (optional) maps spoken forms back to on-screen forms:
  {"merge":   [[["two","hundred","ninety-four","K"], "294K"], [["D","X","Ball"], "DX-Ball"]],
   "replace": {"R.E.A.": "REA"}}
Merges match consecutive words case-insensitively, ignoring punctuation; trailing
punctuation of the last spoken word is kept.
"""
import json, re, sys

args = sys.argv[1:]
MAXW = 4
if "--max" in args:
    i = args.index("--max"); MAXW = int(args[i + 1]); del args[i:i + 2]
words_path, out_js, out_srt = args[:3]
disp = json.load(open(args[3])) if len(args) > 3 else {}
MERGES = disp.get("merge", []); REPL = disp.get("replace", {})

words = [w for w in json.load(open(words_path))["words"]
         if w.get("type", "word") == "word" and not re.fullmatch(r"\[.*\]", w["text"])]
norm = lambda s: re.sub(r"[^\w~-]", "", s).lower()

toks, i = [], 0
while i < len(words):
    for seq, shown in MERGES:
        if [norm(w["text"]) for w in words[i:i + len(seq)]] == [norm(s) for s in seq]:
            tail = re.search(r"[.,?!:;]*$", words[i + len(seq) - 1]["text"]).group(0)
            toks.append({"t": shown + tail, "s": words[i]["start"], "e": words[i + len(seq) - 1]["end"]})
            i += len(seq); break
    else:
        w = words[i]; t = w["text"]
        for k, v in REPL.items(): t = t.replace(k, v)
        toks.append({"t": t, "s": w["start"], "e": w["end"]}); i += 1

# pages: split at sentence ends, then cut each sentence into evenly sized pages of <= MAXW tokens
# (5 -> 3+2, 6 -> 3+3, 9 -> 3+3+3) so there are no orphan one-word pages; also break at a long pause
sentences, cur = [], []
for i, k in enumerate(toks):
    cur.append(k)
    gap = toks[i + 1]["s"] - k["e"] if i + 1 < len(toks) else 9
    if re.search(r"[.?!:]$", k["t"]) or (gap > 0.45 and k["t"].endswith(",")) or gap > 0.9:
        sentences.append(cur); cur = []
if cur: sentences.append(cur)
def balanced(seq):
    n = len(seq); k = -(-n // MAXW); base, extra = divmod(n, k); out, i = [], 0
    for j in range(k):
        size = base + (1 if j < extra else 0); out.append(seq[i:i + size]); i += size
    return out

pages = []
for snt in sentences:
    # clauses end at commas; pack whole clauses into pages, split only clauses longer than MAXW
    clauses, c = [], []
    for k in snt:
        c.append(k)
        if k["t"].endswith(","): clauses.append(c); c = []
    if c: clauses.append(c)
    cur = []
    for cl in clauses:
        if len(cur) + len(cl) <= MAXW: cur += cl; continue
        if cur: pages.append(cur); cur = []
        if len(cl) > MAXW:
            parts = balanced(cl); pages.extend(parts[:-1]); cur = parts[-1]
        else:
            cur = cl
    if cur: pages.append(cur)

open(out_js, "w").write("window.CAPTION_PAGES = " + json.dumps(pages) + ";\n")

def ts(x):
    ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"
with open(out_srt, "w") as f:
    for n, p in enumerate(pages, 1):
        f.write(f"{n}\n{ts(p[0]['s'])} --> {ts(p[-1]['e'] + 0.15)}\n{' '.join(k['t'] for k in p)}\n\n")
print(f"{len(toks)} tokens, {len(pages)} pages, speech ends at {toks[-1]['e']:.2f}s")
for p in pages: print(f"{p[0]['s']:6.2f}  {' '.join(k['t'] for k in p)}")
