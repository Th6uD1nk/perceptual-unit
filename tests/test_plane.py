import unittest

import support
from perception import Perception
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

class RemoveTest(unittest.TestCase):
  def setUp(self):
    self.plane = Plane({"uid": "A"})

  def test_a_removed_perception_is_no_longer_on_the_plane(self):
    perception = self.plane.add("maison", 0.25, 0.75)
    self.assertTrue(self.plane.remove(perception))
    self.assertNotIn(perception.key, self.plane.perceptions)

  def test_the_other_perceptions_stay(self):
    removed = self.plane.add("maison", 0.25, 0.75)
    kept = self.plane.add("chat", 0.25, 0.75)
    self.plane.remove(removed)
    self.assertEqual(list(self.plane.perceptions.values()), [kept])

  def test_removing_twice_does_nothing_the_second_time(self):
    perception = self.plane.add("maison", 0.25, 0.75)
    self.plane.remove(perception)
    self.assertFalse(self.plane.remove(perception))

  def test_a_perception_that_was_never_on_the_plane_is_not_removed(self):
    other = Plane({"uid": "C"})
    perception = other.add("maison", 0.25, 0.75)
    self.assertFalse(self.plane.remove(perception))
    self.assertIn(perception.key, other.perceptions)

  def test_another_object_with_the_same_key_does_not_remove_the_perception(self):
    perception = self.plane.add("maison", 0.25, 0.75)
    self.assertFalse(self.plane.remove(Perception("maison", 0.25, 0.75)))
    self.assertIs(self.plane.perceptions[perception.key], perception)

  def test_a_perception_added_again_after_its_removal_is_a_new_one(self):
    old = self.plane.add("maison", 0.25, 0.75)
    old.energy = 2.0
    self.plane.remove(old)
    new = self.plane.add("maison", 0.25, 0.75)
    self.assertIsNot(new, old)
    self.assertEqual(new.energy, 0.0)

class ReceiveTest(unittest.TestCase):
  def setUp(self):
    self.plane = Plane({"uid": "A"})

  def test_a_reception_creates_a_perception_with_that_energy(self):
    self.plane.receive("maison", 0.25, 0.75, 2.0)
    self.assertEqual(self.plane.perceptions[("maison", 0.25, 0.75)].energy, 2.0)

  def test_a_reception_returns_the_amount_received(self):
    self.assertEqual(self.plane.receive("maison", 0.25, 0.75, 2.0), 2.0)

  def test_a_second_reception_at_the_same_triplet_adds_up(self):
    self.plane.receive("maison", 0.25, 0.75, 2.0)
    self.plane.receive("maison", 0.25, 0.75, 1.5)
    self.assertEqual(len(self.plane.perceptions), 1)
    self.assertEqual(self.plane.perceptions[("maison", 0.25, 0.75)].energy, 3.5)

  def test_two_triplets_give_two_perceptions_with_their_own_energy(self):
    self.plane.receive("maison", 0.25, 0.75, 2.0)
    self.plane.receive("chat", 0.25, 0.75, 1.0)
    self.assertEqual(self.plane.perceptions[("maison", 0.25, 0.75)].energy, 2.0)
    self.assertEqual(self.plane.perceptions[("chat", 0.25, 0.75)].energy, 1.0)

  def test_a_reception_feeds_a_perception_that_was_added_without_energy(self):
    perception = self.plane.add("maison", 0.25, 0.75)
    self.plane.receive("maison", 0.25, 0.75, 2.0)
    self.assertEqual(perception.energy, 2.0)
    self.assertEqual(len(self.plane.perceptions), 1)

  def test_a_zero_amount_creates_nothing(self):
    self.assertEqual(self.plane.receive("maison", 0.25, 0.75, 0.0), 0.0)
    self.assertEqual(self.plane.perceptions, {})

  def test_a_negative_amount_changes_nothing(self):
    self.plane.receive("maison", 0.25, 0.75, 2.0)
    self.assertEqual(self.plane.receive("maison", 0.25, 0.75, -1.0), 0.0)
    self.assertEqual(self.plane.perceptions[("maison", 0.25, 0.75)].energy, 2.0)
    self.assertEqual(self.plane.receive("chat", 0.25, 0.75, -1.0), 0.0)
    self.assertEqual(len(self.plane.perceptions), 1)

class TakeTest(unittest.TestCase):
  def setUp(self):
    self.plane = Plane({"uid": "A"})
    self.plane.receive("maison", 0.25, 0.75, 3.0)
    self.perception = self.plane.perceptions[("maison", 0.25, 0.75)]

  def test_the_requested_amount_is_taken_when_there_is_enough(self):
    self.assertEqual(self.plane.take(self.perception, 2.0), 2.0)
    self.assertEqual(self.perception.energy, 1.0)

  def test_everything_left_is_taken_when_the_request_is_larger(self):
    self.assertEqual(self.plane.take(self.perception, 5.0), 3.0)
    self.assertEqual(self.perception.energy, 0.0)

  def test_taking_again_after_the_energy_is_gone_takes_nothing(self):
    self.plane.take(self.perception, 5.0)
    self.assertEqual(self.plane.take(self.perception, 1.0), 0.0)

  def test_a_zero_or_negative_amount_takes_nothing(self):
    self.assertEqual(self.plane.take(self.perception, 0.0), 0.0)
    self.assertEqual(self.plane.take(self.perception, -1.0), 0.0)
    self.assertEqual(self.perception.energy, 3.0)

  def test_a_perception_of_another_plane_loses_nothing(self):
    other = Plane({"uid": "C"})
    other.receive("maison", 0.25, 0.75, 3.0)
    foreign = other.perceptions[("maison", 0.25, 0.75)]
    self.assertEqual(self.plane.take(foreign, 1.0), 0.0)
    self.assertEqual(foreign.energy, 3.0)

  def test_another_object_with_the_same_key_loses_nothing(self):
    stranger = Perception("maison", 0.25, 0.75)
    stranger.energy = 3.0
    self.assertEqual(self.plane.take(stranger, 1.0), 0.0)
    self.assertEqual(stranger.energy, 3.0)
    self.assertEqual(self.perception.energy, 3.0)

  def test_taking_leaves_the_perceptions_of_the_plane_in_place(self):
    self.plane.take(self.perception, 5.0)
    self.assertEqual(list(self.plane.perceptions.values()), [self.perception])

if __name__ == "__main__":
  unittest.main()
