import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

import support

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "gui"))

from server import PAGE_PATH, load_unit, make_server

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

class ServerTest(unittest.TestCase):
  def setUp(self):
    self.server = make_server(load_unit(), 0)
    self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    self.thread.start()
    self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

  def tearDown(self):
    self.server.shutdown()
    self.server.server_close()
    self.thread.join()

  def test_the_root_serves_the_page(self):
    with urllib.request.urlopen(self.base + "/") as response:
      self.assertEqual(response.status, 200)
      self.assertIn("text/html", response.headers["Content-Type"])
      self.assertEqual(response.read(), PAGE_PATH.read_bytes())

  def test_an_unknown_route_is_not_found(self):
    with self.assertRaises(urllib.error.HTTPError) as caught:
      urllib.request.urlopen(self.base + "/unknown")
    self.assertEqual(caught.exception.code, 404)

  def test_the_server_holds_the_unit_it_was_given(self):
    unit = load_unit()
    server = make_server(unit, 0)
    self.assertIs(server.unit, unit)
    server.server_close()

if __name__ == "__main__":
  unittest.main()
