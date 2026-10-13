import unittest
from types import SimpleNamespace

import support
from generator import Generator
from scheduler import Scheduler
from moments import Moments
from perception import Perception
from plane import Plane

POINT = ("house", 0.25, 0.75)
KEY = POINT + (0,)

def make_plane(uid="A", peak=10.0, moments=None):
  return Plane({"uid": uid, "peak": peak}, moments if moments is not None else support.moments())

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
    self.clock = SimpleNamespace(moment=0)
    self.moments = Moments(self.clock, 2)
    self.plane = make_plane(moments=self.moments)

  def test_the_same_triplet_received_in_two_moments_gives_two_perceptions_with_their_own_energy(self):
    self.plane.receive(*POINT, 1.0)
    self.clock.moment = 1
    self.plane.receive(*POINT, 2.0)
    self.assertEqual(self.plane.perceptions[POINT + (0,)].energy, 1.0)
    self.assertEqual(self.plane.perceptions[POINT + (1,)].energy, 2.0)

  def test_a_perception_keeps_the_moment_in_which_it_was_born(self):
    self.plane.receive(*POINT, 1.0)
    self.clock.moment = 5
    self.assertEqual(self.plane.perceptions[POINT + (0,)].moment, 0)

  def test_a_transfer_lands_in_the_moment_in_progress_of_the_target_and_the_source_keeps_its_moment(self):
    target = make_plane("C", moments=self.moments)
    self.plane.receive(*POINT, 1.0)
    self.clock.moment = 1
    self.plane.transfer(self.plane.perceptions[POINT + (0,)], target, 0.25)
    self.assertEqual(self.plane.perceptions[POINT + (0,)].energy, 0.75)
    self.assertEqual(list(target.perceptions), [POINT + (1,)])
    self.assertEqual(target.perceptions[POINT + (1,)].energy, 0.25)

class CountTest(unittest.TestCase):
  def setUp(self):
    self.clock = SimpleNamespace(moment=0)
    self.moments = Moments(self.clock, 2)
    self.plane = make_plane(moments=self.moments)

  def test_a_reception_that_creates_a_perception_counts_it_and_a_reinforcement_does_not(self):
    self.plane.receive(*POINT, 1.0)
    self.plane.receive(*POINT, 1.0)
    self.assertEqual(self.moments.count(0), 1)

  def test_two_perceptions_of_one_moment_count_two(self):
    self.plane.receive(*POINT, 1.0)
    self.plane.receive("cat", 0.5, 0.5, 1.0)
    self.assertEqual(self.moments.count(0), 2)

  def test_a_removal_takes_one_off_the_count_of_the_moment_of_the_perception_and_not_of_the_moment_in_progress(self):
    self.plane.receive(*POINT, 1.0)
    self.clock.moment = 1
    self.plane.remove(self.plane.perceptions[KEY])
    self.assertEqual((self.moments.count(0), self.moments.count(1)), (0, 0))

  def test_a_perception_emptied_by_a_take_leaves_the_count_and_a_partial_take_does_not(self):
    self.plane.receive(*POINT, 1.0)
    self.plane.take(self.plane.perceptions[KEY], 0.5)
    self.assertEqual(self.moments.count(0), 1)
    self.plane.take(self.plane.perceptions[KEY], 0.5)
    self.assertEqual(self.moments.count(0), 0)

  def test_a_transfer_that_empties_the_source_moves_the_count_to_the_moment_in_progress_of_the_target(self):
    target = make_plane("C", moments=self.moments)
    self.plane.receive(*POINT, 1.0)
    self.clock.moment = 1
    self.plane.transfer(self.plane.perceptions[KEY], target, 1.0)
    self.assertEqual((self.moments.count(0), self.moments.count(1)), (0, 1))

