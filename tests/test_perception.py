import unittest

import support
from perception import Perception

class PerceptionTest(unittest.TestCase):
  def test_a_perception_starts_without_energy(self):
    self.assertEqual(Perception("house", 0.25, 0.75).energy, 0.0)

  def test_a_perception_is_not_read_at_birth(self):
    self.assertFalse(Perception("house", 0.25, 0.75).read)

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
