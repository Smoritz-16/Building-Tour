#!/bin/bash
# encode.sh ROOM : rendered frames -> smooth 24fps fly-in clip, opening poster, and high-res resting still.
# Frames come from two passes: 22 evenly-timed frames (out/ROOM) plus extra in-betweens for the fast middle
# of the move (out/ROOM_odd, on a 43-frame grid). Missing in-betweens at the slow ends are blended.
set -e
R=$1
SRC=${SRC:-./out}
DST=${DST:-../../media/rooms}
SEQ=$(mktemp -d)
mkdir -p "$DST"
python3 - "$SRC" "$R" "$SEQ" <<'PY'
import sys, os
from PIL import Image
src, r, seq = sys.argv[1:]
def even(k): return Image.open(f'{src}/{r}/{k:03d}.jpg').convert('RGB')
for i in range(43):
    if i % 2 == 0:
        im = even(i // 2)
    else:
        odd = f'{src}/{r}_odd/{i:03d}.jpg'
        im = Image.open(odd).convert('RGB') if os.path.exists(odd) else Image.blend(even(i // 2), even(i // 2 + 1), 0.5)
    # a re-rendered even frame (on the 43 grid) replaces the original if present
    fix = f'{src}/{r}_odd/{i:03d}.jpg'
    if i % 2 == 0 and os.path.exists(fix):
        im = Image.open(fix).convert('RGB')
    im.save(f'{seq}/{i:03d}.png')
PY
ffmpeg -y -loglevel error -framerate 14 -i "$SEQ/%03d.png" \
  -vf "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,scale=1280:720:flags=lanczos,format=yuv420p" \
  -c:v libx264 -preset veryfast -crf 21 -movflags +faststart -an "$DST/$R.mp4"
ffmpeg -y -loglevel error -i "$SRC/$R/000.jpg" -vf scale=1280:720:flags=lanczos -q:v 4 "$DST/$R-top.jpg"
ffmpeg -y -loglevel error -i "$SRC/${R}_final/021.jpg" -q:v 3 "$DST/$R.jpg"
rm -rf "$SEQ"
ls -la "$DST/$R"*
