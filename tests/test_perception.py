import unittest

import support
from perception import Perception

class PerceptionTest(unittest.TestCase):
  def test_a_perception_starts_without_energy(self):
    self.assertEqual(Perception("house", 0.25, 0.75, 0).energy, 0.0)

  def test_a_perception_is_read_by_no_cursor_at_birth(self):
    self.assertEqual(Perception("house", 0.25, 0.75, 0).reads, {})

  def test_the_key_is_the_triplet_of_the_hash_and_the_position(self):
    self.assertEqual(Perception("house", 0.25, 0.75, 0).key, ("house", 0.25, 0.75, 0))

  def test_the_key_includes_the_moment_and_two_moments_give_two_keys(self):
    first = Perception("house", 0.25, 0.75, 0)
    second = Perception("house", 0.25, 0.75, 1)
    self.assertEqual(first.moment, 0)
    self.assertNotEqual(first.key, second.key)

  def test_the_key_follows_the_position(self):
    perception = Perception("house", 0.25, 0.75, 0)
    perception.x = 0.5
    self.assertEqual(perception.key, ("house", 0.5, 0.75, 0))

  def test_the_key_cannot_be_set(self):
    with self.assertRaises(AttributeError):
      Perception("house", 0.25, 0.75, 0).key = ("cat", 0.0, 0.0, 0)

  def test_a_perception_holds_nothing_else(self):
    with self.assertRaises(AttributeError):
      Perception("house", 0.1, 0.1, 0).other = 3

class AgeTest(unittest.TestCase):
  def test_a_perception_is_born_at_tick_zero_by_default(self):
    self.assertEqual(Perception("house", 0.25, 0.75, 0).born, 0)

  def test_the_birth_tick_is_the_one_given(self):
    self.assertEqual(Perception("house", 0.25, 0.75, 0, 40).born, 40)

  def test_the_age_is_the_number_of_ticks_since_the_birth(self):
    perception = Perception("house", 0.25, 0.75, 0, 40)
    self.assertEqual(perception.age(40), 0)
    self.assertEqual(perception.age(65), 25)

  def test_the_birth_tick_does_not_change_the_key_nor_the_state(self):
    young, old = Perception("house", 0.25, 0.75, 0, 40), Perception("house", 0.25, 0.75, 0, 0)
    self.assertEqual(young.key, old.key)
    self.assertEqual(young.state(), old.state())

class StateTest(unittest.TestCase):
  def test_the_state_gives_the_hash_the_position_the_moment_and_the_energy(self):
    perception = Perception("house", 0.25, 0.75, 3)
    perception.energy = 0.5
    self.assertEqual(perception.state(), {"hash": "house", "x": 0.25, "y": 0.75, "moment": 3, "energy": 0.5})

  def test_the_state_follows_the_changes_of_the_perception(self):
    perception = Perception("house", 0.25, 0.75, 0)
    perception.energy = 0.125
    perception.x = 0.5
    self.assertEqual(perception.state()["energy"], 0.125)
    self.assertEqual(perception.state()["x"], 0.5)

  def test_changing_the_state_does_not_change_the_perception(self):
    perception = Perception("house", 0.25, 0.75, 0)
    perception.state()["energy"] = 9.0
    self.assertEqual(perception.energy, 0.0)

if __name__ == "__main__":
  unittest.main()
