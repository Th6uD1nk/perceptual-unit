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
