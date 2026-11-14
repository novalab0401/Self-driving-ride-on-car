from ..base_bt_nodes import BTNode, Status


class DriveForward2s(BTNode):
    """테스트용 액션: 정해진 시간 동안 직진한 뒤 멈춘다."""

    def __init__(self, name, shared, duration=2.0, speed=100):
        super().__init__(name)
        self.shared = shared

        self.duration = duration  # 주행 시간 (초)
        self.speed = speed        # 좌우 바퀴 속도 (255 가 최대)

        self.start_time = None

    def tick(self):
        now = self.shared.get_clock().now().nanoseconds * 1e-9

        if self.start_time is None:
            self.start_time = now
            self.shared.get_logger().info('[BT][DriveForward2s] START')

        if now - self.start_time < self.duration:
            self.shared.publish_command(0, self.speed, self.speed)
            return Status.RUNNING

        self.shared.stop_vehicle()
        self.shared.get_logger().info('[BT][DriveForward2s] SUCCESS')
        return Status.SUCCESS

    def halt(self):
        self.shared.stop_vehicle()

    def reset(self):
        super().reset()
        self.start_time = None
