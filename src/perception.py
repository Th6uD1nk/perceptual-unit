class Perception:
  __slots__ = ("hash", "x", "y", "energy", "read", "read_tick")

  def __init__(self, hash_, x, y):
    self.hash = hash_
    self.x = x
    self.y = y
    self.energy = 0.0
    self.read = False
    self.read_tick = 0

  @property
  def key(self):
    return (self.hash, self.x, self.y)
