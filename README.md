# Calder Quay

A scroll-driven leasing site for an invented twisting glass residential tower. Scroll to fly around the building, then pick a floor in the availability section: the camera flies in, the floors above peel away, and you look down into a furnished cutaway of that floor (kitchens, bathrooms, bedrooms and living rooms, all modelled in code). Click a residence to switch between the two on a floor, drag to turn, and press Esc or "Back to tower" to fly out.

The tower, podium, city and sky are all built in code with Three.js (loaded from a CDN), so the page needs an internet connection to show the 3D model.

Edit `src/page.html`, then rebuild the self-contained `index.html`:

```bash
python3 tools/build.py
```

`src/fx/` holds the website-fx-presets renderers (ASCII and liquid orb), unchanged.

The building, residences and prices are invented. The tour form does not send anything.


## Room tours

Click a room name inside a floor (or "View rooms" in the floor details) and the 3D camera dives at the room, then a full-screen rendered fly-in takes over: it starts above the room with the ceiling lifted off and glides down to eye level, like a developer's leasing site. Tabs switch between the living room, kitchen and dining, primary bedroom and primary bath.

The rooms are modelled and rendered in Blender (Cycles) by `tools/render/rooms.py`; `tools/render/encode.sh` turns the frames into the clips in `media/rooms/`. Calder Quay is fictional, so the renders are labelled as representative finishes.

## Furnished floor models

When you fly into a floor, the furnished cutaway is a Blender model rather than boxes drawn in code. `tools/render/floor.py` models each layout (one residence on half a floor with 1, 2 or 3 bedrooms, plus the full-floor sky residences and penthouses) after real high-end waterfront residences: wide-plank oak floors, 24-inch marble tiles in the baths, oak kitchen runs with marble counters and a waterfall island, freestanding soaking tubs, glass-screened showers and standard furniture sizes. It lights the floor with Cycles, bakes the lighting and materials into one texture, and exports `media/floors/*.glb`, which the page draws as-is (no lights needed, so it stays fast). The room labels and click targets come from the same layout in `src/page.html`; if a model can't load, the page falls back to the code-drawn furniture.

```bash
cd tools/render && ./floors.sh          # needs: pip install bpy (Blender 5.x) and Node for npx
```
