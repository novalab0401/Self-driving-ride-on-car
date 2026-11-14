from ..base_bt_nodes import BTNode, Status
from ...lib import decision_making_func_lib as DMFL


class FollowLane(BTNode):
    """경로의 기울기를 보고 조향을 정해 차선을 따라간다.

    쓸 수 있는 경로가 없으면 FAILURE 를 돌려준다 (주행하지 않음).
    """

    def __init__(self, name, shared, speed=100, steering=7):
        super().__init__(name)
        self.shared = shared

        self.speed = speed        # 예시 속도 값 (255 가 최대 속도)
        self.steering = steering  # 예시 조향 값 (7 이 최대 조향)

    def tick(self):
        path = self.shared.path_data
        if path is None or len(path) < 10:
            return Status.FAILURE

        target_slope = DMFL.calculate_slope_between_points(path[-10], path[-1])

        # 두 점의 높이가 같으면 기울기 대신 문자열 'inf' 가 오므로 직진으로 처리한다
        if isinstance(target_slope, str) or target_slope == 0:
            steering = 0
        elif target_slope > 0:
            steering = self.steering
        else:
            steering = -self.steering

        self.shared.publish_command(steering, self.speed, self.speed)
        return Status.RUNNING

    def halt(self):
        self.shared.stop_vehicle()
