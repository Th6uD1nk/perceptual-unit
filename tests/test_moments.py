import unittest

import support
from moments import Moments
from scheduler import Scheduler

class CurrentTest(unittest.TestCase):
  def test_the_current_moment_follows_the_moment_of_the_scheduler(self):
    scheduler = Scheduler({"scheduler": {"tick": 1.0, "budget": 0, "moment": 2}})
    moments = Moments(scheduler, 2)
    self.assertEqual(moments.current(), 0)
    scheduler.advance(2.0)
    self.assertEqual(moments.current(), 1)

class TicksTest(unittest.TestCase):
  def test_the_ticks_follow_the_scheduler(self):
    scheduler = Scheduler({"scheduler": {"tick": 1.0, "budget": 0, "moment": 100}})
    moments = Moments(scheduler, 2)
    self.assertEqual(moments.ticks, 0)
    scheduler.advance(7.0)
    self.assertEqual(moments.ticks, 7)

class CountTest(unittest.TestCase):
  def setUp(self):
    self.moments = support.moments()

  def test_a_moment_nobody_was_born_in_counts_zero(self):
    self.assertEqual(self.moments.count(7), 0)

  def test_a_birth_adds_one_to_the_count_of_its_moment_only(self):
    self.moments.born(1)
    self.moments.born(1)
    self.moments.born(2)
    self.assertEqual((self.moments.count(1), self.moments.count(2)), (2, 1))

  def test_a_death_takes_one_off_the_count_of_its_moment(self):
    self.moments.born(1)
    self.moments.born(1)
    self.moments.died(1)
    self.assertEqual(self.moments.count(1), 1)
    self.moments.died(1)
    self.assertEqual(self.moments.count(1), 0)
    self.assertNotIn(1, self.moments.counts)

  def test_a_death_in_a_moment_that_counts_zero_is_refused(self):
    with self.assertRaises(ValueError):
      self.moments.died(1)

class EventTest(unittest.TestCase):
  def setUp(self):
    self.moments = support.moments()

  def test_an_event_enters_the_moment_in_progress(self):
    self.moments.record(["a", "b"])
    self.assertEqual(self.moments.events(0), [["a", "b"]])

  def test_the_order_and_the_duplicates_of_the_hashes_and_the_order_of_the_events_are_kept(self):
    self.moments.record(["a", "b", "a"])
    self.moments.record(["c"])
    self.assertEqual(self.moments.events(0), [["a", "b", "a"], ["c"]])

  def test_each_moment_has_its_own_events(self):
    self.moments.born(0)
    self.moments.record(["a"])
    self.moments.scheduler.moment = 1
    self.moments.record(["b"])
    self.assertEqual(self.moments.events(0), [["a"]])
    self.assertEqual(self.moments.events(1), [["b"]])

  def test_an_event_is_independent_of_the_list_it_was_made_from_and_of_what_is_given_back(self):
    source = ["a", "b"]
    given = self.moments.record(source)
    source.append("c")
    given.append("d")
    self.moments.events(0)[0].append("e")
    self.assertEqual(self.moments.events(0), [["a", "b"]])

  def test_a_moment_without_events_gives_an_empty_list(self):
    self.assertEqual(self.moments.events(9), [])

