import unittest

import support
from perception import Perception
from plane import Plane

POINT = ("house", 0.25, 0.75)
KEY = POINT + (0,)

def make_plane(uid="A", peak=10.0, current_moment=support.now):
  return Plane({"uid": uid, "peak": peak}, current_moment)

class PlaneTest(unittest.TestCase):
  def test_a_new_plane_holds_no_perception(self):
    self.assertEqual(make_plane().perceptions, {})

  def test_two_planes_do_not_share_their_perceptions(self):
    first = make_plane()
    second = make_plane("C")
    first.receive(*POINT, 1.0)
    self.assertEqual(second.perceptions, {})

class ReceiveTest(unittest.TestCase):
  def setUp(self):
    self.plane = make_plane()

  def test_a_reception_creates_a_perception_with_that_energy_under_its_own_key(self):
    self.plane.receive(*POINT, 2.0)
    perception = self.plane.perceptions[KEY]
    self.assertEqual(perception.key, KEY)
    self.assertEqual(perception.energy, 2.0)

  def test_a_reception_returns_the_amount_received(self):
    self.assertEqual(self.plane.receive(*POINT, 2.0), 2.0)

  def test_a_second_reception_at_the_same_triplet_feeds_the_same_perception(self):
    self.plane.receive(*POINT, 2.0)
    first = self.plane.perceptions[KEY]
    self.plane.receive(*POINT, 1.5)
    self.assertEqual(len(self.plane.perceptions), 1)
    self.assertIs(self.plane.perceptions[KEY], first)
    self.assertEqual(first.energy, 3.5)

  def test_two_hashes_give_two_perceptions_with_their_own_energy(self):
    self.plane.receive("house", 0.25, 0.75, 2.0)
    self.plane.receive("cat", 0.25, 0.75, 1.0)
    self.assertEqual(self.plane.perceptions[("house", 0.25, 0.75, 0)].energy, 2.0)
    self.assertEqual(self.plane.perceptions[("cat", 0.25, 0.75, 0)].energy, 1.0)

  def test_two_positions_of_one_hash_give_two_perceptions(self):
    self.plane.receive("house", 0.25, 0.75, 1.0)
    self.plane.receive("house", 0.5, 0.75, 1.0)
    self.assertEqual(len(self.plane.perceptions), 2)

  def test_a_zero_amount_creates_nothing(self):
    self.assertEqual(self.plane.receive(*POINT, 0.0), 0.0)
    self.assertEqual(self.plane.perceptions, {})

  def test_a_negative_amount_changes_nothing(self):
    self.plane.receive(*POINT, 2.0)
    self.assertEqual(self.plane.receive(*POINT, -1.0), 0.0)
    self.assertEqual(self.plane.perceptions[KEY].energy, 2.0)
    self.assertEqual(self.plane.receive("cat", 0.25, 0.75, -1.0), 0.0)
    self.assertEqual(len(self.plane.perceptions), 1)

class PeakTest(unittest.TestCase):
  def test_a_reception_larger_than_the_peak_is_cut_at_the_peak(self):
    plane = make_plane(peak=4.0)
    self.assertEqual(plane.receive(*POINT, 6.0), 4.0)
    self.assertEqual(plane.perceptions[KEY].energy, 4.0)

  def test_a_reinforcement_accepts_only_what_is_left_below_the_peak(self):
    plane = make_plane(peak=4.0)
    plane.receive(*POINT, 3.0)
    self.assertEqual(plane.receive(*POINT, 3.0), 1.0)
    self.assertEqual(plane.perceptions[KEY].energy, 4.0)

  def test_a_perception_at_the_peak_accepts_nothing(self):
    plane = make_plane(peak=4.0)
    plane.receive(*POINT, 4.0)
    self.assertEqual(plane.receive(*POINT, 1.0), 0.0)
    self.assertEqual(plane.perceptions[KEY].energy, 4.0)

  def test_the_peak_applies_to_each_perception_on_its_own(self):
    plane = make_plane(peak=4.0)
    plane.receive("house", 0.25, 0.75, 4.0)
    self.assertEqual(plane.receive("cat", 0.25, 0.75, 3.0), 3.0)

  def test_each_plane_has_its_own_peak(self):
    small = make_plane(peak=1.0)
    large = make_plane("C", peak=5.0)
    self.assertEqual(small.receive(*POINT, 3.0), 1.0)
    self.assertEqual(large.receive(*POINT, 3.0), 3.0)

