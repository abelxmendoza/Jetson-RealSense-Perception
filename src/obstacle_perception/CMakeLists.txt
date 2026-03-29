cmake_minimum_required(VERSION 3.8)
project(obstacle_perception)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(obstacle_interfaces REQUIRED)

add_executable(obstacle_node src/obstacle_node.cpp)

ament_target_dependencies(obstacle_node
  rclcpp
  sensor_msgs
  visualization_msgs
  obstacle_interfaces
)

install(TARGETS obstacle_node
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
