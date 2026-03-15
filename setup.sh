#!/usr/bin/env bash
# Optional setup: create venv and install pip dependencies.
# RealSense SDK (librealsense) and pyrealsense2 must be installed separately — see docs/software_setup.md

set -e
cd "$(dirname "$0")"

if command -v python3 &>/dev/null; then
    python3 -m pip install --user -r requirements.txt
    echo "Installed Python deps from requirements.txt"
else
    echo "python3 not found"
    exit 1
fi

echo "Done. Install librealsense/pyrealsense2 per docs/software_setup.md"
