---
name: reel-edit-engine
description: Edit a raw talking-head clip (the user's own footage) into a finished, post-ready Instagram Reel / TikTok / YouTube Short in one of 20 named editing styles — glass-explainer, cinematic-type, split-reel, depth-ui (UI behind the head), cutout-grid, cutout-backdrop, image-cluster, explainer-panel, ranking-format (tier list), split-screen-document, personal/business short-form, coaching-call-clips, youtube-clips, broll-library — with word-synced chest captions, punch-ins, cards and counters that land on the spoken word, cut-out person over images/UI, synthesized SFX and music, and a "Comment KEYWORD" end card. Use whenever the user uploads or points to a video of themselves talking and asks to edit it, "make it a reel", "/style-name", "edit like Ajené", "cut this into clips", "add captions and B-roll", or wants a new editing style built from a reference reel.
---

# Reel Edit Engine

Raw file goes in → `/style` → edited reel comes out. The engine lives in the repo
**github.com/rahul-kumbhar0/reel-edit-engine** (clone it; everything below refers to it as `$E`).
Scenes are HTML driven by time `t`, rendered frame-by-frame over the footage with Playwright;
captions and every beat are anchored to the speaker's own words (`R.at("phrase")`).

## 0. Setup (once per session, ~2 min)
```bash
git clone --depth 1 https://github.com/rahul-kumbhar0/reel-edit-engine $HOME/reel-edit-engine
E=$HOME/reel-edit-engine; bash $E/setup.sh $HOME/reel-work   # playwright, sherpa-onnx + Parakeet ASR (480MB from GitHub), rembg, fonts
```
Sandbox facts: Hugging Face, storage.googleapis.com, instagram.com and most image/stock hosts are
blocked; GitHub, npm, PyPI, apt work. That is why ASR is sherpa-onnx (GitHub-hosted model) and
why reference reels are viewed through the user's Chrome extension tools (`browser_open`, repeated
`browser_screenshot`, `post_details`). On the user's own machine, Whisper / ElevenLabs Scribe work
too — a `words.json` from either (`{"words":[{text,start,end}]}`) drops straight in.

## 1. Get the clip and the style
- The clip: an upload, a path on the linked computer (stage it), or a long recording for the clip
  styles. If the user gave no clip, ask for one (even a phone recording); never fake footage.
- The style: a `/name` the user typed, or pick for them from the ask (see the table in
  `$E/STYLES.md`): explaining with numbers → glass-explainer / explainer-panel; punchy quotes →
  cinematic-type; comparison or steps → split-reel; "tech/UI vibe" → depth-ui; metaphors / mood →
  image-cluster, cutout-grid, cutout-backdrop; a list → ranking-format; a document or screenshot
  to walk through → split-screen-document; a long recording → coaching-call-clips / youtube-clips.
- The CTA keyword and the handle to show (ask once if unknown; never invent).

## 2. Ingest → transcript → edit sheet
```bash
P=$HOME/reel-work/projects/<slug>; bash $E/tools/new.sh <style> $P
bash $E/tools/ingest.sh <raw clip> $P                              # src.mp4 1080x1920@30, src.wav, cleaned voice.wav
python3 -I $E/tools/transcribe.py $P/src.wav $P/words.json         # word timestamps (offline)
python3 $E/tools/beats.py $P/words.json --cuts $P/cuts.json        # sentences, pauses, auto-tightened cut list
```
Read the sheet. Fix ASR errors you can see (names, product words) with `display.json`
(`{"merge":[[["direct","apply"],"DirectApply"]],"replace":{"red":"read"}}`) — the captions must
show the right spelling even when the recogniser heard it wrong. Edit `cuts.json` if the user
flubbed a take or you want a tighter order (segments can be reordered). Then:
```bash
python3 $E/tools/cut.py $P $P/cuts.json                            # cut.mp4, cut_voice.wav, cut_words.json
bash $E/tools/frames.sh $P/cut.mp4 $P/footage                      # frame sequence the page shows
python3 $E/tools/captions.py $P/cut_words.json $P/captions.js $P/captions.srt $P/display.json --max 4
python3 -I $E/tools/segment.py $P/footage $P/cutout --scale 0.5 --every 2   # ONLY for depth-ui / cutout-* styles (~0.3 s/frame)
```
Long recordings (coaching-call-clips, youtube-clips): run `python3 $E/tools/clips.py words.json
--min 30 --max 60 --top 6` first, read the shortlist, pick the clips with the user (one
AskUserQuestion), write one `cuts.json` per clip, and run the rest per clip.

