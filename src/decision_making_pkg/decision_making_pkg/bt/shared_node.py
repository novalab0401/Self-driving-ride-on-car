from rclpy.node import Node
from rclpy.qos import QoSProfile
from rclpy.qos import QoSHistoryPolicy
from rclpy.qos import QoSDurabilityPolicy
from rclpy.qos import QoSReliabilityPolicy

from std_msgs.msg import String, Bool
from interfaces_pkg.msg import PathPlanningResult, DetectionArray, MotionCommand

#---------------Variable Setting---------------
# motion_planner_node 와 같은 토픽을 쓴다 (두 노드를 동시에 실행하면 안 됨)
SUB_DETECTION_TOPIC_NAME = "detections"
SUB_PATH_TOPIC_NAME = "path_planning_result"
SUB_TRAFFIC_LIGHT_TOPIC_NAME = "yolov8_traffic_light_info"
SUB_LIDAR_OBSTACLE_TOPIC_NAME = "lidar_obstacle_info"
PUB_TOPIC_NAME = "topic_control_signal"
#----------------------------------------------


class ROS2NodeShared(Node):
    """모든 BT 노드가 함께 쓰는 ROS2 노드.

    센서 처리 결과를 구독해서 최신 값을 들고 있고, 모션 명령을 발행한다.
    """

    def __init__(self, node_name='bt_planner_node'):
        super().__init__(node_name)

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=1
        )

        # 최신 수신 데이터 (아직 한 번도 못 받았으면 None)
        self.detection_data = None
        self.path_data = None
        self.traffic_light_data = None
        self.lidar_data = None

        self.create_subscription(DetectionArray, SUB_DETECTION_TOPIC_NAME, self._detection_cb, qos_profile)
        self.create_subscription(PathPlanningResult, SUB_PATH_TOPIC_NAME, self._path_cb, qos_profile)
        self.create_subscription(String, SUB_TRAFFIC_LIGHT_TOPIC_NAME, self._traffic_light_cb, qos_profile)
        self.create_subscription(Bool, SUB_LIDAR_OBSTACLE_TOPIC_NAME, self._lidar_cb, qos_profile)

        self.publisher = self.create_publisher(MotionCommand, PUB_TOPIC_NAME, qos_profile)

    def _detection_cb(self, msg: DetectionArray):
        self.detection_data = msg

    def _path_cb(self, msg: PathPlanningResult):
        self.path_data = list(zip(msg.x_points, msg.y_points))

    def _traffic_light_cb(self, msg: String):
        self.traffic_light_data = msg

    def _lidar_cb(self, msg: Bool):
        self.lidar_data = msg

    def publish_command(self, steering: int, left_speed: int, right_speed: int):
        msg = MotionCommand()
        msg.steering = int(steering)
        msg.left_speed = int(left_speed)
        msg.right_speed = int(right_speed)
        self.publisher.publish(msg)

    def stop_vehicle(self):
        self.publish_command(0, 0, 0)
