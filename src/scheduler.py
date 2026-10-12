import collections
import math

from validation import validate_scheduler

MICROSECONDS_PER_MILLISECOND = 1000

class Scheduler:
  def __init__(self, config):
    validate_scheduler(config)
    self.tick_us = round(config["scheduler"]["tick"] * MICROSECONDS_PER_MILLISECOND)
    self.budget = config["scheduler"]["budget"]
    self.ticks = 0
    self.elapsed_us = 0
    self.queue = collections.deque()

  def submit(self, work):
    if not callable(work):
      raise ValueError("work: must be callable")
    self.queue.append(work)

  def cycle(self):
    remaining = self.budget if self.budget else math.inf
    for _ in range(len(self.queue)):
      if remaining <= 0:
        break
      used = self.queue.popleft()(remaining)
      if isinstance(used, bool) or not isinstance(used, int) or used < 0:
        raise ValueError("work: must return an integer of at least 0")
      remaining -= used

  def advance(self, dt_ms):
    if dt_ms < 0:
      raise ValueError("dt_ms: must not be negative")
    self.elapsed_us += round(dt_ms * MICROSECONDS_PER_MILLISECOND)
    count = self.elapsed_us // self.tick_us
    self.elapsed_us -= count * self.tick_us
    for _ in range(count):
      self.ticks += 1
      self.cycle()
    return count
