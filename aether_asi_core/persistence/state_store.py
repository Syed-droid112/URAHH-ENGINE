import json
from pathlib import Path

class StateStore:
    DEFAULT = {"objectives": [], "iteration": 0, "alignment_score": 1.0}

    def __init__(self, path: str = "data/soul_state.json"):
        self.path = Path(path)

    def load(self) -> dict:
        if not self.path.exists():
            return dict(self.DEFAULT)
        with open(self.path) as f:
            return json.load(f)

    def save(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)
