"""
Full autonomy stack — one command to launch everything.

  ros2 launch jetson_realsense_perception autonomy_stack.launch.py

Optional overrides:
  ros2 launch ... safe_distance:=1.5 forward_speed:=0.3 turn_rate:=0.4

Pipeline:
  D455 → /camera/depth/color/points
       → obstacle_node  → /obstacles + /obstacle_markers
       → control_node   → /cmd_vel  + /cmd_vel_marker
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # ----------------------------------------------------------------
    # Declare overridable launch arguments
    # ----------------------------------------------------------------
    args = [
        DeclareLaunchArgument("safe_distance",
            default_value="1.0",
            description="Stop-and-turn threshold in metres"),
        DeclareLaunchArgument("critical_distance",
            default_value="0.5",
            description="Emergency-stop threshold in metres"),
        DeclareLaunchArgument("forward_speed",
            default_value="0.5",
            description="Forward velocity in m/s"),
        DeclareLaunchArgument("turn_rate",
            default_value="0.5",
            description="Rotation rate in rad/s"),
        DeclareLaunchArgument("sample_stride",
            default_value="8",
            description="PointCloud2 point sampling stride (higher = lighter load)"),
    ]

    # ----------------------------------------------------------------
    # URDF for robot_state_publisher
    # ----------------------------------------------------------------
    urdf_path = os.path.join(
        get_package_share_directory("robot_description"),
        "urdf",
        "robot.urdf",
    )
    with open(urdf_path, "r") as f:
        robot_description = f.read()

    # ----------------------------------------------------------------
    # Nodes
    # ----------------------------------------------------------------
    nodes = [
        # TF tree: base_link → camera_link
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            name="robot_state_publisher",
            output="screen",
            parameters=[{"robot_description": robot_description}],
        ),

        # RealSense D455 driver
        # pointcloud.enable=True is required — obstacle_node subscribes to the cloud
        Node(
            package="realsense2_camera",
            executable="realsense2_camera_node",
            name="camera",
            output="screen",
            parameters=[{
                "pointcloud.enable": True,
                "align_depth.enable": False,
                "depth_module.profile": "640x480x30",
                "rgb_camera.profile":   "640x480x30",
            }],
        ),

        # Perception: PointCloud2 → /obstacles + /obstacle_markers
        Node(
            package="obstacle_perception",
            executable="obstacle_node",
            name="obstacle_node",
            output="screen",
            parameters=[{
                "sample_stride": LaunchConfiguration("sample_stride"),
            }],
        ),

        # Control: /obstacles → /cmd_vel + /cmd_vel_marker
        Node(
            package="robot_control",
            executable="control_node",
            name="control_node",
            output="screen",
            parameters=[{
                "safe_distance":     LaunchConfiguration("safe_distance"),
                "critical_distance": LaunchConfiguration("critical_distance"),
                "forward_speed":     LaunchConfiguration("forward_speed"),
                "turn_rate":         LaunchConfiguration("turn_rate"),
            }],
        ),
    ]

    return LaunchDescription(args + nodes)
