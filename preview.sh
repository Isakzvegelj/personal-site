#!/bin/bash
# Run a local copy of the complete site. Nothing is pushed or published.
set -e
cd "$(dirname "$0")"
PORT="${SITE_PREVIEW_PORT:-8877}"

# Reuse an already-running preview instead of starting a second server.
if curl -fsS --max-time 1 "http://127.0.0.1:${PORT}/" 2>/dev/null | grep -q "Isak Žvegelj"; then
  echo "Using existing site preview: http://localhost:${PORT}/"
  exit 0
fi

# Give a useful error if the port is taken by another process.
if lsof -nP -iTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port ${PORT} is already in use by another service." >&2
  echo "Use a different port: SITE_PREVIEW_PORT=9000 ./preview.sh" >&2
  exit 1
fi

echo "Site preview: http://localhost:${PORT}/"
echo "Press Ctrl-C to stop."
python3 -m http.server "$PORT"