class MoveTest(unittest.TestCase):
  def setUp(self):
    self.clock = SimpleNamespace(moment=0)
    self.moments = Moments(self.clock, 2)
    self.plane = make_plane(peak=4.0, moments=self.moments)
    self.plane.receive(*POINT, 1.0)
    self.perception = self.plane.perceptions[KEY]

  def test_a_moved_perception_takes_its_new_position_and_its_new_key(self):
    self.assertIs(self.plane.move(self.perception, 0.5, 0.5), self.perception)
    self.assertEqual(self.perception.key, ("house", 0.5, 0.5, 0))
    self.assertIs(self.plane.perceptions[("house", 0.5, 0.5, 0)], self.perception)
    self.assertNotIn(KEY, self.plane.perceptions)
    self.assertEqual((self.perception.energy, self.perception.moment), (1.0, 0))

  def test_the_new_position_is_brought_back_into_the_plane(self):
    self.plane.move(self.perception, 1.5, -0.2)
    self.assertEqual((self.perception.x, self.perception.y), (1.0, 0.0))

  def test_a_perception_that_is_not_on_the_plane_is_not_moved(self):
    stranger = Perception(*KEY)
    stranger.energy = 1.0
    self.assertIsNone(self.plane.move(stranger, 0.5, 0.5))
    self.assertEqual((stranger.x, stranger.y), (0.25, 0.75))
    self.assertIn(KEY, self.plane.perceptions)

  def test_a_simple_move_does_not_change_the_count_of_the_moment(self):
    self.plane.move(self.perception, 0.5, 0.5)
    self.assertEqual(self.moments.count(0), 1)

  def test_two_perceptions_of_one_hash_and_one_moment_that_meet_are_merged(self):
    self.plane.receive("house", 0.5, 0.75, 2.0)
    other = self.plane.perceptions[("house", 0.5, 0.75, 0)]
    kept = self.plane.move(other, 0.25, 0.75)
    self.assertIs(kept, self.perception)
    self.assertEqual(list(self.plane.perceptions), [KEY])
    self.assertEqual(self.perception.energy, 3.0)
    self.assertEqual(self.moments.count(0), 1)

  def test_a_merge_stops_at_the_peak_and_the_surplus_stays_in_the_moved_perception(self):
    self.plane.receive(*POINT, 2.0)
    self.plane.receive("house", 0.5, 0.75, 2.0)
    other = self.plane.perceptions[("house", 0.5, 0.75, 0)]
    kept = self.plane.move(other, 0.25, 0.75)
    self.assertIs(kept, self.perception)
    self.assertEqual((self.perception.energy, other.energy), (4.0, 1.0))
    self.assertIs(self.plane.perceptions[("house", 0.5, 0.75, 0)], other)
    self.assertEqual(self.moments.count(0), 2)

  def test_a_perception_of_another_hash_or_of_another_moment_is_not_merged(self):
    self.plane.receive("cat", 0.5, 0.75, 1.0)
    self.clock.moment = 1
    self.plane.receive("house", 0.5, 0.75, 1.0)
    for key in (("cat", 0.5, 0.75, 0), ("house", 0.5, 0.75, 1)):
      self.plane.move(self.plane.perceptions[key], 0.25, 0.75)
    self.assertEqual(len(self.plane.perceptions), 3)

  def test_a_perception_moved_during_a_pass_is_visited_once_and_an_absorbed_one_is_skipped(self):
    self.plane.receive("house", 0.5, 0.75, 1.0)
    other = self.plane.perceptions[("house", 0.5, 0.75, 0)]
    seen = []
    def hook(perception):
      seen.append(perception.key)
      if perception is self.perception:
        self.plane.move(other, 0.25, 0.75)
    self.plane.visit(10, hook)
    self.assertEqual(seen, [KEY])

