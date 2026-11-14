from ..base_bt_nodes import BTNode, Status


class RedLightAhead(BTNode):
    """빨간 신호등이 정지해야 할 위치에 보이면 SUCCESS."""

    def __init__(self, name, shared, y_max_threshold=150):
        super().__init__(name)
        self.shared = shared

        # 신호등 bbox 의 아래쪽 y 좌표가 이 값보다 작을 때 정지한다
        self.y_max_threshold = y_max_threshold

    def tick(self):
        traffic_light = self.shared.traffic_light_data
        detections = self.shared.detection_data

        if traffic_light is None or traffic_light.data != 'Red' or detections is None:
            return Status.FAILURE

        for detection in detections.detections:
            if detection.class_name == 'traffic_light':
                y_max = int(detection.bbox.center.position.y + detection.bbox.size.y / 2)
                if y_max < self.y_max_threshold:
                    return Status.SUCCESS

        return Status.FAILURE
