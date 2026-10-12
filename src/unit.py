import copy

from plane import Plane
from scheduler import Scheduler
from validation import validate_config

class Unit:
  def __init__(self, config):
    validate_config(config)
    self.config = copy.deepcopy(config)
    self.planes = {entry["uid"]: Plane(entry) for entry in self.config["planes"]}
    self.scheduler = Scheduler(self.config)

  @property
  def ticks(self):
    return self.scheduler.ticks

  def update(self, dt_ms):
    return self.scheduler.advance(dt_ms)

  def state(self):
    return {"ticks": self.ticks, "planes": [plane.state() for plane in self.planes.values()]}