class MomentTest(unittest.TestCase):
  def setUp(self):
    self.moment = [0]
    self.plane = make_plane(current_moment=lambda: self.moment[0])

  def test_the_same_triplet_received_in_two_moments_gives_two_perceptions_with_their_own_energy(self):
    self.plane.receive(*POINT, 1.0)
    self.moment[0] = 1
    self.plane.receive(*POINT, 2.0)
    self.assertEqual(self.plane.perceptions[POINT + (0,)].energy, 1.0)
    self.assertEqual(self.plane.perceptions[POINT + (1,)].energy, 2.0)

  def test_a_perception_keeps_the_moment_in_which_it_was_born(self):
    self.plane.receive(*POINT, 1.0)
    self.moment[0] = 5
    self.assertEqual(self.plane.perceptions[POINT + (0,)].moment, 0)

  def test_a_transfer_lands_in_the_moment_in_progress_of_the_target_and_the_source_keeps_its_moment(self):
    target = make_plane("C", current_moment=lambda: self.moment[0])
    self.plane.receive(*POINT, 1.0)
    self.moment[0] = 1
    self.plane.transfer(self.plane.perceptions[POINT + (0,)], target, 0.25)
    self.assertEqual(self.plane.perceptions[POINT + (0,)].energy, 0.75)
    self.assertEqual(list(target.perceptions), [POINT + (1,)])
    self.assertEqual(target.perceptions[POINT + (1,)].energy, 0.25)

class RemoveTest(unittest.TestCase):
  def setUp(self):
    self.plane = make_plane()
    self.plane.receive(*POINT, 2.0)
    self.perception = self.plane.perceptions[KEY]

  def test_a_removed_perception_is_no_longer_on_the_plane(self):
    self.assertTrue(self.plane.remove(self.perception))
    self.assertNotIn(KEY, self.plane.perceptions)

  def test_the_other_perceptions_stay(self):
    self.plane.receive("cat", 0.25, 0.75, 1.0)
    kept = self.plane.perceptions[("cat", 0.25, 0.75, 0)]
    self.plane.remove(self.perception)
    self.assertEqual(list(self.plane.perceptions.values()), [kept])

  def test_a_perception_that_was_never_on_the_plane_is_not_removed(self):
    other = make_plane("C")
    other.receive(*POINT, 2.0)
    foreign = other.perceptions[KEY]
    self.assertFalse(self.plane.remove(foreign))
    self.assertIn(KEY, other.perceptions)

  def test_another_object_with_the_same_key_does_not_remove_the_perception(self):
    self.assertFalse(self.plane.remove(Perception(*KEY)))
    self.assertIs(self.plane.perceptions[KEY], self.perception)

  def test_a_perception_born_again_after_its_removal_is_a_new_one(self):
    self.plane.remove(self.perception)
    self.plane.receive(*POINT, 1.0)
    reborn = self.plane.perceptions[KEY]
    self.assertIsNot(reborn, self.perception)
    self.assertEqual(reborn.energy, 1.0)

class TakeTest(unittest.TestCase):
  def setUp(self):
    self.plane = make_plane()
    self.plane.receive(*POINT, 3.0)
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
    other = make_plane("C")
    other.receive(*POINT, 3.0)
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

class TransferTest(unittest.TestCase):
  def setUp(self):
    self.source = make_plane("A", peak=10.0)
    self.target = make_plane("C", peak=4.0)
    self.source.receive(*POINT, 3.0)
    self.perception = self.source.perceptions[KEY]

  def energy(self, plane):
    return sum(perception.energy for perception in plane.perceptions.values())

  def test_the_target_receives_at_the_same_triplet_what_the_source_gives_up(self):
    self.assertEqual(self.source.transfer(self.perception, self.target, 2.0), 2.0)
    self.assertEqual(self.target.perceptions[KEY].energy, 2.0)
    self.assertEqual(self.perception.energy, 1.0)

  def test_a_request_larger_than_the_energy_transfers_everything_and_empties_the_source(self):
    self.assertEqual(self.source.transfer(self.perception, self.target, 5.0), 3.0)
    self.assertEqual(self.target.perceptions[KEY].energy, 3.0)
    self.assertNotIn(KEY, self.source.perceptions)

  def test_the_surplus_above_the_target_peak_stays_in_the_source(self):
    self.source.receive(*POINT, 4.0)
    before = self.energy(self.source) + self.energy(self.target)
    self.assertEqual(self.source.transfer(self.perception, self.target, 7.0), 4.0)
    self.assertEqual(self.target.perceptions[KEY].energy, 4.0)
    self.assertEqual(self.perception.energy, 3.0)
    self.assertEqual(self.energy(self.source) + self.energy(self.target), before)

  def test_a_target_perception_at_the_peak_accepts_nothing_and_the_source_keeps_everything(self):
    self.target.receive(*POINT, 4.0)
    self.assertEqual(self.source.transfer(self.perception, self.target, 2.0), 0.0)
    self.assertEqual(self.perception.energy, 3.0)

  def test_the_transfer_feeds_an_existing_perception_of_the_target(self):
    self.target.receive(*POINT, 1.0)
    self.source.transfer(self.perception, self.target, 2.0)
    self.assertEqual(self.target.perceptions[KEY].energy, 3.0)
    self.assertEqual(len(self.target.perceptions), 1)

  def test_a_zero_or_negative_amount_transfers_nothing(self):
    self.assertEqual(self.source.transfer(self.perception, self.target, 0.0), 0.0)
    self.assertEqual(self.source.transfer(self.perception, self.target, -1.0), 0.0)
    self.assertEqual(self.target.perceptions, {})
    self.assertEqual(self.perception.energy, 3.0)

  def test_a_perception_that_is_not_on_the_source_transfers_nothing(self):
    stranger = Perception(*KEY)
    stranger.energy = 3.0
    self.assertEqual(self.source.transfer(stranger, self.target, 2.0), 0.0)
    self.assertEqual(self.target.perceptions, {})
    self.assertEqual(stranger.energy, 3.0)

