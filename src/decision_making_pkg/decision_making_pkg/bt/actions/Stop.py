from ..base_bt_nodes import BTNode, Status


class Stop(BTNode):
    """정지 명령을 계속 보낸다. 스스로 끝나지 않으므로 항상 RUNNING."""

    def __init__(self, name, shared):
        super().__init__(name)
        self.shared = shared

    def tick(self):
        self.shared.stop_vehicle()
        return Status.RUNNING
