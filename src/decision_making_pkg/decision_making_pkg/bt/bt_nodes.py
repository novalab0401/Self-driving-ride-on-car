"""BT XML 에서 쓸 수 있는 노드 목록.

노드를 추가하려면:
  1. actions/ 또는 conditions/ 에 노드 클래스를 만든다.
  2. 이 파일에서 import 하고 아래 BTNodeList 에 이름을 넣는다.
  3. trees/ 의 XML 을 Groot2 로 수정한다.
"""
from .base_bt_nodes import (
    Sequence,
    Fallback,
    ReactiveSequence,
    ReactiveFallback,
    Parallel,
)

# ===============================
# Action Nodes
# ===============================
from .actions.DriveForward2s import DriveForward2s
from .actions.FollowLane import FollowLane
from .actions.Stop import Stop

# ===============================
# Condition Nodes
# ===============================
from .conditions.ObstacleDetected import ObstacleDetected
from .conditions.RedLightAhead import RedLightAhead


class BTNodeList:
    CONTROL_NODES = [
        "Sequence",
        "ReactiveSequence",
        "Fallback",
        "ReactiveFallback",
        "Parallel",
    ]

    ACTION_NODES = [
        "DriveForward2s",
        "FollowLane",
        "Stop",
    ]

    CONDITION_NODES = [
        "ObstacleDetected",
        "RedLightAhead",
    ]

    DECORATOR_NODES = []
