#include <cmath>
#include <cstdint>

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <sensor_msgs/point_cloud2_iterator.hpp>
#include <visualization_msgs/msg/marker.hpp>
#include <visualization_msgs/msg/marker_array.hpp>

#include <obstacle_interfaces/msg/obstacle.hpp>
#include <obstacle_interfaces/msg/obstacle_array.hpp>

using std::placeholders::_1;

// Max sphere markers sent to RViz per frame — keeps Jetson GPU load bounded
static constexpr std::size_t MAX_VIZ_MARKERS = 300;

static constexpr float MIN_RANGE = 0.3f;  // metres — below this is sensor noise
static constexpr float MAX_RANGE = 4.0f;  // metres — beyond this we don't care

class ObstacleNode : public rclcpp::Node
{
public:
  ObstacleNode() : Node("obstacle_node")
  {
    // sample_stride: process every Nth point from the cloud.
    // D455 at 640x480 = 307k pts/frame. stride=8 → ~38k pts, plenty for control.
    declare_parameter("sample_stride", 8);
    sample_stride_ = static_cast<std::size_t>(get_parameter("sample_stride").as_int());

    pointcloud_sub_ = create_subscription<sensor_msgs::msg::PointCloud2>(
      "/camera/depth/color/points", 10,
      std::bind(&ObstacleNode::pointcloud_callback, this, _1));

    obstacle_pub_ = create_publisher<obstacle_interfaces::msg::ObstacleArray>(
      "/obstacles", 10);

    marker_pub_ = create_publisher<visualization_msgs::msg::MarkerArray>(
      "/obstacle_markers", 10);

    RCLCPP_INFO(get_logger(),
      "ObstacleNode ready — stride=%zu, range=[%.1f, %.1f]m",
      sample_stride_, MIN_RANGE, MAX_RANGE);
  }

private:
  void pointcloud_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    obstacle_interfaces::msg::ObstacleArray obstacle_array;
    obstacle_array.header = msg->header;

    // PointCloud2Iterator: stride-safe typed access — no PCL needed
    sensor_msgs::PointCloud2Iterator<float> iter_x(*msg, "x");
    sensor_msgs::PointCloud2Iterator<float> iter_y(*msg, "y");
    sensor_msgs::PointCloud2Iterator<float> iter_z(*msg, "z");

    std::size_t idx = 0;
    for (; iter_x != iter_x.end(); ++iter_x, ++iter_y, ++iter_z, ++idx) {
      if (idx % sample_stride_ != 0) {
        continue;
      }

      const float x = *iter_x;
      const float y = *iter_y;
      const float z = *iter_z;

      if (!std::isfinite(x) || !std::isfinite(y) || !std::isfinite(z)) {
        continue;
      }

      const float distance = std::sqrt(x * x + y * y + z * z);

      if (distance >= MIN_RANGE && distance <= MAX_RANGE) {
        obstacle_interfaces::msg::Obstacle obs;
        obs.x = x;
        obs.y = y;
        obs.z = z;
        obs.distance = distance;
        obstacle_array.obstacles.push_back(obs);
      }
    }

    obstacle_pub_->publish(obstacle_array);
    publish_markers(obstacle_array);
  }

  void publish_markers(const obstacle_interfaces::msg::ObstacleArray & array)
  {
    visualization_msgs::msg::MarkerArray marker_array;
    const auto & obstacles = array.obstacles;

    if (obstacles.empty()) {
      // Publish a single DELETE_ALL to clear any lingering spheres
      visualization_msgs::msg::Marker del;
      del.header = array.header;
      del.action = visualization_msgs::msg::Marker::DELETEALL;
      marker_array.markers.push_back(del);
      marker_pub_->publish(marker_array);
      return;
    }

    // Sub-sample the obstacle list so we never flood RViz with 40k+ markers
    const std::size_t n = obstacles.size();
    const std::size_t step = std::max(std::size_t{1}, n / MAX_VIZ_MARKERS);

    int32_t id = 0;
    for (std::size_t i = 0; i < n; i += step) {
      const auto & obs = obstacles[i];

      visualization_msgs::msg::Marker m;
      m.header = array.header;
      m.ns     = "obstacles";
      m.id     = id++;
      m.type   = visualization_msgs::msg::Marker::SPHERE;
      m.action = visualization_msgs::msg::Marker::ADD;

      m.pose.position.x = obs.x;
      m.pose.position.y = obs.y;
      m.pose.position.z = obs.z;
      m.pose.orientation.w = 1.0;

      m.scale.x = 0.07;
      m.scale.y = 0.07;
      m.scale.z = 0.07;

      // Color by distance: RED < 0.5m | YELLOW < 1.0m | GREEN ≥ 1.0m
      m.color.a = 0.85f;
      if (obs.distance < 0.5f) {
        m.color.r = 1.0f; m.color.g = 0.0f; m.color.b = 0.0f;  // red
      } else if (obs.distance < 1.0f) {
        m.color.r = 1.0f; m.color.g = 0.8f; m.color.b = 0.0f;  // yellow
      } else {
        m.color.r = 0.0f; m.color.g = 1.0f; m.color.b = 0.0f;  // green
      }

      // Short lifetime so stale markers auto-clear if the camera stops
      m.lifetime = rclcpp::Duration::from_seconds(0.3);

      marker_array.markers.push_back(m);
    }

    marker_pub_->publish(marker_array);
  }

  std::size_t sample_stride_;

  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr pointcloud_sub_;
  rclcpp::Publisher<obstacle_interfaces::msg::ObstacleArray>::SharedPtr obstacle_pub_;
  rclcpp::Publisher<visualization_msgs::msg::MarkerArray>::SharedPtr marker_pub_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<ObstacleNode>());
  rclcpp::shutdown();
  return 0;
}
