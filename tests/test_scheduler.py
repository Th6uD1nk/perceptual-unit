import math
import unittest

import support
from scheduler import Scheduler

def make_scheduler(tick=4.0):
  return Scheduler({"clock": {"tick": tick}})

class AdvanceTest(unittest.TestCase):
  def test_a_new_scheduler_has_no_tick(self):
    self.assertEqual(make_scheduler().ticks, 0)

  def test_partial_amounts_add_up_to_a_tick(self):
    scheduler = make_scheduler()
    self.assertEqual(scheduler.advance(3.0), 0)
    self.assertEqual(scheduler.ticks, 0)
    self.assertEqual(scheduler.advance(3.0), 1)
    self.assertEqual(scheduler.ticks, 1)

  def test_several_ticks_can_elapse_at_once_and_the_remainder_is_kept(self):
    scheduler = make_scheduler()
    self.assertEqual(scheduler.advance(10.0), 2)
    self.assertEqual(scheduler.advance(2.0), 1)
    self.assertEqual(scheduler.ticks, 3)

  def test_a_zero_duration_changes_nothing(self):
    scheduler = make_scheduler()
    scheduler.advance(3.0)
    self.assertEqual(scheduler.advance(0.0), 0)
    self.assertEqual(scheduler.advance(1.0), 1)

  def test_a_negative_duration_is_refused_and_changes_nothing(self):
    scheduler = make_scheduler()
    scheduler.advance(3.0)
    with self.assertRaises(ValueError):
      scheduler.advance(-1.0)
    self.assertEqual(scheduler.advance(1.0), 1)

  def test_a_fractional_tick_is_counted_exactly(self):
    self.assertEqual(make_scheduler(tick=0.1).advance(0.3), 3)

  def test_inexact_durations_lose_no_tick_over_many_calls(self):
    scheduler = make_scheduler(tick=1.0)
    for _ in range(60):
      scheduler.advance(16.7)
    self.assertEqual(scheduler.ticks, 1002)

class WorkTest(unittest.TestCase):
  def setUp(self):
    self.scheduler = make_scheduler()
    self.calls = []

  def record(self, name):
    def work(units):
      self.calls.append(name)
      return 0
    return work

  def test_a_submitted_work_waits_for_a_full_tick(self):
    self.scheduler.submit(self.record("a"))
    self.scheduler.advance(3.0)
    self.assertEqual(self.calls, [])
    self.scheduler.advance(1.0)
    self.assertEqual(self.calls, ["a"])

  def test_a_work_runs_once_unless_it_submits_itself_again(self):
    self.scheduler.submit(self.record("a"))
    self.scheduler.advance(12.0)
    self.assertEqual(self.calls, ["a"])

  def test_a_work_that_submits_itself_again_runs_at_every_tick(self):
    def again(units):
      self.calls.append("again")
      self.scheduler.submit(again)
      return 0
    self.scheduler.submit(again)
    self.scheduler.advance(12.0)
    self.assertEqual(self.calls, ["again", "again", "again"])

  def test_the_works_run_in_the_order_of_their_submission(self):
    for name in ("a", "b", "c"):
      self.scheduler.submit(self.record(name))
    self.scheduler.advance(4.0)
    self.assertEqual(self.calls, ["a", "b", "c"])

  def test_a_work_submitted_during_a_cycle_waits_for_the_next_tick(self):
    def submitter(units):
      self.scheduler.submit(self.record("late"))
      return 0
    self.scheduler.submit(submitter)
    self.scheduler.advance(4.0)
    self.assertEqual(self.calls, [])
    self.scheduler.advance(4.0)
    self.assertEqual(self.calls, ["late"])

  def test_the_ticks_are_counted_before_the_works_of_a_tick_run(self):
    seen = []
    def work(units):
      seen.append(self.scheduler.ticks)
      return 0
    self.scheduler.submit(work)
    self.scheduler.advance(4.0)
    self.assertEqual(seen, [1])

  def test_a_work_receives_unlimited_units_when_there_is_no_budget(self):
    seen = []
    def work(units):
      seen.append(units)
      return 0
    self.scheduler.submit(work)
    self.scheduler.advance(4.0)
    self.assertEqual(seen, [math.inf])

  def test_a_work_must_give_back_an_integer_of_at_least_zero(self):
    for value in (-1, 1.5, "1", None, True):
      scheduler = make_scheduler()
      scheduler.submit(lambda units, value=value: value)
      with self.assertRaises(ValueError, msg=repr(value)):
        scheduler.advance(4.0)

  def test_a_work_must_be_callable(self):
    with self.assertRaises(ValueError):
      self.scheduler.submit("work")

class ConfigTest(unittest.TestCase):
  def rejected(self, config):
    with self.assertRaises(ValueError) as caught:
      Scheduler(config)
    return str(caught.exception)

  def test_a_config_must_be_an_object(self):
    self.assertIn("config:", self.rejected([]))

  def test_the_clock_is_required(self):
    self.assertIn("config.clock", self.rejected({}))

  def test_the_clock_must_be_an_object(self):
    self.assertIn("config.clock", self.rejected({"clock": 4.0}))

  def test_the_tick_is_required(self):
    self.assertIn("config.clock.tick", self.rejected({"clock": {}}))

  def test_the_tick_must_be_a_number_of_at_least_one_microsecond(self):
    for tick in (0, -1, 0.0005, "4", None, True, [4]):
      self.assertIn("config.clock.tick", self.rejected({"clock": {"tick": tick}}), repr(tick))

if __name__ == "__main__":
  unittest.main()
