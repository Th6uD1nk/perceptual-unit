from perception import Perception

class Plane:
  def __init__(self, config):
    self.uid = config["uid"]
    self.peak = config["peak"]
    self.perceptions = {}

  def receive(self, hash_, x, y, amount):
    key = (hash_, x, y)
    perception = self.perceptions.get(key)
    room = self.peak - (perception.energy if perception is not None else 0.0)
    accepted = min(amount, room)
    if accepted <= 0:
      return 0.0
    if perception is None:
      perception = self.perceptions[key] = Perception(hash_, x, y)
    perception.energy += accepted
    return accepted

  def remove(self, perception):
    if self.perceptions.get(perception.key) is not perception:
      return False
    del self.perceptions[perception.key]
    return True

  def take(self, perception, amount):
    if amount <= 0 or self.perceptions.get(perception.key) is not perception:
      return 0.0
    taken = min(amount, perception.energy)
    perception.energy -= taken
    if taken > 0 and perception.energy <= 0:
      self.remove(perception)
    return taken
