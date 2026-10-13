import collections

from perception import Perception

class Plane:
  def __init__(self, config, moments):
    self.uid = config["uid"]
    self.peak = config["peak"]
    self.moments = moments
    self.perceptions = {}
    self.visit_queue = None

  def receive(self, hash_, x, y, amount):
    moment = self.moments.current()
    key = (hash_, x, y, moment)
    perception = self.perceptions.get(key)
    room = self.peak - (perception.energy if perception is not None else 0.0)
    accepted = min(amount, room)
    if accepted <= 0:
      return 0.0
    if perception is None:
      perception = self.perceptions[key] = Perception(hash_, x, y, moment)
      self.moments.born(moment)
    perception.energy += accepted
    return accepted

  def remove(self, perception):
    if self.perceptions.get(perception.key) is not perception:
      return False
    del self.perceptions[perception.key]
    self.moments.died(perception.moment)
    return True

  def take(self, perception, amount):
    if amount <= 0 or self.perceptions.get(perception.key) is not perception:
      return 0.0
    taken = min(amount, perception.energy)
    perception.energy -= taken
    if taken > 0 and perception.energy <= 0:
      self.remove(perception)
    return taken

  def transfer(self, perception, target, amount):
    if self.perceptions.get(perception.key) is not perception:
      return 0.0
    offered = min(amount, perception.energy)
    accepted = target.receive(perception.hash, perception.x, perception.y, offered)
    return self.take(perception, accepted)

  def visit(self, units, on_visit=None):
    if units <= 0:
      return 0, False
    if self.visit_queue is None:
      self.visit_queue = collections.deque(self.perceptions.values())
    used = 0
    while self.visit_queue and used < units:
      perception = self.visit_queue.popleft()
      used += 1
      if self.perceptions.get(perception.key) is perception and on_visit is not None:
        on_visit(perception)
    finished = not self.visit_queue
    if finished:
      self.visit_queue = None
    return used, finished

  def state(self):
    return {"uid": self.uid, "peak": self.peak, "perceptions": [perception.state() for perception in self.perceptions.values()]}
