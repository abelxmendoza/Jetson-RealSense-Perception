#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="127.0.0.1"
PORT="${BENCH_DASHBOARD_PORT:-8765}"
URL="http://${HOST}:${PORT}"
STATE_DIR="${PROJECT_DIR}/.bench_dashboard"
PYTHON="${PYTHON:-python3}"

health_check() {
  "${PYTHON}" - "${URL}/api/health" <<'PY' >/dev/null 2>&1
import sys
from urllib.request import urlopen

with urlopen(sys.argv[1], timeout=0.5) as response:
    if response.status != 200:
        raise SystemExit(1)
PY
}

mkdir -p "${STATE_DIR}"

if ! health_check; then
  nohup "${PYTHON}" "${PROJECT_DIR}/scripts/bench_dashboard.py" \
    --host "${HOST}" --port "${PORT}" \
    >"${STATE_DIR}/server.log" 2>&1 &
  echo $! >"${STATE_DIR}/server.pid"

  for _attempt in $(seq 1 30); do
    if health_check; then
      break
    fi
    sleep 0.1
  done
fi

if ! health_check; then
  echo "The dashboard did not start. Check ${STATE_DIR}/server.log" >&2
  exit 1
fi

echo "Depth Bench Inspector is running at ${URL}"
echo "Server log: ${STATE_DIR}/server.log"

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "${URL}" >/dev/null 2>&1 || true
elif command -v gio >/dev/null 2>&1; then
  gio open "${URL}" >/dev/null 2>&1 || true
else
  echo "No desktop URL opener found; open ${URL} in a browser."
fi
