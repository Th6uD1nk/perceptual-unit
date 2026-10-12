import unittest

import support
from perception import Perception
from plane import Plane

KEY = ("house", 0.25, 0.75)

class PlaneTest(unittest.TestCase):
  def test_a_new_plane_holds_no_perception(self):
    self.assertEqual(Plane({"uid": "A"}).perceptions, {})

  def test_two_planes_do_not_share_their_perceptions(self):
    first = Plane({"uid": "A"})
    second = Plane({"uid": "C"})
    first.receive(*KEY, 1.0)
    self.assertEqual(second.perceptions, {})

class ReceiveTest(unittest.TestCase):
  def setUp(self):
    self.plane = Plane({"uid": "A"})

  def test_a_reception_creates_a_perception_with_that_energy_under_its_own_key(self):
    self.plane.receive(*KEY, 2.0)
    perception = self.plane.perceptions[KEY]
    self.assertEqual(perception.key, KEY)
    self.assertEqual(perception.energy, 2.0)

  def test_a_reception_returns_the_amount_received(self):
    self.assertEqual(self.plane.receive(*KEY, 2.0), 2.0)

  def test_a_second_reception_at_the_same_triplet_feeds_the_same_perception(self):
    self.plane.receive(*KEY, 2.0)
    first = self.plane.perceptions[KEY]
    self.plane.receive(*KEY, 1.5)
    self.assertEqual(len(self.plane.perceptions), 1)
    self.assertIs(self.plane.perceptions[KEY], first)
    self.assertEqual(first.energy, 3.5)

  def test_two_hashes_give_two_perceptions_with_their_own_energy(self):
    self.plane.receive("house", 0.25, 0.75, 2.0)
    self.plane.receive("cat", 0.25, 0.75, 1.0)
    self.assertEqual(self.plane.perceptions[("house", 0.25, 0.75)].energy, 2.0)
    self.assertEqual(self.plane.perceptions[("cat", 0.25, 0.75)].energy, 1.0)

  def test_two_positions_of_one_hash_give_two_perceptions(self):
    self.plane.receive("house", 0.25, 0.75, 1.0)
    self.plane.receive("house", 0.5, 0.75, 1.0)
    self.assertEqual(len(self.plane.perceptions), 2)

  def test_a_zero_amount_creates_nothing(self):
    self.assertEqual(self.plane.receive(*KEY, 0.0), 0.0)
    self.assertEqual(self.plane.perceptions, {})

  def test_a_negative_amount_changes_nothing(self):
    self.plane.receive(*KEY, 2.0)
    self.assertEqual(self.plane.receive(*KEY, -1.0), 0.0)
    self.assertEqual(self.plane.perceptions[KEY].energy, 2.0)
    self.assertEqual(self.plane.receive("cat", 0.25, 0.75, -1.0), 0.0)
    self.assertEqual(len(self.plane.perceptions), 1)

class RemoveTest(unittest.TestCase):
  def setUp(self):
    self.plane = Plane({"uid": "A"})
    self.plane.receive(*KEY, 2.0)
    self.perception = self.plane.perceptions[KEY]

  def test_a_removed_perception_is_no_longer_on_the_plane(self):
    self.assertTrue(self.plane.remove(self.perception))
    self.assertNotIn(KEY, self.plane.perceptions)

  def test_the_other_perceptions_stay(self):
    self.plane.receive("cat", 0.25, 0.75, 1.0)
    kept = self.plane.perceptions[("cat", 0.25, 0.75)]
    self.plane.remove(self.perception)
    self.assertEqual(list(self.plane.perceptions.values()), [kept])

  def test_removing_twice_does_nothing_the_second_time(self):
    self.plane.remove(self.perception)
    self.assertFalse(self.plane.remove(self.perception))

  def test_a_perception_that_was_never_on_the_plane_is_not_removed(self):
    other = Plane({"uid": "C"})
    other.receive(*KEY, 2.0)
    foreign = other.perceptions[KEY]
    self.assertFalse(self.plane.remove(foreign))
    self.assertIn(KEY, other.perceptions)

  def test_another_object_with_the_same_key_does_not_remove_the_perception(self):
    self.assertFalse(self.plane.remove(Perception(*KEY)))
    self.assertIs(self.plane.perceptions[KEY], self.perception)

  def test_a_perception_born_again_after_its_removal_is_a_new_one(self):
    self.plane.remove(self.perception)
    self.plane.receive(*KEY, 1.0)
    reborn = self.plane.perceptions[KEY]
    self.assertIsNot(reborn, self.perception)
    self.assertEqual(reborn.energy, 1.0)

class TakeTest(unittest.TestCase):
  def setUp(self):
    self.plane = Plane({"uid": "A"})
    self.plane.receive(*KEY, 3.0)
    self.perception = self.plane.perceptions[KEY]

  def test_the_requested_amount_is_taken_when_there_is_enough(self):
    self.assertEqual(self.plane.take(self.perception, 2.0), 2.0)
    self.assertEqual(self.perception.energy, 1.0)

  def test_everything_left_is_taken_when_the_request_is_larger(self):
    self.assertEqual(self.plane.take(self.perception, 5.0), 3.0)
    self.assertEqual(self.perception.energy, 0.0)

  def test_a_zero_or_negative_amount_takes_nothing(self):
    self.assertEqual(self.plane.take(self.perception, 0.0), 0.0)
    self.assertEqual(self.plane.take(self.perception, -1.0), 0.0)
    self.assertEqual(self.perception.energy, 3.0)

  def test_a_perception_of_another_plane_loses_nothing(self):
    other = Plane({"uid": "C"})
    other.receive(*KEY, 3.0)
    foreign = other.perceptions[KEY]
    self.assertEqual(self.plane.take(foreign, 1.0), 0.0)
    self.assertEqual(foreign.energy, 3.0)

  def test_another_object_with_the_same_key_loses_nothing(self):
    stranger = Perception(*KEY)
    stranger.energy = 3.0
    self.assertEqual(self.plane.take(stranger, 1.0), 0.0)
    self.assertEqual(stranger.energy, 3.0)
    self.assertEqual(self.perception.energy, 3.0)

  def test_a_perception_emptied_by_a_take_leaves_the_plane(self):
    self.plane.take(self.perception, 3.0)
    self.assertNotIn(KEY, self.plane.perceptions)

  def test_a_perception_partly_taken_stays_on_the_plane(self):
    self.plane.take(self.perception, 2.0)
    self.assertIs(self.plane.perceptions[KEY], self.perception)

  def test_the_other_perceptions_stay_when_one_is_emptied(self):
    self.plane.receive("cat", 0.25, 0.75, 1.0)
    kept = self.plane.perceptions[("cat", 0.25, 0.75)]
    self.plane.take(self.perception, 3.0)
    self.assertEqual(list(self.plane.perceptions.values()), [kept])

class InvariantTest(unittest.TestCase):
  def test_every_perception_on_a_plane_has_energy(self):
    plane = Plane({"uid": "A"})
    for index in range(6):
      plane.receive(f"word{index}", 0.1 * index, 0.5, 1.0 + index)
    for perception in list(plane.perceptions.values()):
      plane.take(perception, 2.0)
    plane.receive("word0", 0.0, 0.5, 0.0)
    plane.receive("word1", 0.1, 0.5, -1.0)
    self.assertTrue(plane.perceptions)
    for perception in plane.perceptions.values():
      self.assertGreater(perception.energy, 0.0)

if __name__ == "__main__":
  unittest.main()
