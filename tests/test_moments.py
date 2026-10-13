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

if __name__ == "__main__":
  unittest.main()
