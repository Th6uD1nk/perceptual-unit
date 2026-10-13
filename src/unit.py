import copy

from cursor import Cursor
from generator import Generator
from plane import Plane
from scheduler import Scheduler
from transcription import token_hash, token_position
from validation import validate_config

class Unit:
  def __init__(self, config):
    validate_config(config)
    self.config = copy.deepcopy(config)
    self.planes = {entry["uid"]: Plane(entry) for entry in self.config["planes"]}
    self.scheduler = Scheduler(self.config)
    self.generator = Generator(self.config["random"]["seed"])
    self.cursors = [
      Cursor(transfer, self.planes[entry["uid"]], self.planes[transfer["target"]], self.generator)
      for entry in self.config["planes"]
      for transfer in entry["transfers"]
    ]
    for cursor in self.cursors:
      cursor.restart()

  @property
  def ticks(self):
    return self.scheduler.ticks

  def update(self, dt_ms):
    return self.scheduler.advance(dt_ms)

  def feed(self, token, energy):
    if not isinstance(token, str) or not token:
      raise ValueError("token: must be a non-empty string")
    x, y = token_position(token)
    return next(iter(self.planes.values())).receive(token_hash(token), x, y, energy)

  def state(self):
    return {"ticks": self.ticks, "planes": [plane.state() for plane in self.planes.values()]}
