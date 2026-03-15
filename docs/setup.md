# Setup

## Prerequisites

- Ubuntu 22.04
- NVIDIA Jetson Orin Nano
- ROS2 Humble
- Intel RealSense D455

## ROS2 packages

sudo apt update
sudo apt install -y ros-humble-realsense2-camera ros-humble-foxglove-bridge

## Python dependencies

pip3 install -r requirements.txt

## Build (workspace)

cd ~/ros2_ws
colcon build

## Source environment

source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash

## ROS domain (optional)

export ROS_DOMAIN_ID=7
