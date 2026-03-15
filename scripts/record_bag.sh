#!/bin/bash

set -e

source scripts/setup_env.sh

ros2 bag record \
  /camera/camera/color/image_raw \
  /camera/camera/depth/image_rect_raw \
  /tf