## 3. Author the scenes (this is the editing)
Open `$P/index.html` (copied from the style pack). Keep the layout; change the content:
1. `window.FOOTAGE.count` = the number printed by frames.sh; `cut: "cutout"` only if you segmented.
2. Rewrite `const T = {...}`: every anchor is a phrase the speaker actually says (copy from the
   edit sheet; `R.at` matches on caption display text, so use the `display.json` spelling).
3. Rewrite the on-screen text from the transcript: the number they say becomes the counter, the
   two things they compare become the two boxes, the three steps become the chapters. Nothing
   invented, nothing generic — if a card has no line in the transcript to land on, delete the card.
4. Style rules are in `$E/STYLES.md` ("Rules that make it look like the reference"). One idea per
   sentence; cards land ON the word; captions 3–4 words; punch-ins on emphasis only; mouth never
   covered; end card ≥ 3 s with the user's keyword.
Then check stills — cheap, do it every time:
```bash
cd $HOME/reel-work; node $E/tools/render.mjs $P/index.html --stills $P/stills 0.5 3 6 9 12 15 18 21 24 27 30
ffmpeg -y -loglevel error -pattern_type glob -i "$P/stills/t*.png" -vf "scale=230:-1,tile=6x2:padding=4:color=white" -frames:v 1 $P/sheet.png
```
Read `sheet.png`. Look for: text overflow, a card over the mouth, captions colliding with a panel,
an empty-looking frame, a phrase that didn't anchor (page error = phrase not found → fix spelling).
Fix, re-still, repeat. Only then render.

## 4. Render, sound, mix, QA
```bash
node $E/tools/render.mjs $P/index.html $P/video.mp4 auto 30 5          # ~3 min per 30 s; run in background
node $E/tools/render.mjs $P/index.html --cues $P/cues.json
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $P/video.mp4); mkdir -p $P/audio $P/out
python3 $E/tools/sfx.py $P/cues.json $D $P/audio/sfx.wav
echo '{"bpm":100,"dur":'$D',"groove_in":0.4,"breaks":[],"fade_out":1.6,"key":"Dm"}' > $P/music.json
python3 $E/tools/music.py $P/music.json $P/audio/music.wav              # original beat; or pass the user's track instead
bash $E/tools/mix.sh $P/video.mp4 $P/cut_voice.wav $P/audio/sfx.wav $P/audio/music.wav $D $P/out/<slug>.mp4 0.12
bash $E/tools/mix.sh $P/video.mp4 $P/cut_voice.wav $P/audio/sfx.wav none $D $P/out/<slug>_nomusic.mp4
bash $E/tools/qa.sh $P/out/<slug>.mp4 $P/qa.png                          # then READ qa.png
```
QA: 1080×1920 h264+aac, −14 LUFS, every beat present, captions readable over every background,
CTA ≥ 3 s with the real keyword/handle, no clipped text, speech never cut mid-word.

## 5. Deliver
Cover = the strongest still (`--stills` at the hook) → `out/cover.png`. Send with SendUserFile
(attach): reel with music, reel without music (for trending audio in-app), cover, `captions.srt`,
and `out/caption.txt` (hook line + 2 lines + "Comment KEYWORD …"). Reply in 3–5 lines: style,
length, what each beat shows, and that re-edits are cheap because the project folder is kept
(changing a card = edit index.html + re-render). Offer the next style on the same clip — the whole
point of the system is one clip, many looks.

## Building a NEW style from a reference reel
1. Watch it with the Chrome extension (`post_details` for caption/stats, `browser_screenshot` ×8
   on the playing reel, or ffmpeg frames if the user uploads the file) and write down: layout bands,
   fonts, the one accent colour, how captions sit, what happens ON each spoken beat, transitions.
2. Copy the closest pack (`styles/<nearest>`) to `styles/<new-name>/index.html`, add a `<style>`
   block with the new components, and express every beat as `R.at`-anchored calls.
3. Test it on the example project (`examples/`), add a row to `STYLES.md`, push to the repo.
Engine API: `R.footage(t)` (awaited frame), `R.rect(el,t,keys)` (dock/undock the footage),
`R.zoom(el,t,[[a,b,scale,ox,oy]],{drift})` punch-ins, `R.rise/pop/words/count/marker/type/wipe/
camera/draw/dots`, `R.at/R.end/R.voiceEnd`, `R.setup({scenes,captions:{hide}})`, `R.frame(t)`.
Every helper is a pure function of `t`; call them unconditionally in `seek` so SFX cues register.

## Brand
`engine/tokens.css :root` — `--accent` (default Ajené orange #E8842A), `--bg`, fonts, `--cap-top`.
For the user's brands switch the accent and keep everything else; that is what makes 20 styles read
as one account.
