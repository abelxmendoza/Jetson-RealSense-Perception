#!/usr/bin/env python3
"""Serve the recorded-run dashboard on localhost using only Python stdlib."""

from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from jetson_realsense_perception.bench_recording import RecordingError, load_jsonl, parse_jsonl_text  # noqa: E402
from replay_bench import build_report  # noqa: E402

DASHBOARD_DIR = REPO_ROOT / "dashboard"
DEFAULT_RECORDING = REPO_ROOT / "tests" / "fixtures" / "bench_synthetic.jsonl"
MAX_REQUEST_BYTES = 25 * 1024 * 1024


class DashboardHandler(SimpleHTTPRequestHandler):
    server_version = "BenchDashboard/1.0"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/default":
            try:
                self._json(200, build_report(load_jsonl(DEFAULT_RECORDING)))
            except RecordingError as exc:
                self._json(500, {"error": str(exc)})
            return
        if self.path == "/api/health":
            self._json(200, {"ok": True, "default_recording": DEFAULT_RECORDING.name})
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/replay":
            self._json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise RecordingError("request must contain a recording no larger than 25 MiB")
            request = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(request, dict) or not isinstance(request.get("content"), str):
                raise RecordingError("request must contain string fields: name and content")
            name = request.get("name", "recording.jsonl")
            if not isinstance(name, str):
                raise RecordingError("recording name must be a string")
            report = build_report(parse_jsonl_text(request["content"], Path(name).name))
        except (RecordingError, UnicodeError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})
            return
        self._json(200, report)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"dashboard: {format % args}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="bind address (default: localhost only)")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"Bench dashboard: http://{args.host}:{server.server_port}", flush=True)
    print("Recordings stay on this computer; press Ctrl-C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
