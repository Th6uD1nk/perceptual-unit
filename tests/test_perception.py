import unittest

import support
from perception import Perception

class PerceptionTest(unittest.TestCase):
  def test_a_perception_keeps_its_hash_and_its_position(self):
    perception = Perception("house", 0.25, 0.75)
    self.assertEqual(perception.hash, "house")
    self.assertEqual(perception.x, 0.25)
    self.assertEqual(perception.y, 0.75)

  def test_a_perception_starts_without_energy(self):
    self.assertEqual(Perception("house", 0.25, 0.75).energy, 0.0)

  def test_two_perceptions_do_not_share_their_state(self):
    first = Perception("house", 0.1, 0.1)
    second = Perception("house", 0.1, 0.1)
    first.energy = 2.0
    self.assertEqual(second.energy, 0.0)

  def test_the_key_is_the_triplet_of_the_hash_and_the_position(self):
    self.assertEqual(Perception("house", 0.25, 0.75).key, ("house", 0.25, 0.75))

  def test_the_key_follows_the_position(self):
    perception = Perception("house", 0.25, 0.75)
    perception.x = 0.5
    self.assertEqual(perception.key, ("house", 0.5, 0.75))

  def test_the_key_cannot_be_set(self):
    with self.assertRaises(AttributeError):
      Perception("house", 0.25, 0.75).key = ("cat", 0.0, 0.0)

  def test_a_perception_holds_nothing_else(self):
    with self.assertRaises(AttributeError):
      Perception("house", 0.1, 0.1).age = 3

if __name__ == "__main__":
  unittest.main()
