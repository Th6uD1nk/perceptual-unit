class Perception:
  __slots__ = ("hash", "x", "y", "moment", "energy", "read", "read_tick")

  def __init__(self, hash_, x, y, moment):
    self.hash = hash_
    self.x = x
    self.y = y
    self.moment = moment
    self.energy = 0.0
    self.read = False
    self.read_tick = 0

  @property
  def key(self):
    return (self.hash, self.x, self.y, self.moment)

  def state(self):
    return {"hash": self.hash, "x": self.x, "y": self.y, "moment": self.moment, "energy": self.energy, "read": self.read}
