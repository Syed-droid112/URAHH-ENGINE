import logging
import sys

def setup_logging(level: int = logging.INFO):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(name)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"))
    root = logging.getLogger("aether_asi_core")
    root.setLevel(level)
    if not root.handlers:
        root.addHandler(handler)
