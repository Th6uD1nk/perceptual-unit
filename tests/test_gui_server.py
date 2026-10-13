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

from server import PAGE_PATH, TOKEN_ENERGY, load_unit, make_server, step_clock

class LoadUnitTest(unittest.TestCase):
  def test_the_unit_of_the_gui_has_one_plane_with_its_peak(self):
    unit = load_unit()
    self.assertEqual(list(unit.planes), ["A"])
    self.assertEqual(unit.planes["A"].peak, 0.25)

  def test_the_unit_is_built_from_the_given_config_file(self):
    config = {"scheduler": {"tick": 1.0, "budget": 0}, "random": {"seed": 1}, "planes": [{"uid": "X", "peak": 1.0, "transfers": []}, {"uid": "Y", "peak": 2.0, "transfers": []}]}
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

  def test_the_state_route_serves_the_state_of_the_unit_as_json(self):
    self.server.unit.planes["A"].receive("house", 0.25, 0.75, 0.125)
    with urllib.request.urlopen(self.base + "/api/state") as response:
      self.assertEqual(response.status, 200)
      self.assertIn("application/json", response.headers["Content-Type"])
      self.assertEqual(json.loads(response.read()), self.server.unit.state())

  def post(self, body):
    request = urllib.request.Request(self.base + "/api/token", data=body, headers={"Content-Type": "application/json"}, method="POST")
    return urllib.request.urlopen(request)

  def test_a_posted_token_enters_the_unit_and_the_new_state_comes_back(self):
    with self.post(b'{"token": "house"}') as response:
      self.assertEqual(response.status, 200)
      state = json.loads(response.read())
    perceptions = state["planes"][0]["perceptions"]
    self.assertEqual(len(perceptions), 1)
    self.assertEqual(perceptions[0]["energy"], TOKEN_ENERGY)
    self.assertEqual(state, self.server.unit.state())

  def test_an_invalid_body_is_refused_with_a_message_and_nothing_enters_the_unit(self):
    for body in (b'{"token": ""}', b'{}', b'{"token": 3}', b'[1]', b'not json'):
      with self.assertRaises(urllib.error.HTTPError, msg=body) as caught:
        self.post(body)
      self.assertEqual(caught.exception.code, 400)
      self.assertIn("error", json.loads(caught.exception.read()))
    self.assertEqual(self.server.unit.planes["A"].perceptions, {})

  def test_a_request_waits_while_the_lock_of_the_unit_is_held(self):
    statuses = []
    thread = threading.Thread(target=lambda: statuses.append(urllib.request.urlopen(self.base + "/api/state").status))
    self.server.lock.acquire()
    thread.start()
    thread.join(0.2)
    self.assertEqual(statuses, [])
    self.server.lock.release()
    thread.join(2)
    self.assertEqual(statuses, [200])

  def test_stepping_the_clock_advances_the_unit_and_the_state_shows_it(self):
    self.assertEqual(step_clock(self.server, 12.0), 3)
    self.assertEqual(self.server.unit.ticks, 3)
    with urllib.request.urlopen(self.base + "/api/state") as response:
      self.assertEqual(json.loads(response.read())["ticks"], 3)

  def test_a_refused_step_releases_the_lock(self):
    with self.assertRaises(ValueError):
      step_clock(self.server, -1.0)
    self.assertTrue(self.server.lock.acquire(blocking=False))
    self.server.lock.release()

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
