"""Aether-ASI-Core entry point — runs the self-refactoring loop."""

from aether_asi_core.utils.logging import setup_logging
from aether_asi_core.soul.soul_module import SoulModule
from aether_asi_core.meta_optimizer.optimizer import MetaOptimizer

def main():
    setup_logging()

    soul = SoulModule()
    if soul.objective_function() is None:
        soul.add_objective("Achieve recursive self-improvement via logic compression", priority=1)

    # First run: dry_run=True to show what WOULD change without writing
    print("=== DRY RUN ===")
    optimizer = MetaOptimizer(soul=soul, max_depth=5, dry_run=True)
    dry_result = optimizer.self_optimize()
    print(f"Dry run result: {dry_result['total_files_changed']} file(s) would change over {dry_result['iterations_run']} iteration(s)")

    # Second run: actually write changes
    print("\n=== LIVE RUN ===")
    optimizer_live = MetaOptimizer(soul=soul, max_depth=5, dry_run=False)
    live_result = optimizer_live.self_optimize()
    print(f"Live result: {live_result['total_files_changed']} file(s) changed over {live_result['iterations_run']} iteration(s)")

    for change in live_result["changes"]:
        print(f"\n--- {change['file']} ---")
        print(change["diff"])

    print(f"\nSoul iteration: {live_result['soul_iteration']}")

if __name__ == "__main__":
    main()
