import os
import threading
import time

import rclpy
from rclpy.executors import MultiThreadedExecutor
from rclpy.signals import SignalHandlerOptions
from ament_index_python.packages import get_package_share_directory

from .bt.shared_node import ROS2NodeShared
from .bt.bt_constructor import build_behavior_tree
from .bt.base_bt_nodes import Status, tick_node

#---------------Variable Setting---------------
# 실행할 BT XML 파일 이름 (trees 폴더 안). 실행할 때 바꾸려면:
#   ros2 run decision_making_pkg bt_planner_node --ros-args -p tree:=test_drive_bt.xml
TREE_FILE = "main_bt.xml"

# BT 를 tick 하는 주기 (초). driving.ino 는 0.5초 동안 명령이 없으면 후륜을 멈춘다
TICK_PERIOD = 0.1
#----------------------------------------------


def main(args=None):
    # Ctrl+C 를 rclpy 가 먼저 처리하면 종료 직전에 정지 명령을 보낼 수 없으므로 직접 처리한다
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)

    # 1. Shared ROS2 Node 생성
    shared = ROS2NodeShared(node_name='bt_planner_node')

    # 2. BT 생성
    tree_file = shared.declare_parameter('tree', TREE_FILE).value
    xml_path = os.path.join(get_package_share_directory('decision_making_pkg'), 'trees', tree_file)
    shared.get_logger().info(f"[MAIN] Loading BT XML: {xml_path}")
    root = build_behavior_tree(shared, xml_path)

    # 3. 구독 콜백은 별도 스레드에서 처리
    executor = MultiThreadedExecutor()
    executor.add_node(shared)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()

    # 4. Tick loop
    shared.get_logger().info("[MAIN] Behavior Tree started")
    try:
        while rclpy.ok():
            status = tick_node(root)

            if status == Status.SUCCESS:
                shared.get_logger().info("[BT] Mission completed")
                break

            if status == Status.FAILURE:
                shared.get_logger().warn("[BT] Mission failed")
                break

            time.sleep(TICK_PERIOD)

    except KeyboardInterrupt:
        shared.get_logger().warn("[MAIN] KeyboardInterrupt")

    finally:
        # 어떤 이유로 끝나든 달리던 액션을 중단시키고 정지 명령을 보낸다
        root.reset()
        shared.stop_vehicle()
        time.sleep(0.2)  # 정지 명령이 실제로 나갈 시간

        # 콜백 스레드가 완전히 끝난 뒤에 노드를 없앤다
        # (돌고 있는 중에 없애면 종료할 때 "terminate called" 로 비정상 종료됨)
        executor.shutdown()
        spin_thread.join(timeout=2.0)
        shared.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
