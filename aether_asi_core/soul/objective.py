from dataclasses import dataclass, field
from datetime import datetime, timezone
import heapq

@dataclass(order=True)
class Objective:
    priority: int
    description: str = field(compare=False)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), compare=False)
    status: str = field(default="active", compare=False)

class ObjectiveQueue:
    def __init__(self):
        self._heap: list[Objective] = []

    def push(self, obj: Objective):
        heapq.heappush(self._heap, obj)

    def pop(self) -> Objective:
        return heapq.heappop(self._heap)

    def peek(self) -> Objective | None:
        return self._heap[0] if self._heap else None

    def to_list(self) -> list[dict]:
        return [{"description": o.description, "priority": o.priority,
                 "created_at": o.created_at, "status": o.status}
                for o in sorted(self._heap)]

    def __len__(self):
        return len(self._heap)
