"""SoulModule — persistent high-level objective function with alignment gating."""

import logging
from pathlib import Path
from aether_asi_core.persistence.state_store import StateStore
from aether_asi_core.soul.objective import Objective, ObjectiveQueue

logger = logging.getLogger(__name__)

class SoulModule:
    def __init__(self, state_path: str = "data/soul_state.json"):
        self.store = StateStore(state_path)
        self.queue = ObjectiveQueue()
        self.iteration = 0
        self.alignment_score = 1.0
        self._load()

    def _load(self):
        data = self.store.load()
        self.iteration = data.get("iteration", 0)
        self.alignment_score = data.get("alignment_score", 1.0)
        for o in data.get("objectives", []):
            self.queue.push(Objective(
                priority=o["priority"], description=o["description"],
                created_at=o.get("created_at", ""), status=o.get("status", "active")))

    def objective_function(self) -> Objective | None:
        return self.queue.peek()

    def add_objective(self, description: str, priority: int):
        self.queue.push(Objective(priority=priority, description=description))

    def alignment_check(self, original_source: str, new_source: str) -> bool:
        """Real alignment check: reject changes that delete too much code,
        introduce syntax errors, or reduce functionality."""
        import ast
        # 1. New source must parse
        try:
            new_tree = ast.parse(new_source)
        except SyntaxError:
            logger.warning("REJECTED: new source has syntax errors.")
            return False
        # 2. Must not delete more than 40% of lines
        orig_lines = len(original_source.strip().splitlines())
        new_lines = len(new_source.strip().splitlines())
        if orig_lines > 0 and new_lines < orig_lines * 0.6:
            logger.warning("REJECTED: too much code deleted (%d -> %d lines).", orig_lines, new_lines)
            return False
        # 3. Must preserve all function/class definitions
        orig_tree = ast.parse(original_source)
        orig_names = {n.name for n in ast.walk(orig_tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
        new_names = {n.name for n in ast.walk(new_tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
        missing = orig_names - new_names
        if missing:
            logger.warning("REJECTED: would delete definitions: %s", missing)
            return False
        return True

    def persist_state(self):
        self.store.save({
            "objectives": self.queue.to_list(),
            "iteration": self.iteration,
            "alignment_score": self.alignment_score,
        })

    def tick(self):
        self.iteration += 1
        self.persist_state()
        logger.info("Soul tick -> iteration %d", self.iteration)
