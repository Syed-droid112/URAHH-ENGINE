"""MetaOptimizer — reads, transforms, and writes back its own source files."""

import ast
import logging
import difflib
from pathlib import Path

from aether_asi_core.soul.soul_module import SoulModule
from aether_asi_core.meta_optimizer.code_graph import CodeGraph
from aether_asi_core.meta_optimizer.refactor import apply_all_transforms

logger = logging.getLogger(__name__)


class MetaOptimizer:
    def __init__(self, soul: SoulModule, max_depth: int = 5, dry_run: bool = False):
        self.soul = soul
        self.max_depth = max_depth
        self.dry_run = dry_run  # if True, don't write files, just report
        self.changes_log: list[dict] = []

    def introspect(self, target_dir: Path | None = None) -> dict[Path, str]:
        """Read all .py files under the target directory (default: own package)."""
        if target_dir is None:
            target_dir = Path(__file__).resolve().parent.parent  # aether_asi_core/
        files: dict[Path, str] = {}
        for py_file in sorted(target_dir.rglob("*.py")):
            try:
                source = py_file.read_text(encoding="utf-8")
                ast.parse(source)  # validate it parses
                files[py_file] = source
                logger.info("Read: %s (%d lines)", py_file.name, len(source.splitlines()))
            except (SyntaxError, UnicodeDecodeError) as e:
                logger.warning("Skip %s: %s", py_file, e)
        return files

    def optimize_source(self, source: str) -> str:
        """Apply all AST transforms to a source string."""
        return apply_all_transforms(source)

    def diff(self, original: str, new: str, filename: str = "") -> str:
        """Generate a unified diff between original and new source."""
        return "\n".join(difflib.unified_diff(
            original.splitlines(), new.splitlines(),
            fromfile=f"a/{filename}", tofile=f"b/{filename}", lineterm=""))

    def refactor_file(self, path: Path, source: str) -> bool:
        """Refactor a single file: transform, alignment-check, write back.
        Returns True if the file was changed."""
        new_source = self.optimize_source(source)
        if new_source.strip() == source.strip():
            logger.info("No changes for %s", path.name)
            return False

        d = self.diff(source, new_source, path.name)
        logger.info("Proposed diff for %s:\n%s", path.name, d)

        if not self.soul.alignment_check(source, new_source):
            logger.warning("Alignment gate REJECTED changes to %s", path.name)
            return False

        self.changes_log.append({
            "file": str(path),
            "diff": d,
            "original_lines": len(source.splitlines()),
            "new_lines": len(new_source.splitlines()),
        })

        if not self.dry_run:
            path.write_text(new_source + "\n", encoding="utf-8")
            logger.info("WROTE changes to %s", path)
        else:
            logger.info("DRY RUN — would write changes to %s", path)

        return True

    def run_loop(self, target_dir: Path | None = None) -> dict:
        """The main self-refactoring loop. Runs up to max_depth iterations.
        Each iteration: read all files -> transform -> alignment check -> write back.
        Stops when no more changes are produced (fixed point)."""
        logger.info("=== SELF-REFACTORING LOOP START (max_depth=%d, dry_run=%s) ===",
                     self.max_depth, self.dry_run)
        total_changes = 0

        for depth in range(self.max_depth):
            logger.info("--- Iteration %d/%d ---", depth + 1, self.max_depth)
            files = self.introspect(target_dir)
            changed_this_round = 0

            for path, source in files.items():
                if self.refactor_file(path, source):
                    changed_this_round += 1

            total_changes += changed_this_round
            logger.info("Iteration %d: %d file(s) changed.", depth + 1, changed_this_round)

            if changed_this_round == 0:
                logger.info("Fixed point reached at iteration %d. No more changes.", depth + 1)
                break

        self.soul.tick()
        summary = {
            "iterations_run": depth + 1,
            "total_files_changed": total_changes,
            "changes": self.changes_log,
            "soul_iteration": self.soul.iteration,
        }
        logger.info("=== SELF-REFACTORING LOOP COMPLETE === %s", summary)
        return summary

    def self_optimize(self) -> dict:
        """Convenience: run the loop on the optimizer's own package."""
        own_dir = Path(__file__).resolve().parent.parent  # aether_asi_core/
        return self.run_loop(target_dir=own_dir)
