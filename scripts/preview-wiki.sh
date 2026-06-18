#!/usr/bin/env bash
# Local wiki preview with auto-rebuild of obfuscated JS on source changes.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PORT="${WIKI_PREVIEW_PORT:-8765}"
WATCH_PID=""

cleanup() {
  if [ -n "$WATCH_PID" ] && kill -0 "$WATCH_PID" 2>/dev/null; then
    kill "$WATCH_PID" 2>/dev/null || true
    wait "$WATCH_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

if [ ! -d node_modules ]; then
  echo "Installing wiki build dependencies…"
  npm install --no-fund --no-audit
fi

echo "Building obfuscated JS (js/dist/)…"
npm run build:web

echo "Watching js/shield.js, js/core.js, js/search.js for changes…"
npm run watch:web &
WATCH_PID=$!

echo "Wiki preview: http://localhost:${PORT}"
echo "Press Ctrl+C to stop."
python3 -m http.server "$PORT"
