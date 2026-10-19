# Jetson RealSense Perception — convenience targets
# Run from repo root

.PHONY: check capture ros-launch ros-sanity bench-dashboard bench-report test-offline help

help:
	@echo "Targets:"
	@echo "  make check       - Run check_realsense.py (verify camera + pyrealsense2)"
	@echo "  make capture     - Capture color + depth to assets/sample_outputs"
	@echo "  make ros-launch - Launch RealSense ROS2 node (sources ROS2 + workspace)"
	@echo "  make ros-sanity - Run ROS topic sanity script (source ROS2 first)"
	@echo "  make bench-dashboard - Start the offline dashboard on localhost"
	@echo "  make bench-report - Generate /tmp/bench-report.json from the fixture"
	@echo "  make test-offline - Run Mac/Linux tests that need no hardware or ROS"

check:
	python3 scripts/check_realsense.py

capture:
	python3 scripts/capture_color_depth.py -o assets/sample_outputs

ros-launch:
	bash scripts/launch_realsense_ros.sh

ros-sanity:
	bash scripts/ros_topic_sanity.sh

bench-dashboard:
	python3 scripts/bench_dashboard.py

bench-report:
	python3 scripts/replay_bench.py tests/fixtures/bench_synthetic.jsonl --output /tmp/bench-report.json

test-offline:
	python3 -m unittest discover -s tests -v
