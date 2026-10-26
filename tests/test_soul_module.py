import ast, tempfile, unittest
from pathlib import Path
from aether_asi_core.soul.soul_module import SoulModule

class TestSoulModule(unittest.TestCase):
    def _soul(self, td):
        return SoulModule(state_path=str(Path(td) / "s.json"))

    def test_add_and_peek(self):
        with tempfile.TemporaryDirectory() as td:
            s = self._soul(td)
            s.add_objective("X", 1)
            self.assertEqual(s.objective_function().description, "X")

    def test_persist_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            p = str(Path(td) / "s.json")
            s = SoulModule(state_path=p)
            s.add_objective("Y", 2)
            s.tick()
            s2 = SoulModule(state_path=p)
            self.assertEqual(s2.iteration, 1)
            self.assertEqual(s2.objective_function().description, "Y")

    def test_alignment_rejects_syntax_error(self):
        with tempfile.TemporaryDirectory() as td:
            s = self._soul(td)
            self.assertFalse(s.alignment_check("x = 1", "def (broken"))

    def test_alignment_rejects_deleted_functions(self):
        with tempfile.TemporaryDirectory() as td:
            s = self._soul(td)
            self.assertFalse(s.alignment_check("def foo(): pass", "x = 1"))

    def test_alignment_accepts_valid_change(self):
        with tempfile.TemporaryDirectory() as td:
            s = self._soul(td)
            self.assertTrue(s.alignment_check("def foo(): pass", "def foo():\n    return 1"))

if __name__ == "__main__":
    unittest.main()
