class Perception:
  __slots__ = ("hash", "x", "y", "moment", "energy", "reads", "born")

  def __init__(self, hash_, x, y, moment, born=0):
    self.hash = hash_
    self.x = x
    self.y = y
    self.moment = moment
    self.energy = 0.0
    self.reads = {}
    self.born = born

  @property
  def key(self):
    return (self.hash, self.x, self.y, self.moment)

  def age(self, ticks):
    return ticks - self.born

  def state(self):
    return {"hash": self.hash, "x": self.x, "y": self.y, "moment": self.moment, "energy": self.energy}
