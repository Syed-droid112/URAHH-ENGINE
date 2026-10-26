import ast
import importlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aether_asi_core.meta_optimizer.optimizer import MetaOptimizer
from aether_asi_core.meta_optimizer.refactor import apply_all_transforms
from aether_asi_core.soul.soul_module import SoulModule


class ReviewRegressions(unittest.TestCase):
    def test_zero_depth_is_noop(self):
        with tempfile.TemporaryDirectory() as td:
            soul = SoulModule(str(Path(td) / "state.json"))
            opt = MetaOptimizer(soul, max_depth=0)
            with patch.object(opt, "introspect", side_effect=AssertionError("read")):
                result = opt.run_loop()
            self.assertEqual(result["iterations_run"], 0)
            self.assertEqual(result["total_files_changed"], 0)
            self.assertEqual(result["changes"], [])

    def test_negative_depth_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                MetaOptimizer(SoulModule(str(Path(td) / "s.json")), max_depth=-1)

    def test_imports_preserved_even_when_other_code_changes(self):
        src = ('from __future__ import annotations\n'
               'from .optimizer import MetaOptimizer\n'
               'from .other import *\n'
               'import side_effect_plugin\n'
               '__all__ = ["MetaOptimizer"]\n'
               'value = 1 + 2\n')
        out = ast.parse(apply_all_transforms(src))
        before = [ast.dump(n) for n in ast.parse(src).body
                  if isinstance(n, (ast.Import, ast.ImportFrom))]
        after = [ast.dump(n) for n in out.body
                 if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertEqual(before, after)

    def test_noop_preserves_comments_and_formatting(self):
        src = "# comment\nx  = 42\n"
        self.assertEqual(apply_all_transforms(src), src)

    def test_live_lossy_write_requires_optin(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "mod.py"
            src = "# valuable comment\nx  = 1 + 2\ny = 4\n"
            path.write_text(src)
            opt = MetaOptimizer(SoulModule(str(Path(td) / "s.json")))
            self.assertFalse(opt.refactor_file(path, src))
            self.assertEqual(path.read_text(), src)
            opt.allow_lossy = True
            self.assertTrue(opt.refactor_file(path, src))
            self.assertIn("x = 3", path.read_text())

    def test_behavior_validator_vetoes_live_write(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "mod.py"
            src = "x = 1 + 2\n"
            path.write_text(src)
            opt = MetaOptimizer(SoulModule(str(Path(td) / "s.json")),
                                allow_lossy=True, validator=lambda *args: False)
            self.assertFalse(opt.refactor_file(path, src))
            self.assertEqual(path.read_text(), src)
            self.assertEqual(opt.changes_log, [])

    def test_change_log_does_not_accumulate_between_runs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "pkg"
            root.mkdir()
            (root / "mod.py").write_text("x = 1 + 2\n")
            opt = MetaOptimizer(SoulModule(str(Path(td) / "s.json")),
                                allow_lossy=True)
            first = opt.run_loop(root)
            second = opt.run_loop(root)
            self.assertEqual(len(first["changes"]), 1)
            self.assertEqual(second["changes"], [])

    def test_gate_rejects_interface_and_scope_changes(self):
        cases = [
            ("def f(x): return x", "def f(): return 1"),
            ("async def f(): pass", "def f(): pass"),
            ("class A:\n def f(self): pass\nclass B: pass",
             "class A: pass\nclass B:\n def f(self): pass"),
            ("@staticmethod\ndef f(): pass", "def f(): pass"),
            ("x = 1", "return 1"),
            ("def broken(", "x = 1"),
        ]
        with tempfile.TemporaryDirectory() as td:
            soul = SoulModule(str(Path(td) / "s.json"))
            for original, candidate in cases:
                with self.subTest(candidate=candidate):
                    self.assertFalse(soul.alignment_check(original, candidate))

    def test_invalid_transform_does_not_crash_or_write(self):
        src = "def f():\n    if False:\n        x = 1\n"
        with tempfile.TemporaryDirectory() as td:
            opt = MetaOptimizer(SoulModule(str(Path(td) / "s.json")))
            self.assertEqual(opt.optimize_source(src), src)
        compile(apply_all_transforms("def f():\n    pass\n    pass\n"), "", "exec")

    def test_cli_requires_explicit_lossy_flag(self):
        result = subprocess.run([sys.executable, "-m", "aether_asi_core.main", "--live"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("--live requires --allow-lossy", result.stderr)

    def test_declared_build_backend_is_importable(self):
        # Parse this small build-system section without requiring Python 3.11 tomllib.
        root = Path(__file__).resolve().parents[1]
        declaration = next(line for line in (root / "pyproject.toml").read_text().splitlines()
                           if line.startswith("build-backend"))
        backend = ast.literal_eval(declaration.split("=", 1)[1].strip())
        self.assertTrue(callable(importlib.import_module(backend).build_wheel))
