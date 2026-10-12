import json
import sys
import tempfile
import unittest
from pathlib import Path

import support

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "gui"))

from server import load_unit

class LoadUnitTest(unittest.TestCase):
  def test_the_unit_of_the_gui_has_one_plane_with_its_peak(self):
    unit = load_unit()
    self.assertEqual(list(unit.planes), ["A"])
    self.assertEqual(unit.planes["A"].peak, 0.25)

  def test_the_unit_is_built_from_the_given_config_file(self):
    config = {"scheduler": {"tick": 1.0, "budget": 0}, "planes": [{"uid": "X", "peak": 1.0}, {"uid": "Y", "peak": 2.0}]}
    with tempfile.TemporaryDirectory() as folder:
      path = Path(folder) / "config.json"
      path.write_text(json.dumps(config))
      unit = load_unit(path)
    self.assertEqual(list(unit.planes), ["X", "Y"])

if __name__ == "__main__":
  unittest.main()
