import collections
import math

from validation import validate_clock

MICROSECONDS_PER_MILLISECOND = 1000

class Scheduler:
  def __init__(self, config):
    validate_clock(config)
    self.tick_us = round(config["clock"]["tick"] * MICROSECONDS_PER_MILLISECOND)
    self.ticks = 0
    self.elapsed_us = 0
    self.queue = collections.deque()

  def submit(self, work):
    if not callable(work):
      raise ValueError("work: must be callable")
    self.queue.append(work)

  def cycle(self):
    for _ in range(len(self.queue)):
      used = self.queue.popleft()(math.inf)
      if isinstance(used, bool) or not isinstance(used, int) or used < 0:
        raise ValueError("work: must return an integer of at least 0")

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
