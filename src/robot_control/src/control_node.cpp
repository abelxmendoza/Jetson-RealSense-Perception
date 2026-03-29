#include <cmath>
#include <limits>

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <std_msgs/msg/header.hpp>
#include <visualization_msgs/msg/marker.hpp>

#include <obstacle_interfaces/msg/obstacle_array.hpp>

using std::placeholders::_1;

class ControlNode : public rclcpp::Node
{
public:
  ControlNode() : Node("control_node")
  {
    // All tuning values are runtime-overridable via launch file or ros2 param set
    declare_parameter("safe_distance",     1.0);
    declare_parameter("critical_distance", 0.5);
    declare_parameter("forward_speed",     0.5);
    declare_parameter("turn_rate",         0.5);

    safe_distance_     = get_parameter("safe_distance").as_double();
    critical_distance_ = get_parameter("critical_distance").as_double();
    forward_speed_     = get_parameter("forward_speed").as_double();
    turn_rate_         = get_parameter("turn_rate").as_double();

    obstacle_sub_ = create_subscription<obstacle_interfaces::msg::ObstacleArray>(
      "/obstacles", 10,
      std::bind(&ControlNode::obstacle_callback, this, _1));

    cmd_pub_ = create_publisher<geometry_msgs::msg::Twist>("/cmd_vel", 10);

    marker_pub_ = create_publisher<visualization_msgs::msg::Marker>(
      "/cmd_vel_marker", 10);

    RCLCPP_INFO(get_logger(),
      "ControlNode ready — safe=%.1fm  critical=%.1fm  fwd=%.2fm/s  turn=%.2frad/s",
      safe_distance_, critical_distance_, forward_speed_, turn_rate_);
  }

private:
  void obstacle_callback(const obstacle_interfaces::msg::ObstacleArray::SharedPtr msg)
  {
    // Find the closest obstacle within safe_distance and record its y position
    // to determine which way to turn (directional avoidance).
    float closest_dist = std::numeric_limits<float>::max();
    float closest_y    = 0.0f;

    for (const auto & obs : msg->obstacles) {
      if (obs.distance < static_cast<float>(safe_distance_) &&
          obs.distance < closest_dist)
      {
        closest_dist = obs.distance;
        closest_y    = obs.y;
      }
    }

    geometry_msgs::msg::Twist cmd;
    const bool obstacle_close = (closest_dist < static_cast<float>(safe_distance_));

    if (obstacle_close) {
      cmd.linear.x = 0.0;

      // Obstacle on the LEFT  (y > 0 in camera frame) → turn RIGHT (negative z)
      // Obstacle on the RIGHT (y < 0 in camera frame) → turn LEFT  (positive z)
      cmd.angular.z = (closest_y > 0.0f) ? -turn_rate_ : turn_rate_;

      const char * dir = (closest_y > 0.0f) ? "RIGHT" : "LEFT";
      RCLCPP_WARN_THROTTLE(get_logger(), *get_clock(), 500,
        "Obstacle at %.2fm (y=%.2f) — turning %s", closest_dist, closest_y, dir);
    } else {
      cmd.linear.x  = forward_speed_;
      cmd.angular.z = 0.0;
    }

    cmd_pub_->publish(cmd);
    publish_vel_marker(cmd, msg->header);
  }

  void publish_vel_marker(
    const geometry_msgs::msg::Twist & cmd,
    const std_msgs::msg::Header & header)
  {
    // Yaw: forward → 0 rad | turning left → +45° | turning right → -45°
    double yaw = 0.0;
    if (cmd.angular.z > 0.01)       yaw =  M_PI / 4.0;
    else if (cmd.angular.z < -0.01) yaw = -M_PI / 4.0;

    // Quaternion from yaw around Z — avoids tf2 dependency
    // q.w = cos(yaw/2),  q.z = sin(yaw/2),  q.x = q.y = 0
    const double half_yaw = yaw / 2.0;

    visualization_msgs::msg::Marker m;
    m.header         = header;
    m.header.frame_id = "base_link";
    m.ns             = "cmd_vel";
    m.id             = 0;
    m.type           = visualization_msgs::msg::Marker::ARROW;
    m.action         = visualization_msgs::msg::Marker::ADD;

    m.pose.position.x    = 0.0;
    m.pose.position.y    = 0.0;
    m.pose.position.z    = 0.3;
    m.pose.orientation.w = std::cos(half_yaw);
    m.pose.orientation.x = 0.0;
    m.pose.orientation.y = 0.0;
    m.pose.orientation.z = std::sin(half_yaw);

    // Arrow length scales with forward speed so a stopped robot shows a stub
    const double arrow_len = (cmd.linear.x > 0.0) ? 0.6 : 0.15;
    m.scale.x = arrow_len;  // shaft length
    m.scale.y = 0.06;       // shaft diameter
    m.scale.z = 0.10;       // head diameter

    // BLUE
    m.color.r = 0.0f;
    m.color.g = 0.4f;
    m.color.b = 1.0f;
    m.color.a = 1.0f;

    m.lifetime = rclcpp::Duration::from_seconds(0.3);

    marker_pub_->publish(m);
  }

  double safe_distance_;
  double critical_distance_;
  double forward_speed_;
  double turn_rate_;

  rclcpp::Subscription<obstacle_interfaces::msg::ObstacleArray>::SharedPtr obstacle_sub_;
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr cmd_pub_;
  rclcpp::Publisher<visualization_msgs::msg::Marker>::SharedPtr marker_pub_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<ControlNode>());
  rclcpp::shutdown();
  return 0;
}
