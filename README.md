# Calder Quay

A scroll-driven leasing site for an invented twisting glass residential tower. Scroll to fly around the building, then pick a floor in the availability section to see which residences are free.

The tower, podium, city and sky are all built in code with Three.js (loaded from a CDN), so the page needs an internet connection to show the 3D model.

Edit `src/page.html`, then rebuild the self-contained `index.html`:

```bash
python3 tools/build.py
```

`src/fx/` holds the website-fx-presets renderers (ASCII and liquid orb), unchanged.

The building, residences and prices are invented. The tour form does not send anything.
