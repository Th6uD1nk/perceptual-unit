import copy
import json
import unittest

import support
from plane import Plane
from unit import Unit

def entry(uid, peak=1.0):
  return {"uid": uid, "peak": peak}

def make_config(planes, tick=4.0):
  return {"scheduler": {"tick": tick, "budget": 0}, "planes": planes}

CONFIG = make_config([entry("A", 4.0), entry("C", 2.0), entry("D", 1.0)])

class InstantiationTest(unittest.TestCase):
  def test_the_unit_creates_one_plane_per_entry(self):
    unit = Unit(CONFIG)
    self.assertEqual(len(unit.planes), 3)
    for plane in unit.planes.values():
      self.assertIsInstance(plane, Plane)

  def test_the_planes_are_found_by_uid(self):
    self.assertEqual(Unit(CONFIG).planes["C"].uid, "C")

  def test_the_order_of_the_config_is_kept(self):
    unit = Unit(make_config([entry("D"), entry("A")]))
    self.assertEqual(list(unit.planes), ["D", "A"])

  def test_each_plane_receives_its_own_peak(self):
    unit = Unit(CONFIG)
    self.assertEqual([plane.peak for plane in unit.planes.values()], [4.0, 2.0, 1.0])

  def test_two_units_do_not_share_their_planes(self):
    first = Unit(CONFIG)
    second = Unit(CONFIG)
    self.assertIsNot(first.planes["A"], second.planes["A"])

  def test_the_unit_keeps_its_own_copy_of_the_config(self):
    config = copy.deepcopy(CONFIG)
    unit = Unit(config)
    config["planes"].append({"uid": "Z"})
    config["planes"][0]["uid"] = "B"
    self.assertEqual(list(unit.planes), ["A", "C", "D"])
    self.assertEqual(unit.config, CONFIG)

class SchedulerTest(unittest.TestCase):
  def test_an_update_advances_the_ticks_by_the_tick_duration_of_the_config(self):
    unit = Unit(make_config([entry("A")], tick=2.0))
    self.assertEqual(unit.update(10.0), 5)
    self.assertEqual(unit.ticks, 5)

  def test_two_units_do_not_share_their_scheduler(self):
    first = Unit(CONFIG)
    second = Unit(CONFIG)
    first.update(8.0)
    self.assertEqual(second.ticks, 0)

class StateTest(unittest.TestCase):
  def test_the_state_gives_the_ticks_and_the_planes_in_the_order_of_the_config(self):
    unit = Unit(CONFIG)
    unit.update(8.0)
    state = unit.state()
    self.assertEqual(state["ticks"], 2)
    self.assertEqual([plane["uid"] for plane in state["planes"]], ["A", "C", "D"])

  def test_the_state_holds_the_perceptions_of_each_plane(self):
    unit = Unit(CONFIG)
    unit.planes["A"].receive("house", 0.25, 0.75, 1.0)
    unit.planes["D"].receive("cat", 0.5, 0.5, 0.5)
    planes = {plane["uid"]: plane for plane in unit.state()["planes"]}
    self.assertEqual([entry["hash"] for entry in planes["A"]["perceptions"]], ["house"])
    self.assertEqual(planes["C"]["perceptions"], [])
    self.assertEqual([entry["hash"] for entry in planes["D"]["perceptions"]], ["cat"])

  def test_the_state_can_be_written_as_json(self):
    unit = Unit(CONFIG)
    unit.planes["A"].receive("house", 0.25, 0.75, 1.0)
    self.assertEqual(json.loads(json.dumps(unit.state())), unit.state())

  def test_reading_the_state_changes_nothing_and_gives_the_same_result(self):
    unit = Unit(CONFIG)
    unit.planes["A"].receive("house", 0.25, 0.75, 1.0)
    self.assertEqual(unit.state(), unit.state())

  def test_changing_the_state_does_not_change_the_unit(self):
    unit = Unit(CONFIG)
    unit.planes["A"].receive("house", 0.25, 0.75, 1.0)
    unit.state()["planes"][0]["perceptions"].clear()
    unit.state()["planes"][0]["peak"] = 99.0
    self.assertEqual(len(unit.planes["A"].perceptions), 1)
    self.assertEqual(unit.planes["A"].peak, 4.0)

class RejectionTest(unittest.TestCase):
  def rejected(self, config):
    with self.assertRaises(ValueError) as caught:
      Unit(config)
    return str(caught.exception)

  def test_a_config_must_be_an_object(self):
    self.assertIn("config", self.rejected([]))

  def test_the_planes_are_required(self):
    self.assertIn("config.planes", self.rejected({}))

  def test_the_planes_must_be_a_non_empty_list(self):
    self.assertIn("config.planes", self.rejected({"planes": []}))
    self.assertIn("config.planes", self.rejected({"planes": {"uid": "A"}}))

  def test_a_config_without_a_scheduler_is_refused(self):
    self.assertIn("config.scheduler", self.rejected({"planes": [entry("A")]}))

  def test_a_plane_must_be_an_object(self):
    self.assertIn("config.planes[1]", self.rejected({"planes": [entry("A"), "C"]}))

  def test_a_plane_needs_a_uid(self):
    self.assertIn("config.planes[0].uid", self.rejected({"planes": [{}]}))

  def test_a_uid_must_be_a_non_empty_string(self):
    for uid in ("", 3, None, ["A"]):
      self.assertIn("config.planes[0].uid", self.rejected({"planes": [entry(uid)]}), repr(uid))

  def test_a_plane_needs_a_peak(self):
    self.assertIn("config.planes[0].peak", self.rejected({"planes": [{"uid": "A"}]}))

  def test_a_peak_must_be_a_number_greater_than_zero(self):
    for peak in (0, -1, "1", None, True, [1]):
      self.assertIn("config.planes[0].peak", self.rejected({"planes": [entry("A", peak)]}), repr(peak))

  def test_a_uid_cannot_be_used_twice(self):
    message = self.rejected({"planes": [entry("A"), entry("C"), entry("A")]})
    self.assertIn("config.planes[2].uid", message)
    self.assertIn("already used", message)

if __name__ == "__main__":
  unittest.main()