class VisitTest(unittest.TestCase):
  def setUp(self):
    self.plane = make_plane()
    for index in range(3):
      self.plane.receive(f"word{index}", 0.1 * index, 0.5, 1.0)
    self.seen = []

  def visit(self, units):
    return self.plane.visit(units, lambda perception: self.seen.append(perception.hash))

  def test_a_pass_visits_each_perception_once_and_ends(self):
    self.assertEqual(self.visit(10), (3, True))
    self.assertEqual(self.seen, ["word0", "word1", "word2"])

  def test_a_pass_cut_by_the_units_resumes_where_it_stopped(self):
    self.assertEqual(self.visit(2), (2, False))
    self.assertEqual(self.seen, ["word0", "word1"])
    self.assertEqual(self.visit(2), (1, True))
    self.assertEqual(self.seen, ["word0", "word1", "word2"])

  def test_a_new_pass_starts_again_from_the_first_perception(self):
    self.visit(10)
    self.visit(10)
    self.assertEqual(self.seen, ["word0", "word1", "word2"] * 2)

  def test_a_pass_over_an_empty_plane_ends_at_once(self):
    self.assertEqual(make_plane().visit(5), (0, True))

  def test_zero_or_negative_units_visit_nothing_and_start_no_pass(self):
    self.assertEqual(self.visit(0), (0, False))
    self.assertEqual(self.visit(-1), (0, False))
    self.assertEqual(self.seen, [])
    self.visit(10)
    self.assertEqual(self.seen, ["word0", "word1", "word2"])

  def test_a_perception_removed_during_a_pass_is_skipped_but_costs_a_unit(self):
    self.visit(1)
    self.plane.take(self.plane.perceptions[("word1", 0.1, 0.5, 0)], 1.0)
    self.assertEqual(self.visit(10), (2, True))
    self.assertEqual(self.seen, ["word0", "word2"])

  def test_a_perception_born_during_a_pass_waits_for_the_next_pass(self):
    self.visit(1)
    self.plane.receive("late", 0.9, 0.5, 1.0)
    self.visit(10)
    self.assertEqual(self.seen, ["word0", "word1", "word2"])
    self.visit(10)
    self.assertEqual(self.seen[3:], ["word0", "word1", "word2", "late"])

  def test_the_visit_does_not_need_a_callback(self):
    self.assertEqual(self.plane.visit(10), (3, True))

class StateTest(unittest.TestCase):
  def test_the_state_of_an_empty_plane_has_no_perception(self):
    self.assertEqual(make_plane("A", peak=4.0).state(), {"uid": "A", "peak": 4.0, "perceptions": []})

  def test_the_state_lists_the_perceptions_in_the_order_of_their_arrival(self):
    plane = make_plane()
    plane.receive("house", 0.25, 0.75, 1.0)
    plane.receive("cat", 0.5, 0.5, 2.0)
    perceptions = plane.state()["perceptions"]
    self.assertEqual([entry["hash"] for entry in perceptions], ["house", "cat"])
    self.assertEqual(perceptions[1], {"hash": "cat", "x": 0.5, "y": 0.5, "energy": 2.0, "read": False})

  def test_a_perception_that_left_the_plane_is_no_longer_in_the_state(self):
    plane = make_plane()
    plane.receive(*POINT, 1.0)
    plane.take(plane.perceptions[KEY], 1.0)
    self.assertEqual(plane.state()["perceptions"], [])

class InvariantTest(unittest.TestCase):
  def test_every_perception_on_a_plane_has_energy(self):
    plane = make_plane()
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
