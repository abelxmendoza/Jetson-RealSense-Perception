cmake_minimum_required(VERSION 3.8)
project(robot_control)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(obstacle_interfaces REQUIRED)

add_executable(control_node src/control_node.cpp)

ament_target_dependencies(control_node
  rclcpp
  std_msgs
  geometry_msgs
  visualization_msgs
  obstacle_interfaces
)

install(TARGETS control_node
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
