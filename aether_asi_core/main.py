"""Preview self-refactoring; live writes require explicit lossy-output consent."""

import argparse
from aether_asi_core.utils.logging import setup_logging
from aether_asi_core.soul.soul_module import SoulModule
from aether_asi_core.meta_optimizer.optimizer import MetaOptimizer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="write transformed source")
    parser.add_argument("--allow-lossy", action="store_true",
                        help="accept removal of comments and original formatting")
    args = parser.parse_args()
    if args.live and not args.allow_lossy:
        parser.error("--live requires --allow-lossy")
    setup_logging()
    optimizer = MetaOptimizer(SoulModule(), dry_run=not args.live,
                              allow_lossy=args.allow_lossy)
    result = optimizer.self_optimize()
    for change in result["changes"]:
        print(change["diff"])
    print(result)


if __name__ == "__main__":
    main()
