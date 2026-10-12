import unittest

import support
from scheduler import Scheduler

def make_scheduler(tick=4.0):
  return Scheduler({"clock": {"tick": tick}})

class AdvanceTest(unittest.TestCase):
  def test_a_new_scheduler_has_no_tick(self):
    self.assertEqual(make_scheduler().ticks, 0)

  def test_less_than_a_tick_gives_no_tick(self):
    scheduler = make_scheduler()
    self.assertEqual(scheduler.advance(3.0), 0)
    self.assertEqual(scheduler.ticks, 0)

  def test_partial_amounts_add_up_to_a_tick(self):
    scheduler = make_scheduler()
    self.assertEqual(scheduler.advance(3.0), 0)
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

  def test_the_tick_duration_comes_from_the_config(self):
    self.assertEqual(make_scheduler(tick=2.0).advance(10.0), 5)

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

  def test_the_tick_must_be_a_number_greater_than_zero(self):
    for tick in (0, -1, "4", None, True, [4]):
      self.assertIn("config.clock.tick", self.rejected({"clock": {"tick": tick}}), repr(tick))

if __name__ == "__main__":
  unittest.main()
