#!/bin/bash

set -e

source scripts/setup_env.sh

ros2 launch realsense2_camera rs_launch.py \
  enable_color:=true \
  enable_depth:=true \
  enable_sync:=true \
  pointcloud.enable:=false \
  align_depth.enable:=false
