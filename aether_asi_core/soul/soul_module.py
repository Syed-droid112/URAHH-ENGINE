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
        """Structural checks only; acceptance does not prove semantic equivalence."""
        import ast
        # 1. New source must parse
        try:
            new_tree = ast.parse(new_source)
            orig_tree = ast.parse(original_source)
            compile(new_tree, "<candidate>", "exec")
        except (SyntaxError, ValueError, TypeError):
            logger.warning("REJECTED: new source has syntax errors.")
            return False
        # 2. Must not delete more than 40% of lines
        orig_lines = len(original_source.strip().splitlines())
        new_lines = len(new_source.strip().splitlines())
        if orig_lines > 0 and new_lines < orig_lines * 0.6:
            logger.warning("REJECTED: too much code deleted (%d -> %d lines).", orig_lines, new_lines)
            return False
        # Preserve definitions in their lexical scopes, including signatures/decorators.
        def interfaces(tree):
            result = {}
            def visit(node, scope=()):
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        key = scope + ((type(child).__name__, child.name),)
                        fields = ("bases", "keywords", "decorator_list") if isinstance(child, ast.ClassDef) else ("args", "returns", "decorator_list", "type_comment", "type_params")
                        result[key] = tuple(
                            (field, ast.dump(value) if isinstance(value, ast.AST)
                             else tuple(ast.dump(v) for v in value) if isinstance(value, list)
                             else value)
                            for field in fields if (value := getattr(child, field, None)) is not None
                        )
                        visit(child, key)
                    else:
                        visit(child, scope)
            visit(tree)
            return result
        original_interfaces = interfaces(orig_tree)
        candidate_interfaces = interfaces(new_tree)
        if any(candidate_interfaces.get(key) != value for key, value in original_interfaces.items()):
            logger.warning("REJECTED: definitions or their interfaces changed.")
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

