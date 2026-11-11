# reel-edit-engine

Edit a raw talking-head clip into a styled Instagram Reel / Short with code: offline transcription
with word timestamps, jump cuts, word-synced captions, HTML/CSS overlays rendered frame-by-frame
over the footage, person cut-outs for "UI behind your head" looks, synthesized SFX + music, and a
set of **style packs** (`styles/`) that reproduce the 20-style "Claude can edit videos" look.

```
raw.mp4 ─ingest─▶ src.mp4 + src.wav ─transcribe─▶ words.json ─beats/cut─▶ cut.mp4 + cut_words.json
        ─frames─▶ footage/00000.jpg… ─(segment)─▶ cutout/00000.png…
        ─captions─▶ captions.js/.srt ─▶ styles/<name>/index.html (R.at("phrase") anchors)
        ─render.mjs─▶ video.mp4 ─sfx/music/mix─▶ out/<slug>.mp4  (+ cover, SRT, caption)
```

Setup: `bash setup.sh` (installs playwright, sherpa-onnx + Parakeet ASR from GitHub releases,
rembg, fonts). Usage is documented in `SKILL.md` (the Claude skill) and `STYLES.md` (the packs).
Everything in `tools/` is a small standalone script; `engine/engine.js` is the animation runtime
(pure functions of time `t`), `engine/tokens.css` holds the brand knobs.

Credits: workflow modelled on Ajené Pinnock's "20 editing styles for Claude" reels; animation engine
derived from the tech-reel-studio skill.
