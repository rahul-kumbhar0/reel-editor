# Style packs

Every style is `styles/<name>/index.html`: a working page on the test script (`examples/`), written
with the engine helpers and anchored to spoken phrases via `R.at("...")`. To use one: copy it into
the project (`tools/new.sh <name> <project>`), replace the `T = {...}` anchors with phrases from
the new transcript, rewrite the on-screen text (cards, numbers, titles) from what the speaker says,
and keep the layout. Shared look: one accent colour, serif-italic + heavy sans, chest captions with
a small accent chip, dot-matrix reveal at the start, "Comment CUT" end card. Brand knobs are in
`engine/tokens.css :root`.

| style | one line | needs | layout bands (1080×1920) |
|---|---|---|---|
| `glass-explainer` | dark explainer panel on glass cards above, you in a rounded window below | footage | chapter bar y200 · counters y330–530 · big word y900 · PiP 60,1200,960×640 |
| `explainer-panel` | close-ups (hard punch-ins) + a bottom panel that explains the current idea | footage | footage full · panel 60,1300,960×540 · captions move to y1100 while open |
| `cinematic-type` | bold serif type, full-colour cards that cut away from the face on key lines | footage | hook line y220 · full-bleed cards · split half (left 540 colour / right face) |
| `split-reel` | face on top (0–960), animations below (960–1920); window goes full-screen on the hook | footage | top: face, object-position 50% 20% · bottom: title y90, vs row y430, strip y700 |
| `split-screen-document` | document on the left, you on the right, checks/highlights land on the doc | footage (+ img/doc.png) | doc 40,160,560×1600 · face 640,160,400×1000 · tags under face |
| `depth-ui` | interfaces BEHIND your head, chest captions in front | cutouts | dim footage → UI cards (y110–800) → cutout → captions |
| `cutout-grid` | you cut out over a 2×2 image grid that changes per idea | cutouts + img/ | grid full · captions in a dark box y1210 |
| `cutout-backdrop` | you cut out over one full-screen image per idea (slow Ken Burns) | cutouts + img/ | backdrop full · serif kicker y170 · bottom shade for captions |
| `image-cluster` | 2–3 metaphor images cluster above the head, small caption bottom-left | footage + img/ | cluster y200–750 · caption 70,1500 left-aligned 30px |
| `ranking-format` | tier list S→F fills the top, cards drop in as you name them, you in a window below | footage | title y120 · tiers y260+ (150 tall, 24 gap) · PiP 60,1200,960×640 |
| `speedy-devv` | spotlit 3D hero full-bleed + karaoke TOP caption with boxed keyword, colored pill callouts + mono tags + rolling odometer + grey footnote, persona cutout bottom-centre, "Comment KEYWORD" IG end card (@speedy_devv look) | cutouts (hero = 3D b-roll as footage/, persona = cutout/) | caption y200 · definition y340 · pills y560–860 · stat y980 · footnote y1560 · persona bottom 0–720 · adds `--kw-blue`/`--kw-green` callout colours |

Workflow styles (same engine, different input):

| style | what it does | tool |
|---|---|---|
| `personal-short-form-reels` | fast reel from your own B-roll: talking head + B-roll cutaways on every concrete noun, captions | `tools/broll_index.py` search → put clips in `broll/`, show them with a `.footage`-style `<img>` sequence or a `<video>` still per beat; any visual style above |
| `personal-broll-library` | index a folder of your B-roll, search it in plain English | `tools/broll_index.py index|sheet|describe|search` |
| `business-short-form-reels` | full screen → split screen → animation, for a product/company clip | `split-reel` + `explainer-panel` recipes with the product's screenshots in img/ |
| `coaching-call-clips` | a recorded call → ranked 30–60 s clips, each edited in a style | `tools/clips.py` on the full transcript → `cuts.json` per clip → `cut.py` → any style |
| `youtube-clips` | the best clips from a long YouTube video | same as above; the source file comes from the user (the sandbox can't fetch YouTube) |

## Rules that make it look like the reference, not like a template
- One visual idea per sentence. A card appears ON the word, never before it.
- Numbers roll (`R.count`), comparisons pop left then right with a beat between, titles are serif italic in the accent colour.
- Captions: 3–4 words per page, active word white (accent while docked), everything else 45% — the viewer reads along.
- Punch-ins are 1.08–1.18, instant in (0.18 s), on emphasis words only; a 3–4% slow creep the rest of the time.
- Panels/cards use the glass or panel tokens, 1.5 px line, big radius, long soft shadow. No gradients on text, no drop shadows on cards lighter than 50% black.
- The end card is the same in every style: "Comment "<KEYWORD>"" + accent pill + the person in a phone-shaped window, ≥ 3 s.
- Never cover the mouth with UI; keep y 700–1150 clear on a centred talking head unless the footage is docked.

## Image sourcing for img/
Order of preference: the user's own photos/screenshots → public-domain art (Wikimedia Commons, via the
Chrome extension tools since the sandbox blocks it) → generated images (full ElevenLabs connector or
any image tool the user has). Name files as the template expects (`img/1a.jpg` …) or edit the paths.
Never present stock/generated images as the user's own results.
