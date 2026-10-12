from perception import Perception

class Plane:
  def __init__(self, config):
    self.uid = config["uid"]
    self.perceptions = {}

  def add(self, hash_, x, y):
    key = (hash_, x, y)
    perception = self.perceptions.get(key)
    if perception is None:
      perception = Perception(hash_, x, y)
      self.perceptions[key] = perception
    return perception

  def remove(self, perception):
    if self.perceptions.get(perception.key) is not perception:
      return False
    del self.perceptions[perception.key]
    return True

  def receive(self, hash_, x, y, amount):
    if amount <= 0:
      return 0.0
    self.add(hash_, x, y).energy += amount
    return amount
