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

from server import PAGE_PATH, input_energy, load_input_energy, load_unit, make_server, step_clock

class LoadUnitTest(unittest.TestCase):
  def test_the_unit_of_the_gui_has_the_planes_a_c_and_d_with_a_cursor_from_a_to_c_and_to_d_and_a_drain_on_each_plane(self):
    unit = load_unit()
    self.assertEqual(list(unit.planes), ["A", "C", "D"])
    self.assertEqual([(cursor.source.uid, cursor.target.uid if cursor.target is not None else None) for cursor in unit.cursors], [("A", "C"), ("A", None), ("A", "D"), ("C", None), ("D", None)])

  def test_the_unit_is_built_from_the_given_config_file(self):
    config = {"scheduler": {"tick": 1.0, "budget": 0, "moment": 10}, "random": {"seed": 1}, "memory": {"floor": 0.3, "threshold": 0.5, "orbit": [0.05, 0.1], "window": 2, "range": 0.5, "rest": 0.03, "far": 0.25, "base": 0.2, "rate": 1.0, "coexpression": 1.0, "kappa": 1.0, "amplify": 2.0}, "planes": [{"uid": "X", "peak": 1.0, "merge": 0, "relax": None, "transfers": []}, {"uid": "Y", "peak": 2.0, "merge": 0, "relax": None, "transfers": []}]}
    with tempfile.TemporaryDirectory() as folder:
      path = Path(folder) / "config.json"
      path.write_text(json.dumps(config))
      unit = load_unit(path)
    self.assertEqual(list(unit.planes), ["X", "Y"])

class InputEnergyTest(unittest.TestCase):
  def test_the_gui_config_gives_a_valid_input_energy(self):
    self.assertGreater(load_input_energy(), 0)

  def test_the_energy_comes_from_the_given_config_file(self):
    with tempfile.TemporaryDirectory() as folder:
      path = Path(folder) / "config.json"
      path.write_text(json.dumps({"input": {"energy": 0.5}}))
      self.assertEqual(load_input_energy(path), 0.5)

  def test_a_missing_section_or_energy_is_refused(self):
    for config in ({}, {"input": {}}, {"input": 3}, {"input": None}, []):
      with self.assertRaises(ValueError, msg=repr(config)) as caught:
        input_energy(config)
      self.assertIn("config.input.energy", str(caught.exception))

  def test_an_energy_that_is_not_a_number_greater_than_zero_is_refused(self):
    for energy in (0, -1, "1", None, True, [1]):
      with self.assertRaises(ValueError, msg=repr(energy)) as caught:
        input_energy({"input": {"energy": energy}})
      self.assertIn("config.input.energy", str(caught.exception))

class ServerTest(unittest.TestCase):
  ENERGY = 0.125

  def setUp(self):
    self.server = make_server(load_unit(), 0, self.ENERGY)
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

  def post(self, body, path="/api/text"):
    request = urllib.request.Request(self.base + path, data=body, headers={"Content-Type": "application/json"}, method="POST")
    return urllib.request.urlopen(request)

  def test_a_posted_text_enters_the_unit_word_by_word_and_the_new_state_comes_back(self):
    with self.post(b'{"text": "The cat, the"}') as response:
      self.assertEqual(response.status, 200)
      state = json.loads(response.read())
    energies = sorted(perception["energy"] for perception in state["planes"][0]["perceptions"])
    self.assertEqual(energies, [self.ENERGY, 2 * self.ENERGY])
    self.assertEqual(state, self.server.unit.state())

  def test_an_invalid_body_is_refused_with_a_message_and_nothing_enters_the_unit(self):
    for body in (b'{"text": ""}', b'{"text": "?!"}', b'{}', b'{"text": 3}', b'[1]', b'not json'):
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
    tick_ms = self.server.unit.scheduler.tick_us / 1000.0
    self.assertEqual(step_clock(self.server, 3 * tick_ms), 3)
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
    with self.assertRaises(urllib.error.HTTPError) as caught:
      self.post(b'{"token": "house"}', "/api/token")
    self.assertEqual(caught.exception.code, 404)

  def test_the_server_holds_the_unit_it_was_given(self):
    unit = load_unit()
    server = make_server(unit, 0, 0.5)
    self.assertIs(server.unit, unit)
    self.assertEqual(server.energy, 0.5)
    server.server_close()

if __name__ == "__main__":
  unittest.main()