class ContextTest(unittest.TestCase):
  def setUp(self):
    self.moments = support.moments()

  def test_the_contexts_of_an_event_of_three_words_are_its_three_neighborhoods(self):
    self.moments.record(["a", "b", "c"])
    self.assertEqual(self.moments.contexts(0), {(None, "b"): {"a": 1}, ("a", "c"): {"b": 1}, ("b", None): {"c": 1}})

  def test_an_event_of_one_word_has_no_neighbor_on_either_side(self):
    self.moments.record(["a"])
    self.assertEqual(self.moments.contexts(0), {(None, None): {"a": 1}})

  def test_the_same_event_recorded_twice_counts_each_context_twice(self):
    self.moments.record(["a", "b", "c"])
    self.moments.record(["a", "b", "c"])
    self.assertEqual(self.moments.contexts(0)[("a", "c")], {"b": 2})

  def test_two_events_with_the_same_neighbors_and_another_middle_share_the_context(self):
    self.moments.record(["a", "x", "c"])
    self.moments.record(["a", "y", "c"])
    self.assertEqual(self.moments.contexts(0)[("a", "c")], {"x": 1, "y": 1})

  def test_a_word_repeated_in_an_event_gives_one_context_per_position(self):
    self.moments.record(["a", "b", "a"])
    self.assertEqual(self.moments.contexts(0), {(None, "b"): {"a": 1}, ("a", "a"): {"b": 1}, ("b", None): {"a": 1}})

  def test_each_moment_has_its_own_contexts(self):
    self.moments.born(0)
    self.moments.record(["a", "b"])
    self.moments.scheduler.moment = 1
    self.moments.record(["c", "d"])
    self.assertEqual(self.moments.contexts(0), {(None, "b"): {"a": 1}, ("a", None): {"b": 1}})
    self.assertEqual(self.moments.contexts(1), {(None, "d"): {"c": 1}, ("c", None): {"d": 1}})

  def test_the_contexts_given_back_are_independent_of_the_stored_ones(self):
    self.moments.record(["a", "b"])
    given = self.moments.contexts(0)
    given[("a", None)]["b"] = 9
    given[("z", "z")] = {}
    self.assertEqual(self.moments.contexts(0), {(None, "b"): {"a": 1}, ("a", None): {"b": 1}})

  def test_a_moment_without_events_has_no_context(self):
    self.assertEqual(self.moments.contexts(9), {})

  def test_the_contexts_are_released_with_the_events_of_a_closed_moment_without_perception(self):
    self.moments.born(0)
    self.moments.record(["a", "b"])
    self.moments.scheduler.moment = 1
    self.assertNotEqual(self.moments.contexts(0), {})
    self.moments.died(0)
    self.assertEqual(self.moments.contexts(0), {})

class TotalTest(unittest.TestCase):
  def setUp(self):
    self.moments = support.moments()

  def test_between_gives_the_words_seen_between_two_neighbors_with_their_count(self):
    self.moments.record(["a", "b", "c"])
    self.moments.record(["a", "b", "c"])
    self.moments.record(["a", "x", "c"])
    self.assertEqual(self.moments.between("a", "c"), {"b": 2, "x": 1})

  def test_the_edges_of_a_flow_are_asked_with_none(self):
    self.moments.record(["a", "b"])
    self.assertEqual(self.moments.between(None, "b"), {"a": 1})
    self.assertEqual(self.moments.between("a", None), {"b": 1})

  def test_an_unknown_pair_gives_an_empty_answer(self):
    self.assertEqual(self.moments.between("a", "c"), {})

  def test_between_adds_the_counts_of_the_moments(self):
    self.moments.born(0)
    self.moments.record(["a", "b", "c"])
    self.moments.scheduler.moment = 1
    self.moments.born(1)
    self.moments.record(["a", "b", "c"])
    self.assertEqual(self.moments.between("a", "c"), {"b": 2})

  def test_the_release_of_a_moment_takes_off_only_what_it_brought(self):
    self.moments.born(0)
    self.moments.record(["a", "b", "c"])
    self.moments.scheduler.moment = 1
    self.moments.born(1)
    self.moments.record(["a", "b", "c"])
    self.moments.record(["a", "x", "c"])
    self.moments.died(0)
    self.assertEqual(self.moments.between("a", "c"), {"b": 1, "x": 1})

  def test_nothing_is_left_when_every_moment_is_released(self):
    self.moments.born(0)
    self.moments.record(["a", "b", "c"])
    self.moments.scheduler.moment = 1
    self.moments.died(0)
    self.assertEqual(self.moments.totals, {})
    self.assertEqual(self.moments.between("a", "c"), {})

  def test_a_moment_that_closes_without_perception_is_taken_off_the_totals_at_the_change_of_moment(self):
    self.moments.record(["a", "b"])
    self.moments.scheduler.moment = 1
    self.moments.current()
    self.assertEqual(self.moments.totals, {})

  def test_the_answer_is_independent_of_the_stored_totals(self):
    self.moments.record(["a", "b", "c"])
    answer = self.moments.between("a", "c")
    answer["b"] = 9
    self.assertEqual(self.moments.between("a", "c"), {"b": 1})

