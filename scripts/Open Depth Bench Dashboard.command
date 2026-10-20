#!/bin/zsh
set -eu

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${BENCH_DASHBOARD_PORT:-8765}"
PYTHON="${PYTHON:-python3}"
URL="http://127.0.0.1:$PORT"
STATE_DIR="$PROJECT_DIR/.bench_dashboard"

cd "$PROJECT_DIR"
mkdir -p "$STATE_DIR"

if ! /usr/bin/curl --silent --fail "$URL/api/health" >/dev/null 2>&1; then
  /usr/bin/nohup "$PYTHON" scripts/bench_dashboard.py --port "$PORT" > "$STATE_DIR/server.log" 2>&1 &
  echo $! > "$STATE_DIR/server.pid"
  for _attempt in {1..30}; do
    if /usr/bin/curl --silent --fail "$URL/api/health" >/dev/null 2>&1; then
      break
    fi
    sleep 0.1
  done
fi

if ! /usr/bin/curl --silent --fail "$URL/api/health" >/dev/null 2>&1; then
  echo "The dashboard did not start. Check $STATE_DIR/server.log"
  read -r "?Press Return to close."
  exit 1
fi

/usr/bin/open "$URL"
echo "Depth Bench Inspector is running at $URL"
echo "Server log: $STATE_DIR/server.log"