class MomentIndexTest(unittest.TestCase):
  def setUp(self):
    self.clock = SimpleNamespace(moment=0)
    self.plane = make_plane(peak=4.0, moments=Moments(self.clock, 2))

  def test_the_perceptions_of_a_moment_are_listed_without_those_of_the_others(self):
    self.plane.receive("a", 0.1, 0.1, 1.0)
    self.plane.receive("b", 0.2, 0.2, 1.0)
    self.clock.moment = 1
    self.plane.receive("c", 0.3, 0.3, 1.0)
    self.assertEqual(sorted(perception.hash for perception in self.plane.of_moment(0)), ["a", "b"])
    self.assertEqual([perception.hash for perception in self.plane.of_moment(1)], ["c"])

  def test_a_reinforcement_does_not_list_a_perception_twice(self):
    self.plane.receive(*POINT, 1.0)
    self.plane.receive(*POINT, 1.0)
    self.assertEqual(len(self.plane.of_moment(0)), 1)

  def test_a_moment_without_perception_gives_an_empty_list_and_leaves_no_entry(self):
    self.assertEqual(self.plane.of_moment(5), [])
    self.plane.receive(*POINT, 1.0)
    self.plane.remove(self.plane.perceptions[KEY])
    self.assertEqual(self.plane.of_moment(0), [])
    self.assertEqual(self.plane.by_moment, {})

  def test_the_list_given_back_is_a_copy(self):
    self.plane.receive(*POINT, 1.0)
    self.plane.of_moment(0).clear()
    self.assertEqual(len(self.plane.of_moment(0)), 1)

  def test_the_index_follows_the_perceptions_through_receptions_takes_moves_merges_and_removals(self):
    generator = Generator(5)
    positions = [0.25, 0.5, 0.75]
    for _ in range(300):
      self.clock.moment = generator.draw(3)
      action = generator.draw(4)
      hash_ = f"word{generator.draw(3)}"
      x = positions[generator.draw(3)]
      if action == 0:
        self.plane.receive(hash_, x, 0.5, 0.5)
      elif self.plane.perceptions:
        perception = list(self.plane.perceptions.values())[generator.draw(len(self.plane.perceptions))]
        if action == 1:
          self.plane.take(perception, 0.4)
        elif action == 2:
          self.plane.move(perception, x, 0.5)
        else:
          self.plane.remove(perception)
      for moment in range(3):
        expected = {id(perception) for perception in self.plane.perceptions.values() if perception.moment == moment}
        self.assertEqual({id(perception) for perception in self.plane.of_moment(moment)}, expected)
      for name in ("word0", "word1", "word2"):
        expected = {id(perception) for perception in self.plane.perceptions.values() if perception.hash == name}
        self.assertEqual({id(perception) for perception in self.plane.living(name)}, expected)
      self.assertTrue(all(self.plane.by_hash.values()))

  def test_the_living_perceptions_of_a_hash_cross_the_moments_and_leave_no_empty_entry(self):
    self.plane.receive("a", 0.1, 0.1, 1.0)
    self.clock.moment = 1
    self.plane.receive("a", 0.2, 0.2, 1.0)
    self.plane.receive("b", 0.3, 0.3, 1.0)
    self.assertEqual(sorted(perception.x for perception in self.plane.living("a")), [0.1, 0.2])
    self.assertEqual(self.plane.living("none"), [])
    for perception in self.plane.living("a"):
      self.plane.remove(perception)
    self.assertEqual(list(self.plane.by_hash), ["b"])

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

  def test_a_transfer_to_nothing_takes_the_energy_and_loses_it(self):
    self.assertEqual(self.source.transfer(self.perception, None, 2.0), 2.0)
    self.assertEqual(self.perception.energy, 1.0)
    self.assertEqual(self.energy(self.target), 0.0)

  def test_a_transfer_to_nothing_larger_than_the_energy_empties_and_removes_the_perception(self):
    self.assertEqual(self.source.transfer(self.perception, None, 5.0), 3.0)
    self.assertNotIn(KEY, self.source.perceptions)
    self.assertEqual(self.source.moments.count(0), 0)

  def test_a_transfer_to_nothing_of_a_perception_that_left_the_plane_gives_nothing(self):
    self.source.remove(self.perception)
    self.assertEqual(self.source.transfer(self.perception, None, 1.0), 0.0)

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

  def test_a_step_that_costs_more_makes_each_perception_count_for_its_cost(self):
    self.assertEqual(self.plane.visit(100, lambda perception: 3), (9, True))

  def test_a_perception_that_costs_more_than_what_is_left_is_still_visited_and_the_pass_is_cut_after_it(self):
    self.assertEqual(self.plane.visit(2, lambda perception: self.seen.append(perception.hash) or 3), (3, False))
    self.assertEqual(self.seen, ["word0"])
    self.plane.visit(2, lambda perception: self.seen.append(perception.hash) or 3)
    self.assertEqual(self.seen, ["word0", "word1"])

  def test_a_cost_that_is_not_an_integer_of_at_least_one_is_refused(self):
    for cost in (0, -1, 1.5, "1", True):
      plane = make_plane()
      plane.receive(*POINT, 1.0)
      with self.assertRaises(ValueError, msg=repr(cost)):
        plane.visit(5, lambda perception, cost=cost: cost)

  def test_the_visit_does_not_need_a_callback(self):
    self.assertEqual(self.plane.visit(10), (3, True))

