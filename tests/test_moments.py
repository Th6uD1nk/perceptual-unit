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

if __name__ == "__main__":
  unittest.main()
