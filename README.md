# Calder Quay

A scroll-driven leasing site for an invented twisting glass residential tower. Scroll to fly around the building, then pick a floor in the availability section: the camera flies in, the floors above peel away, and you look down into a furnished cutaway of that floor (kitchens, bathrooms, bedrooms and living rooms, all modelled in code). Click a residence to switch between the two on a floor, drag to turn, and press Esc or "Back to tower" to fly out.

The tower, podium, city and sky are all built in code with Three.js (loaded from a CDN), so the page needs an internet connection to show the 3D model.

Edit `src/page.html`, then rebuild the self-contained `index.html`:

```bash
python3 tools/build.py
```

`src/fx/` holds the website-fx-presets renderers (ASCII and liquid orb), unchanged.

The building, residences and prices are invented. The tour form does not send anything.


## Photos

Room photos are free-licensed images from [Unsplash](https://unsplash.com/license), loaded from Unsplash's image CDN and credited to each photographer in the room view. Calder Quay is fictional, so they're labelled as representative interiors.
