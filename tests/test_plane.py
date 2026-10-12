import unittest

import support
from plane import Plane

class PlaneTest(unittest.TestCase):
  def test_a_new_plane_holds_no_perception(self):
    self.assertEqual(Plane({"uid": "A"}).perceptions, {})

  def test_two_planes_do_not_share_their_perceptions(self):
    first = Plane({"uid": "A"})
    second = Plane({"uid": "C"})
    first.perceptions["key"] = "value"
    self.assertEqual(second.perceptions, {})

class AddTest(unittest.TestCase):
  def setUp(self):
    self.plane = Plane({"uid": "A"})

  def test_an_added_perception_is_stored_under_its_own_key(self):
    perception = self.plane.add("maison", 0.25, 0.75)
    self.assertEqual(perception.key, ("maison", 0.25, 0.75))
    self.assertIs(self.plane.perceptions[perception.key], perception)

  def test_an_added_perception_has_no_energy(self):
    self.assertEqual(self.plane.add("maison", 0.25, 0.75).energy, 0.0)

  def test_two_hashes_give_two_perceptions(self):
    self.plane.add("maison", 0.25, 0.75)
    self.plane.add("chat", 0.25, 0.75)
    self.assertEqual(len(self.plane.perceptions), 2)

  def test_two_positions_of_one_hash_give_two_perceptions(self):
    self.plane.add("maison", 0.25, 0.75)
    self.plane.add("maison", 0.5, 0.75)
    self.assertEqual(len(self.plane.perceptions), 2)

  def test_the_same_triplet_gives_the_same_perception(self):
    first = self.plane.add("maison", 0.25, 0.75)
    second = self.plane.add("maison", 0.25, 0.75)
    self.assertIs(first, second)
    self.assertEqual(len(self.plane.perceptions), 1)

  def test_an_existing_perception_keeps_its_energy_when_added_again(self):
    self.plane.add("maison", 0.25, 0.75).energy = 2.0
    self.assertEqual(self.plane.add("maison", 0.25, 0.75).energy, 2.0)

if __name__ == "__main__":
  unittest.main()