class RunTest(unittest.TestCase):
  def setUp(self):
    self.scheduler = Scheduler({"scheduler": {"tick": 1.0, "budget": 0, "moment": 1000}})
    self.plane = make_plane()
    for index in range(4):
      self.plane.receive(f"word{index}", 0.1 * index, 0.5, 1.0)
    self.seen = []
    self.ended = []

  def register(self, name="a"):
    self.plane.register(self.scheduler, lambda perception: self.seen.append((name, perception.hash)), lambda: self.ended.append(name))

  def test_a_registered_step_sees_every_perception_of_a_pass_in_order(self):
    self.register()
    self.scheduler.advance(1.0)
    self.assertEqual(self.seen, [("a", f"word{index}") for index in range(4)])

  def test_every_registered_step_sees_every_perception_of_the_same_pass(self):
    self.register("a")
    self.register("b")
    self.scheduler.advance(1.0)
    self.assertEqual(sorted(self.seen), sorted([(name, f"word{index}") for name in ("a", "b") for index in range(4)]))

  def test_each_end_of_pass_is_called_once_per_pass(self):
    self.register("a")
    self.register("b")
    self.scheduler.advance(2.0)
    self.assertEqual(self.ended, ["a", "b", "a", "b"])

  def test_a_pass_cut_by_the_budget_calls_its_ends_only_when_it_is_complete(self):
    scheduler = Scheduler({"scheduler": {"tick": 1.0, "budget": 2, "moment": 1000}})
    self.plane.register(scheduler, lambda perception: self.seen.append(perception.hash), lambda: self.ended.append("end"))
    scheduler.advance(1.0)
    self.assertEqual((len(self.seen), self.ended), (2, []))
    scheduler.advance(1.0)
    self.assertEqual((len(self.seen), self.ended), (4, ["end"]))

  def test_a_pass_cut_by_the_budget_still_shows_every_perception_to_every_step(self):
    scheduler = Scheduler({"scheduler": {"tick": 1.0, "budget": 2, "moment": 1000}})
    first, second = [], []
    self.plane.register(scheduler, lambda perception: first.append(perception.hash), lambda: None)
    self.plane.register(scheduler, lambda perception: second.append(perception.hash), lambda: None)
    scheduler.advance(2.0)
    self.assertEqual(first, [f"word{index}" for index in range(4)])
    self.assertEqual(second, first)

  def test_the_cost_of_a_perception_is_the_greatest_cost_of_its_steps(self):
    self.plane.register(self.scheduler, lambda perception: 2, lambda: None)
    self.plane.register(self.scheduler, lambda perception: None, lambda: None)
    self.assertEqual(self.plane.run(100), 8)

  def test_a_costly_step_makes_the_budget_cut_the_pass_after_the_perception_that_overran_it(self):
    scheduler = Scheduler({"scheduler": {"tick": 1.0, "budget": 4, "moment": 1000}})
    self.plane.register(scheduler, lambda perception: self.seen.append(perception.hash) or 3, lambda: self.ended.append("end"))
    scheduler.advance(1.0)
    self.assertEqual((len(self.seen), self.ended), (2, []))
    scheduler.advance(1.0)
    self.assertEqual((len(self.seen), self.ended), (4, ["end"]))

  def test_a_step_that_gives_back_an_invalid_cost_is_refused(self):
    self.plane.register(self.scheduler, lambda perception: 0, lambda: None)
    with self.assertRaises(ValueError):
      self.plane.run(10)

  def test_the_end_of_a_pass_is_optional(self):
    self.plane.register(self.scheduler, lambda perception: self.seen.append(perception.hash))
    self.scheduler.advance(1.0)
    self.assertEqual(len(self.seen), 4)
    self.assertEqual(self.plane.ends, [])

  def test_a_run_gives_back_the_number_of_perceptions_it_visited(self):
    self.register()
    self.assertEqual(self.plane.run(10), 4)

  def test_a_plane_without_registration_submits_no_work(self):
    self.scheduler.advance(3.0)
    self.assertEqual(self.seen, [])
    self.assertEqual(len(self.scheduler.queue), 0)

class StateTest(unittest.TestCase):
  def test_the_state_of_an_empty_plane_has_no_perception(self):
    self.assertEqual(make_plane("A", peak=4.0).state(), {"uid": "A", "peak": 4.0, "perceptions": []})

  def test_the_state_lists_the_perceptions_in_the_order_of_their_arrival(self):
    plane = make_plane()
    plane.receive("house", 0.25, 0.75, 1.0)
    plane.receive("cat", 0.5, 0.5, 2.0)
    perceptions = plane.state()["perceptions"]
    self.assertEqual([entry["hash"] for entry in perceptions], ["house", "cat"])
    self.assertEqual(perceptions[1], {"hash": "cat", "x": 0.5, "y": 0.5, "moment": 0, "energy": 2.0, "read": False})

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
