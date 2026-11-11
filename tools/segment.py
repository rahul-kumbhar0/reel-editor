"""Cut the person out of every footage frame -> RGBA PNGs (for depth-ui / cutout styles).

usage: python3 segment.py <frames-dir> <out-dir> [--model u2net_human_seg] [--scale 0.5] [--every 1]
  --scale  run the matting at this fraction of 1080x1920 (0.5 = 540x960, ~4x faster; alpha is
           upscaled with feathering so it still looks clean at full size)
  --every  segment every Nth frame and reuse the mask in between (2 = half the time; fine for
           a seated talking head)
Model weights come from GitHub releases (works in the sandbox). u2net_human_seg is tuned for
people; isnet-general-use is sharper on hair but slower.
"""
import os, sys
import numpy as np
from PIL import Image, ImageFilter

args = sys.argv[1:]; model = "u2net_human_seg"; scale = 0.5; every = 1
if "--model" in args: i = args.index("--model"); model = args[i + 1]; del args[i:i + 2]
if "--scale" in args: i = args.index("--scale"); scale = float(args[i + 1]); del args[i:i + 2]
if "--every" in args: i = args.index("--every"); every = int(args[i + 1]); del args[i:i + 2]
src, out = args[:2]; os.makedirs(out, exist_ok=True)

from rembg import new_session, remove
sess = new_session(model)
files = sorted(f for f in os.listdir(src) if f.endswith(".jpg"))
mask = None
for n, f in enumerate(files):
    im = Image.open(f"{src}/{f}").convert("RGB")
    if n % every == 0 or mask is None:
        small = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
        a = remove(small, session=sess, only_mask=True, post_process_mask=True)
        mask = a.resize(im.size, Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.2))
    rgba = im.copy(); rgba.putalpha(mask)
    rgba.save(f"{out}/{os.path.splitext(f)[0]}.png", optimize=False, compress_level=3)
    if n % 60 == 0: print(f"{n}/{len(files)}")
print(f"wrote {len(files)} cutouts to {out}")
