import tempfile, unittest
from pathlib import Path
from aether_asi_core.soul.soul_module import SoulModule
from aether_asi_core.meta_optimizer.optimizer import MetaOptimizer
from aether_asi_core.meta_optimizer.refactor import apply_all_transforms

class TestRefactor(unittest.TestCase):
    def test_removes_extra_pass(self):
        src = "def foo():\n    x = 1\n    pass\n"
        result = apply_all_transforms(src)
        self.assertNotIn("pass", result)
        self.assertIn("x = 1", result)

    def test_folds_constants(self):
        src = "x = 1 + 2\n"
        result = apply_all_transforms(src)
        self.assertIn("3", result)

    def test_preserves_valid_code(self):
        src = "def foo():\n    return 42\n"
        result = apply_all_transforms(src)
        self.assertIn("return 42", result)

class TestMetaOptimizer(unittest.TestCase):
    def _opt(self, td, dry_run=True):
        p = str(Path(td) / "s.json")
        soul = SoulModule(state_path=p)
        soul.add_objective("Test", 1)
        return MetaOptimizer(soul=soul, max_depth=3, dry_run=dry_run)

    def test_introspect_reads_files(self):
        with tempfile.TemporaryDirectory() as td:
            opt = self._opt(td)
            files = opt.introspect()
            self.assertGreater(len(files), 0)

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as td:
            # Create a test file with removable pass
            test_dir = Path(td) / "pkg"
            test_dir.mkdir()
            f = test_dir / "mod.py"
            f.write_text("def foo():\n    x = 1\n    pass\n")
            (test_dir / "__init__.py").write_text("")
            opt = self._opt(td, dry_run=True)
            opt.run_loop(target_dir=test_dir)
            # File should be unchanged
            self.assertIn("pass", f.read_text())

    def test_live_run_writes_changes(self):
        with tempfile.TemporaryDirectory() as td:
            test_dir = Path(td) / "pkg"
            test_dir.mkdir()
            f = test_dir / "mod.py"
            f.write_text("def foo():\n    x = 1\n    pass\n")
            (test_dir / "__init__.py").write_text("")
            p = str(Path(td) / "s.json")
            soul = SoulModule(state_path=p)
            soul.add_objective("Test", 1)
            opt = MetaOptimizer(soul=soul, max_depth=3, dry_run=False)
            result = opt.run_loop(target_dir=test_dir)
            self.assertGreater(result["total_files_changed"], 0)

    def test_reaches_fixed_point(self):
        with tempfile.TemporaryDirectory() as td:
            test_dir = Path(td) / "pkg"
            test_dir.mkdir()
            f = test_dir / "mod.py"
            f.write_text("def foo():\n    return 1\n")
            (test_dir / "__init__.py").write_text("")
            p = str(Path(td) / "s.json")
            soul = SoulModule(state_path=p)
            soul.add_objective("Test", 1)
            opt = MetaOptimizer(soul=soul, max_depth=10, dry_run=False)
            result = opt.run_loop(target_dir=test_dir)
            # Should converge, not run all 10 iterations
            self.assertLessEqual(result["iterations_run"], 5)

if __name__ == "__main__":
    unittest.main()
