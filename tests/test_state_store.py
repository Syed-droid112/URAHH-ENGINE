import json, tempfile, unittest
from pathlib import Path
from aether_asi_core.persistence.state_store import StateStore

class TestStateStore(unittest.TestCase):
    def test_load_missing(self):
        s = StateStore("/tmp/_aether_nonexistent.json")
        self.assertEqual(s.load()["iteration"], 0)

    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            s = StateStore(str(Path(td) / "s.json"))
            s.save({"iteration": 7, "objectives": [], "alignment_score": 1.0})
            self.assertEqual(s.load()["iteration"], 7)

if __name__ == "__main__":
    unittest.main()
