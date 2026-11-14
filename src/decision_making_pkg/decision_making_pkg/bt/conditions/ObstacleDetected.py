from ..base_bt_nodes import BTNode, Status


class ObstacleDetected(BTNode):
    """라이다가 장애물을 감지했으면 SUCCESS."""

    def __init__(self, name, shared):
        super().__init__(name)
        self.shared = shared

    def tick(self):
        lidar = self.shared.lidar_data
        if lidar is not None and lidar.data is True:
            return Status.SUCCESS
        return Status.FAILURE
