from setuptools import find_packages, setup

setup(
    name="jetson_realsense_perception",
    version="0.1.0",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=["rclpy", "sensor_msgs"],
    entry_points={
        "console_scripts": [
            "image_monitor=jetson_realsense_perception.image_monitor:main",
            "depth_inspector=jetson_realsense_perception.depth_inspector:main",
            "frame_latency_check=jetson_realsense_perception.frame_latency_check:main",
            "simple_perception_node=jetson_realsense_perception.simple_perception_node:main",
        ],
    },
)
