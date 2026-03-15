#!/bin/bash

set -e

source scripts/setup_env.sh

echo "Available topics:"
ros2 topic list

echo "Camera info:"
ros2 topic echo /camera/camera/color/camera_info --once
