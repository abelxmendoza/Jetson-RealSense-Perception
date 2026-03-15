#!/bin/bash

set -e

source scripts/setup_env.sh

ros2 launch foxglove_bridge foxglove_bridge_launch.xml port:=8765

echo "Foxglove websocket available at:"
echo "ws://JETSON_IP:8765"
