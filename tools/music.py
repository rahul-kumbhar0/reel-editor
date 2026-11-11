"""Compose an original lo-fi / minimal-electronic tech bed (no samples, no licensing issues).

usage: python3 music.py sections.json out.wav
sections.json: {"bpm":110,"dur":54.5,"groove_in":5.62,"breaks":[[40.32,42.0]],"fade_out":1.6,
                "key":"Am", "seed":11}
  groove_in  when drums + bass enter (put it on the first big reveal, ~4-7 s)
  breaks     drum drop-outs with a riser, ending in a soft impact (use for a theme flip / payoff)
  key        Am (default), Em, Dm, Cm, Fm: transposes the whole progression
Original synthesized music: safe for commercial use, no Content ID.
"""
import json, sys, wave
import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
cfg = json.load(open(sys.argv[1])); out = sys.argv[2]
BPM, DUR = cfg["bpm"], cfg["dur"]
BEAT = 60 / BPM; BAR = 4 * BEAT
N = int(SR * DUR)
rng = np.random.default_rng(cfg.get("seed", 11))
L = np.zeros(N); R = np.zeros(N)

def hz(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, f, o=2): return sosfilt(butter(o, f, "low", fs=SR, output="sos"), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)
def bp(x, a, b): return sosfilt(butter(2, [a, b], "band", fs=SR, output="sos"), x)

def add(sig, at, gl=1.0, gr=None):
    gr = gl if gr is None else gr
    i = int(at * SR)
    if i >= N: return
    j = min(N, i + len(sig)); L[i:j] += sig[: j - i] * gl; R[i:j] += sig[: j - i] * gr

def adsr(n, a, r):
    e = np.ones(n); a, r = int(a * SR), int(r * SR)
    e[:a] = np.linspace(0, 1, a); e[-r:] *= np.linspace(1, 0, r); return e

def saw(f, n, harmonics=10):
    t = np.arange(n) / SR
    return sum(np.sin(2 * np.pi * f * k * t) / k for k in range(1, harmonics + 1)) * 0.6

def tri(f, n):
    t = np.arange(n) / SR
    return 2 * np.abs(2 * ((f * t) % 1) - 1) - 1

# A-minor lo-fi progression: Am7 - Fmaj7 - Cmaj7 - G
SHIFT = {"Am": 0, "Em": -5, "Dm": 5, "Cm": 3, "Fm": -4}[cfg.get("key", "Am")]
CHORDS = [[m + SHIFT for m in c] for c in [[57, 60, 64, 67], [53, 57, 60, 64], [48, 52, 55, 59], [55, 59, 62, 67]]]
ROOTS = [r + SHIFT for r in [45, 41, 48, 43]]
bars = int(np.ceil(DUR / BAR))
g_in = cfg["groove_in"]
BREAKS = cfg.get("breaks") or ([cfg["break"]] if "break" in cfg else [])

def in_break(t): return any(a <= t < b for a, b in BREAKS)

for b in range(bars):
    t0 = b * BAR; ch = CHORDS[b % 4]
    # pad: detuned saws, low-passed, wide
    n = int(SR * (BAR + 0.6))
    for m in ch:
        f = hz(m)
        add(lp(saw(f * 0.997, n), 1100) * adsr(n, 0.35, 0.7) * 0.055, t0, 1.0, 0.75)
        add(lp(saw(f * 1.003, n), 1100) * adsr(n, 0.35, 0.7) * 0.055, t0, 0.75, 1.0)
    # pluck arpeggio, 8th notes, one octave up, with a little stereo echo
    arp = [ch[0], ch[2], ch[1], ch[3], ch[2], ch[1], ch[3], ch[2]]
    for k, m in enumerate(arp):
        at = t0 + k * BEAT / 2
        if in_break(at): continue
        n = int(SR * 0.5); tt = np.arange(n) / SR
        s = lp(tri(hz(m + 12), n), 3200) * np.exp(-tt * 7) * 0.075
        add(s, at, 0.9, 0.6); add(s * 0.35, at + 0.75 * BEAT, 0.4, 0.8)
    if t0 + BAR <= g_in - 0.01:   # intro: no drums/bass yet (light hats in the 2nd half)
        if t0 >= 2.0:
            for k in range(8):
                n = int(SR * 0.05); tt = np.arange(n) / SR
                add(hp(rng.standard_normal(n), 7000) * np.exp(-tt * 90) * 0.035, t0 + k * BEAT / 2 + (0.03 if k % 2 else 0))
        continue
    # bass: root on 1, and-of-2, 3
    for at, dur in [(0, 1.4), (1.5, 0.5), (2, 1.8)]:
        a = t0 + at * BEAT
        if a < g_in or in_break(a): continue
        n = int(SR * dur * BEAT); tt = np.arange(n) / SR; f = hz(ROOTS[b % 4])
        s = (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt)) * adsr(n, 0.01, 0.08) * 0.22
        add(s, a)
    for beat in range(4):
        a = t0 + beat * BEAT
        if a < g_in - 0.02 or in_break(a): continue
        if beat in (0, 2):   # kick
            n = int(SR * 0.35); tt = np.arange(n) / SR
            f = 45 + 105 * np.exp(-tt * 28)
            add(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9) * 0.5, a)
        else:                # soft clap
            n = int(SR * 0.25); tt = np.arange(n) / SR
            add(bp(rng.standard_normal(n), 900, 3200) * np.exp(-tt * 22) * 0.16, a, 0.85, 1.0)
        for h in (0, 1):     # swung 8th hats (open hat on the off-beat after the break)
            ah = a + h * BEAT / 2 + (0.035 if h else 0)
            if in_break(ah): continue
            open_hat = h == 1 and BREAKS and ah >= BREAKS[0][1]
            n = int(SR * (0.18 if open_hat else 0.05)); tt = np.arange(n) / SR
            add(hp(rng.standard_normal(n), 7500) * np.exp(-tt * (18 if open_hat else 85)) * (0.05 if open_hat else 0.04), ah, 0.7, 1.0)

# breakdown risers + soft impacts
for brk0, brk1 in BREAKS:
    n = int(SR * (brk1 - brk0)); tt = np.arange(n) / SR
    add(hp(rng.standard_normal(n), 2500) * (tt / tt[-1]) ** 2 * 0.07, brk0)
    n = int(SR * 1.8); tt = np.arange(n) / SR
    add(lp(rng.standard_normal(n), 6000) * np.exp(-tt * 3) * 0.08, brk1)

# master: fade out, glue, normalise
fo = int(SR * cfg["fade_out"]); fade = np.ones(N); fade[-fo:] = np.linspace(1, 0, fo) ** 1.5
fi = int(SR * 0.08); fade[:fi] = np.linspace(0, 1, fi)
st = np.stack([L, R]) * fade
st = np.tanh(st * 1.4) / 1.4
st /= np.max(np.abs(st)) / 0.89
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st.T * 32767).astype(np.int16).tobytes())
print("wrote", out, f"{DUR}s @ {BPM} bpm")
