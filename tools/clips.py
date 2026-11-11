"""Find the best short-clip windows in a long recording (YouTube video, coaching call, podcast).

usage: python3 clips.py words.json [--min 25] [--max 60] [--top 8] [--out clips.json]
Scores every sentence-aligned window by: hook strength of the opening line (questions, numbers,
contrast words, "here's", "the truth", imperative verbs), density of numbers/specifics, speech rate,
and a self-contained ending (sentence boundary, no dangling "and"/"so"). Prints a ranked sheet;
--out writes [{"start","end","score","hook","text"}] you can turn into cuts.json ({"keep":[[s,e]]})
for cut.py. You (Claude) still read the transcripts and pick — the score is a shortlist, not a verdict.
"""
import json, re, sys

args = sys.argv[1:]; MIN, MAX, TOP, OUT = 25.0, 60.0, 8, None
for flag, cast in (("--min", float), ("--max", float), ("--top", int), ("--out", str)):
    if flag in args: i = args.index(flag); v = cast(args[i + 1]); del args[i:i + 2]; globals()[flag[2:].upper()] = v
W = [w for w in json.load(open(args[0]))["words"] if w.get("type", "word") == "word"]

sents, cur = [], []
for i, w in enumerate(W):
    cur.append(w); gap = W[i + 1]["start"] - w["end"] if i + 1 < len(W) else 9
    if re.search(r"[.?!]$", w["text"]) or gap > 0.8: sents.append(cur); cur = []
if cur: sents.append(cur)
S = [{"s": x[0]["start"], "e": x[-1]["end"], "t": " ".join(w["text"] for w in x)} for x in sents]

HOOK = [r"\?", r"\b\d", r"\b(nobody|no one|everyone|most people|the truth|here's|secret|mistake|stop|never|always|why|how|what if|versus|vs|instead)\b",
        r"^(stop|don't|never|imagine|listen|look|watch|pick|think)\b", r"\b(biggest|only|one thing|number one|first)\b"]
def hook_score(t):
    t = t.lower(); return sum(1 for p in HOOK if re.search(p, t)) + (1 if len(t.split()) <= 12 else 0)
def specifics(t): return len(re.findall(r"\b\d[\d,.%kKxX]*\b|\b(rupee|lakh|crore|dollar|percent|days?|weeks?|months?|years?)\b", t.lower()))

wins = []
for i in range(len(S)):
    for j in range(i, len(S)):
        dur = S[j]["e"] - S[i]["s"]
        if dur < MIN: continue
        if dur > MAX: break
        text = " ".join(x["t"] for x in S[i:j + 1]); words = len(text.split())
        rate = words / dur
        ending = 1.0 if re.search(r"[.?!]$", S[j]["t"]) and not re.search(r"\b(and|so|but|because|which)[.?!]?$", S[j]["t"].lower()) else 0.0
        score = 3 * hook_score(S[i]["t"]) + 1.2 * specifics(text) + 2 * ending + (1.5 if 2.3 <= rate <= 3.6 else 0) - 0.02 * max(0, dur - 40)
        wins.append({"start": round(S[i]["s"], 2), "end": round(S[j]["e"] + 0.4, 2), "score": round(score, 2), "hook": S[i]["t"], "text": text})
wins.sort(key=lambda w: -w["score"])
picked = []
for w in wins:   # greedy, non-overlapping
    if all(w["end"] < p["start"] or w["start"] > p["end"] for p in picked): picked.append(w)
    if len(picked) >= TOP: break
for n, w in enumerate(picked, 1):
    print(f"#{n}  {w['start']:7.2f}-{w['end']:7.2f}  ({w['end'] - w['start']:4.1f}s)  score {w['score']}\n    hook: {w['hook']}\n    {w['text'][:220]}{'…' if len(w['text']) > 220 else ''}\n")
if OUT: json.dump(picked, open(OUT, "w"), indent=1); print("wrote", OUT)
