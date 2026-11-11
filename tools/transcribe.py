"""Offline transcription with word timestamps -> words.json (ElevenLabs-compatible shape).

usage: python3 transcribe.py audio.wav words.json [--model DIR] [--txt transcript.txt]

Backend: sherpa-onnx + NVIDIA Parakeet-TDT 0.6B v2 (int8), downloaded from GitHub releases by
setup.sh (the sandbox blocks Hugging Face, so Whisper can't fetch its weights there). Output:
  {"words": [{"text": "Hello", "start": 0.12, "end": 0.41, "type": "word"}, ...], "text": "..."}
which is exactly what captions.py / engine.js R.at() consume. If you already have an ElevenLabs
Scribe words.json (e.g. from creative_transcribe_audio on the user's machine), skip this script.
"""
import json, os, sys, wave
import numpy as np

args = sys.argv[1:]
model = os.environ.get("ASR_MODEL", os.path.expanduser("~/models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8"))
txt_out = None
if "--model" in args:
    i = args.index("--model"); model = args[i + 1]; del args[i:i + 2]
if "--txt" in args:
    i = args.index("--txt"); txt_out = args[i + 1]; del args[i:i + 2]
wav_path, out_path = args[:2]

import sherpa_onnx

rec = sherpa_onnx.OfflineRecognizer.from_transducer(
    encoder=f"{model}/encoder.int8.onnx", decoder=f"{model}/decoder.int8.onnx",
    joiner=f"{model}/joiner.int8.onnx", tokens=f"{model}/tokens.txt",
    num_threads=max(2, os.cpu_count() or 2), model_type="nemo_transducer", decoding_method="greedy_search")

with wave.open(wav_path) as w:
    assert w.getframerate() == 16000 and w.getnchannels() == 1, "need 16 kHz mono wav (see ingest.sh)"
    samples = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768

# Long files: decode in ~25 s chunks split at low-energy points so words aren't cut mid-way.
SR = 16000
def chunks(x, target=25 * SR, search=3 * SR):
    i = 0
    while i < len(x):
        if len(x) - i <= target + search: yield i, x[i:]; return
        seg = x[i + target - search:i + target + search]
        win = SR // 20
        energy = np.array([np.abs(seg[j:j + win]).mean() for j in range(0, len(seg) - win, win)])
        cut = i + target - search + int(np.argmin(energy)) * win
        yield i, x[i:cut]; i = cut

words = []
for off, piece in chunks(samples):
    s = rec.create_stream(); s.accept_waveform(SR, piece); rec.decode_stream(s)
    r = s.result
    toks, ts = list(r.tokens), list(r.timestamps)
    cur = None
    for tok, t in zip(toks, ts):
        t = float(t) + off / SR
        if tok.startswith("▁") or tok.startswith(" ") or cur is None:   # sentencepiece word start
            if cur: words.append(cur)
            cur = {"text": tok.lstrip("▁ "), "start": round(t, 3), "end": round(t + 0.08, 3), "type": "word"}
        else:
            cur["text"] += tok; cur["end"] = round(t + 0.08, 3)
    if cur: words.append(cur)

# tighten ends: a word ends when the next one starts (cap 0.6 s), last word +0.35 s
for a, b in zip(words, words[1:]):
    a["end"] = round(min(b["start"], a["start"] + 0.6) if b["start"] > a["start"] else a["end"], 3)
if words: words[-1]["end"] = round(words[-1]["start"] + 0.35, 3)
words = [w for w in words if w["text"].strip()]

text = " ".join(w["text"] for w in words)
json.dump({"words": words, "text": text}, open(out_path, "w"), indent=1)
if txt_out: open(txt_out, "w").write(text + "\n")
print(f"{len(words)} words, {words[-1]['end'] if words else 0:.2f}s")
print(text)
