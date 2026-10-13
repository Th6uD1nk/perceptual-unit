import unittest

import support
from moments import Moments
from scheduler import Scheduler

class CurrentTest(unittest.TestCase):
  def test_the_current_moment_follows_the_moment_of_the_scheduler(self):
    scheduler = Scheduler({"scheduler": {"tick": 1.0, "budget": 0, "moment": 2}})
    moments = Moments(scheduler)
    self.assertEqual(moments.current(), 0)
    scheduler.advance(2.0)
    self.assertEqual(moments.current(), 1)

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
