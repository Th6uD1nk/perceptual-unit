import copy

from cursor import Cursor
from generator import Generator
from memory import Memory
from moments import Moments
from plane import Plane
from relaxation import Relaxation
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
    self.memory = Memory(self.config)
    self.relaxations = [Relaxation(self.memory, self.planes[entry["uid"]]) for entry in self.config["planes"] if entry["relax"] == "shape"]
    for relaxation in self.relaxations:
      relaxation.start(self.scheduler)

  @property
  def ticks(self):
    return self.scheduler.ticks

  def update(self, dt_ms):
    return self.scheduler.advance(dt_ms)

  def feed_flow(self, tokens, energy):
    if not isinstance(tokens, list) or not tokens or any(not isinstance(token, str) or not token for token in tokens):
      raise ValueError("tokens: must be a non-empty list of non-empty strings")
    plane = next(iter(self.planes.values()))
    hashes = [self.memory.lexicon.add(token) for token in tokens]
    accepted = []
    for token, hash_ in zip(tokens, hashes):
      x, y = token_position(token)
      accepted.append(plane.receive(hash_, x, y, energy))
    self.moments.record(hashes)
    return accepted

  def between(self, left, right, uid=None):
    for neighbor in (left, right):
      if neighbor is not None and (not isinstance(neighbor, str) or not neighbor):
        raise ValueError("neighbor: must be None or a non-empty string")
    if uid is not None and uid not in self.planes:
      raise ValueError(f"uid: unknown plane {uid!r}")
    found = self.moments.between(
      None if left is None else token_hash(left),
      None if right is None else token_hash(right)
    )
    energies = {}
    if uid is not None and found:
      for perception in self.planes[uid].perceptions.values():
        energies[perception.hash] = energies.get(perception.hash, 0.0) + perception.energy
    entries = [
      {"hash": hash_, "count": count, "energy": energies.get(hash_, 0.0) if uid is not None else None}
      for hash_, count in found.items()
    ]
    if uid is None:
      entries.sort(key=lambda entry: (-entry["count"], entry["hash"]))
    else:
      entries.sort(key=lambda entry: (-entry["energy"], -entry["count"], entry["hash"]))
    return entries

  def state(self):
    return {
      "ticks": self.ticks,
      "moment": self.moments.current(),
      "planes": [plane.state() for plane in self.planes.values()],
      "cursors": [cursor.state() for cursor in self.cursors]
    }
