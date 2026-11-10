#!/bin/bash
# Double-click to open the Calder Quay site with everything working.
# Browsers block a page opened straight from a folder (file://) from loading its 3D models,
# so this serves the folder on http://localhost and opens it there. Close this window to stop.
cd "$(dirname "$0")"
PORT=8765
while lsof -i :$PORT >/dev/null 2>&1; do PORT=$((PORT + 1)); done
echo "Calder Quay is running at http://localhost:$PORT  (close this window to stop)"
( sleep 1; open "http://localhost:$PORT/index.html" ) &
exec python3 -m http.server $PORT --bind 127.0.0.1
