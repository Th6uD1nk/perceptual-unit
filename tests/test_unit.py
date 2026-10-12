import copy
import unittest

from perceptual_unit import Plane, Unit

CONFIG = {"planes": [{"uid": "A"}, {"uid": "C"}, {"uid": "D"}]}

class InstantiationTest(unittest.TestCase):
  def test_the_unit_creates_one_plane_per_entry(self):
    unit = Unit(CONFIG)
    self.assertEqual(len(unit.planes), 3)
    for plane in unit.planes.values():
      self.assertIsInstance(plane, Plane)

  def test_the_planes_are_found_by_uid(self):
    unit = Unit(CONFIG)
    self.assertEqual([plane.uid for plane in unit.planes.values()], ["A", "C", "D"])
    self.assertEqual(unit.planes["C"].uid, "C")

  def test_the_order_of_the_config_is_kept(self):
    unit = Unit({"planes": [{"uid": "D"}, {"uid": "A"}]})
    self.assertEqual(list(unit.planes), ["D", "A"])

  def test_a_single_plane_is_enough(self):
    self.assertEqual(list(Unit({"planes": [{"uid": "A"}]}).planes), ["A"])

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

  def test_a_plane_must_be_an_object(self):
    self.assertIn("config.planes[1]", self.rejected({"planes": [{"uid": "A"}, "C"]}))

  def test_a_plane_needs_a_uid(self):
    self.assertIn("config.planes[0].uid", self.rejected({"planes": [{}]}))

  def test_a_uid_must_be_a_non_empty_string(self):
    for uid in ("", 3, None, ["A"]):
      self.assertIn("config.planes[0].uid", self.rejected({"planes": [{"uid": uid}]}), repr(uid))

  def test_a_uid_cannot_be_used_twice(self):
    message = self.rejected({"planes": [{"uid": "A"}, {"uid": "C"}, {"uid": "A"}]})
    self.assertIn("config.planes[2].uid", message)
    self.assertIn("already used", message)

if __name__ == "__main__":
  unittest.main()