class LinkTest(unittest.TestCase):
  def test_the_words_within_the_window_of_an_event_are_linked_and_the_others_are_not(self):
    moments = support.moments(window=2)
    moments.record(["a", "b", "c", "d"])
    links = {pair: moments.link(pair[0], pair[1]) for pair in ("ab", "ac", "bc", "bd", "cd", "ad")}
    self.assertEqual(links, {"ab": 1, "ac": 1, "bc": 1, "bd": 1, "cd": 1, "ad": 0})

  def test_a_window_of_zero_links_all_the_words_of_the_event(self):
    moments = support.moments(window=0)
    moments.record(["a", "b", "c", "d"])
    self.assertEqual(moments.link("a", "d"), 1)

  def test_a_pair_that_appears_several_times_in_an_event_is_linked_once_and_a_word_is_never_linked_to_itself(self):
    moments = support.moments()
    moments.record(["a", "b", "a", "b"])
    moments.record(["c", "c"])
    self.assertEqual(moments.link("a", "b"), 1)
    self.assertEqual(moments.link("c", "c"), 0)
    self.assertEqual(moments.link_totals, {("a", "b"): 1})

  def test_the_link_is_the_same_in_both_directions_and_adds_up_from_event_to_event(self):
    moments = support.moments()
    moments.record(["a", "b"])
    moments.record(["b", "a"])
    self.assertEqual((moments.link("a", "b"), moments.link("b", "a")), (2, 2))

  def test_each_moment_has_its_own_links_and_the_link_adds_up_the_living_moments(self):
    moments = support.moments()
    moments.born(0)
    moments.record(["a", "b"])
    moments.scheduler.moment = 1
    moments.born(1)
    moments.record(["a", "b"])
    moments.record(["a", "c"])
    self.assertEqual(moments.links_of(0), {("a", "b"): 1})
    self.assertEqual(moments.links_of(1), {("a", "b"): 1, ("a", "c"): 1})
    self.assertEqual(moments.link("a", "b"), 2)

  def test_the_release_of_a_moment_takes_off_only_the_links_it_brought(self):
    moments = support.moments()
    moments.born(0)
    moments.record(["a", "b"])
    moments.scheduler.moment = 1
    moments.born(1)
    moments.record(["a", "b"])
    moments.died(0)
    self.assertEqual(moments.link("a", "b"), 1)
    self.assertEqual(moments.links_of(0), {})

  def test_nothing_is_left_when_every_moment_is_released(self):
    moments = support.moments()
    moments.born(0)
    moments.record(["a", "b"])
    moments.scheduler.moment = 1
    moments.died(0)
    self.assertEqual(moments.link_totals, {})

  def test_a_moment_that_closes_without_perception_takes_its_links_off_at_the_change_of_moment(self):
    moments = support.moments()
    moments.record(["a", "b"])
    moments.scheduler.moment = 1
    moments.current()
    self.assertEqual(moments.link_totals, {})

  def test_the_links_given_back_are_independent_of_the_stored_ones(self):
    moments = support.moments()
    moments.record(["a", "b"])
    moments.links_of(0)[("a", "b")] = 9
    self.assertEqual(moments.links_of(0), {("a", "b"): 1})

class ReleaseTest(unittest.TestCase):
  def setUp(self):
    self.moments = support.moments()

  def next_moment(self):
    self.moments.scheduler.moment += 1

  def test_an_open_moment_keeps_its_events_even_when_it_counts_zero(self):
    self.moments.born(0)
    self.moments.record(["a"])
    self.moments.died(0)
    self.assertEqual(self.moments.events(0), [["a"]])

  def test_a_closed_moment_keeps_its_events_while_a_perception_lives_and_loses_them_at_the_last_death(self):
    self.moments.born(0)
    self.moments.born(0)
    self.moments.record(["a"])
    self.next_moment()
    self.moments.died(0)
    self.assertEqual(self.moments.events(0), [["a"]])
    self.moments.died(0)
    self.assertEqual(self.moments.events(0), [])
    self.assertNotIn(0, self.moments.recorded)

  def test_a_moment_that_closes_without_any_perception_loses_its_events_at_the_change_of_moment(self):
    self.moments.record(["a"])
    self.next_moment()
    self.moments.record(["b"])
    self.assertNotIn(0, self.moments.recorded)
    self.assertEqual(self.moments.events(0), [])
    self.assertEqual(self.moments.events(1), [["b"]])

  def test_a_moment_that_closes_while_a_perception_lives_keeps_its_events(self):
    self.moments.born(0)
    self.moments.record(["a"])
    self.next_moment()
    self.assertEqual(self.moments.events(0), [["a"]])

if __name__ == "__main__":
  unittest.main()
