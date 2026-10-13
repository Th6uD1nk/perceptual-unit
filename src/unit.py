import copy

from cursor import Cursor
from generator import Generator
from moments import Moments
from plane import Plane
from scheduler import Scheduler
from transcription import token_hash, token_position
from validation import validate_config

class Unit:
  def __init__(self, config):
    validate_config(config)
    self.config = copy.deepcopy(config)
    self.scheduler = Scheduler(self.config)
    self.moments = Moments(self.scheduler)
    self.planes = {entry["uid"]: Plane(entry, self.moments) for entry in self.config["planes"]}
    self.generator = Generator(self.config["random"]["seed"])
    self.cursors = [
      Cursor(transfer, self.planes[entry["uid"]], self.planes[transfer["target"]], self.generator)
      for entry in self.config["planes"]
      for transfer in entry["transfers"]
    ]
    for cursor in self.cursors:
      cursor.restart()
      cursor.start(self.scheduler)

  @property
  def ticks(self):
    return self.scheduler.ticks

  def update(self, dt_ms):
    return self.scheduler.advance(dt_ms)

  def feed_flow(self, tokens, energy):
    if not isinstance(tokens, list) or not tokens or any(not isinstance(token, str) or not token for token in tokens):
      raise ValueError("tokens: must be a non-empty list of non-empty strings")
    plane = next(iter(self.planes.values()))
    hashes = [token_hash(token) for token in tokens]
    accepted = []
    for token, hash_ in zip(tokens, hashes):
      x, y = token_position(token)
      accepted.append(plane.receive(hash_, x, y, energy))
    self.moments.record(hashes)
    return accepted

  def state(self):
    return {
      "ticks": self.ticks,
      "moment": self.moments.current(),
      "planes": [plane.state() for plane in self.planes.values()],
      "cursors": [cursor.state() for cursor in self.cursors]
    }
