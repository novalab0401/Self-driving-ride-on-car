from enum import Enum


# =====================================================
# BT Status
# =====================================================

class Status(Enum):
    SUCCESS = 1
    FAILURE = 2
    RUNNING = 3


# =====================================================
# Base BT Node
# =====================================================

class BTNode:
    """모든 BT 노드의 부모.

    tick()  : 한 번 실행하고 Status 를 돌려준다. 노드마다 구현한다.
    halt()  : RUNNING 이던 노드가 다른 가지에 밀려 중단될 때 불린다.
              차를 움직이는 액션은 여기서 정지 명령을 보내야 한다.
    reset() : 다음 실행을 위해 상태를 지운다. 내부 상태가 있는 노드는
              super().reset() 을 부른 뒤 자기 상태를 지운다.
    """

    def __init__(self, name):
        self.name = name
        self.status = None

    def tick(self):
        raise NotImplementedError

    def halt(self):
        pass

    def reset(self):
        if self.status == Status.RUNNING:
            self.halt()
        self.status = None


def tick_node(node):
    """노드를 tick 하고 결과를 node.status 에 남긴다.

    부모 노드는 이 기록을 보고 '달리던 자식' 만 골라 halt 한다.
    """
    node.status = node.tick()
    return node.status


# =====================================================
# Control Nodes
# =====================================================

class ControlNode(BTNode):
    def __init__(self, name, children):
        super().__init__(name)
        self.children = children

    def halt(self):
        self._reset_children()

    def _reset_children(self, start=0):
        for child in self.children[start:]:
            child.reset()


class Sequence(ControlNode):
    """자식을 순서대로 실행한다. 하나라도 실패하면 FAILURE.

    RUNNING 인 자식이 있으면 다음 tick 에 그 자식부터 이어서 실행한다.
    """

    def __init__(self, name, children):
        super().__init__(name, children)
        self.current_index = 0

    def tick(self):
        while self.current_index < len(self.children):
            status = tick_node(self.children[self.current_index])

            if status == Status.RUNNING:
                return Status.RUNNING

            if status == Status.FAILURE:
                self._finish()
                return Status.FAILURE

            self.current_index += 1

        self._finish()
        return Status.SUCCESS

    def halt(self):
        self._finish()

    def _finish(self):
        self._reset_children()
        self.current_index = 0


class ReactiveSequence(ControlNode):
    """매 tick 마다 첫 자식부터 다시 확인하는 Sequence.

    앞의 조건이 깨지면 뒤에서 달리던 액션을 중단시킨다.
    """

    def tick(self):
        for i, child in enumerate(self.children):
            status = tick_node(child)

            if status == Status.RUNNING:
                self._reset_children(start=i + 1)
                return Status.RUNNING

            if status == Status.FAILURE:
                self._reset_children()
                return Status.FAILURE

        self._reset_children()
        return Status.SUCCESS


class Fallback(ControlNode):
    """자식을 순서대로 시도한다. 하나라도 성공하면 SUCCESS.

    RUNNING 인 자식이 있으면 다음 tick 에 그 자식부터 이어서 실행한다.
    """

    def __init__(self, name, children):
        super().__init__(name, children)
        self.current_index = 0

    def tick(self):
        while self.current_index < len(self.children):
            status = tick_node(self.children[self.current_index])

            if status == Status.RUNNING:
                return Status.RUNNING

            if status == Status.SUCCESS:
                self._finish()
                return Status.SUCCESS

            self.current_index += 1

        self._finish()
        return Status.FAILURE

    def halt(self):
        self._finish()

    def _finish(self):
        self._reset_children()
        self.current_index = 0


class ReactiveFallback(ControlNode):
    """매 tick 마다 첫 자식부터 다시 시도하는 Fallback.

    앞(우선순위가 높은) 자식이 실행되기 시작하면 뒤에서 달리던 액션을 중단시킨다.
    """

    def tick(self):
        for i, child in enumerate(self.children):
            status = tick_node(child)

            if status == Status.RUNNING:
                self._reset_children(start=i + 1)
                return Status.RUNNING

            if status == Status.SUCCESS:
                self._reset_children()
                return Status.SUCCESS

        self._reset_children()
        return Status.FAILURE


class Parallel(ControlNode):
    """모든 자식을 함께 실행한다.

    success_count 개가 성공하면 SUCCESS, failure_count 개가 실패하면 FAILURE.
    -1 은 '자식 전부' 를 뜻한다 (Groot2 / BehaviorTree.CPP 와 같은 규칙).
    이미 끝난 자식은 Parallel 이 끝날 때까지 다시 실행하지 않는다.
    """

    def __init__(self, name, children, success_count=-1, failure_count=1):
        super().__init__(name, children)
        self.success_count = success_count
        self.failure_count = failure_count

    def tick(self):
        for child in self.children:
            if child.status in (None, Status.RUNNING):
                tick_node(child)

        successes = sum(c.status == Status.SUCCESS for c in self.children)
        failures = sum(c.status == Status.FAILURE for c in self.children)

        if successes >= self._threshold(self.success_count):
            self._reset_children()
            return Status.SUCCESS

        # 실패 기준을 넘었거나, 전부 끝났는데 성공 기준에 못 미친 경우
        if (failures >= self._threshold(self.failure_count)
                or successes + failures == len(self.children)):
            self._reset_children()
            return Status.FAILURE

        return Status.RUNNING

    def _threshold(self, count):
        return len(self.children) + count + 1 if count < 0 else count
