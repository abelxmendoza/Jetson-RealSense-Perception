#!/bin/bash

set -e

echo "Sourcing ROS2..."
source /opt/ros/humble/setup.bash

echo "Sourcing workspace..."
source ~/ros2_ws/install/setup.bash

export ROS_DOMAIN_ID=7

echo "Environment ready."
