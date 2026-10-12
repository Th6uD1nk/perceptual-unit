from validation import validate_clock

class Scheduler:
  def __init__(self, config):
    validate_clock(config)
    self.tick_ms = config["clock"]["tick"]
    self.ticks = 0
    self.elapsed = 0.0

  def advance(self, dt_ms):
    if dt_ms < 0:
      raise ValueError("dt_ms: must not be negative")
    self.elapsed += dt_ms
    count = int(self.elapsed // self.tick_ms)
    self.elapsed -= count * self.tick_ms
    self.ticks += count
    return count
