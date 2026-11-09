#!/bin/bash
# floors.sh [LAYOUT...] : bake the furnished floor models for the 3D cutaway into media/floors/.
# Each layout is modelled and lit in Blender (floor.py), baked into one texture, then its geometry is
# compressed with meshopt (gltf-transform, fetched by npx) so the browser downloads ~1 MB per model.
#   SAMPLES=128 TEX=2048 ./floors.sh            # all four (half1 half2 half3 full); takes ~1.5-2 h on CPU
#   ./floors.sh half2                          # just one
set -e
cd "$(dirname "$0")"
DST=${DST:-../../media/floors}
OUT=${OUT:-./out/floors}
SAMPLES=${SAMPLES:-128}
mkdir -p "$DST" "$OUT"
LAYOUTS=${*:-half1 half2 half3 full}
for L in $LAYOUTS; do
  T=${TEX:-2048}; [ "$L" = full ] && T=${TEX_FULL:-3072}
  echo "== $L: ${T}px, $SAMPLES samples"
  python3 floor.py "$L" "$OUT/$L.glb" --tex "$T" --samples "$SAMPLES"
  npx --yes @gltf-transform/cli@4 meshopt "$OUT/$L.glb" "$DST/$L.glb" --level medium
  ls -la "$DST/$L.glb"
done
