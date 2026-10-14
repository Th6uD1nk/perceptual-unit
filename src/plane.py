import collections

from perception import Perception

def checked_cost(cost):
  if isinstance(cost, bool) or not isinstance(cost, int) or cost < 1:
    raise ValueError("cost: must be an integer of at least 1")
  return cost

class Plane:
  def __init__(self, config, moments):
    self.uid = config["uid"]
    self.peak = config["peak"]
    self.moments = moments
    self.perceptions = {}
    self.by_moment = {}
    self.by_hash = {}
    self.visit_queue = None
    self.scheduler = None
    self.steps = []
    self.ends = []

  def receive(self, hash_, x, y, amount):
    moment = self.moments.current()
    perception = self.find(hash_, moment)
    room = self.peak - (perception.energy if perception is not None else 0.0)
    accepted = min(amount, room)
    if accepted <= 0:
      return 0.0
    if perception is None:
      key = (hash_, x, y, moment)
      perception = self.perceptions[key] = Perception(hash_, x, y, moment, self.moments.ticks)
      self.by_moment.setdefault(moment, {})[key] = perception
      self.by_hash.setdefault(hash_, {})[key] = perception
      self.moments.born(moment)
    perception.energy += accepted
    return accepted

  def find(self, hash_, moment):
    for perception in self.by_hash.get(hash_, {}).values():
      if perception.moment == moment:
        return perception
    return None

  def move(self, perception, x, y):
    if self.perceptions.get(perception.key) is not perception:
      return None
    x = max(0.0, min(1.0, x))
    y = max(0.0, min(1.0, y))
    key = (perception.hash, x, y, perception.moment)
    if key == perception.key:
      return perception
    del self.perceptions[perception.key]
    del self.by_moment[perception.moment][perception.key]
    del self.by_hash[perception.hash][perception.key]
    perception.x = x
    perception.y = y
    self.perceptions[perception.key] = perception
    self.by_moment[perception.moment][perception.key] = perception
    self.by_hash[perception.hash][perception.key] = perception
    return perception

  def living(self, hash_):
    return list(self.by_hash.get(hash_, {}).values())

  def of_moment(self, moment):
    return list(self.by_moment.get(moment, {}).values())

  def remove(self, perception):
    if self.perceptions.get(perception.key) is not perception:
      return False
    del self.perceptions[perception.key]
    del self.by_moment[perception.moment][perception.key]
    if not self.by_moment[perception.moment]:
      del self.by_moment[perception.moment]
    del self.by_hash[perception.hash][perception.key]
    if not self.by_hash[perception.hash]:
      del self.by_hash[perception.hash]
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
    if target is None:
      return self.take(perception, offered)
    accepted = target.receive(perception.hash, perception.x, perception.y, offered)
    return self.take(perception, accepted)

  def register(self, scheduler, step, end=None):
    self.steps.append(step)
    if end is not None:
      self.ends.append(end)
    if self.scheduler is None:
      self.scheduler = scheduler
      scheduler.submit(self.run)

  def run(self, units):
    used, finished = self.visit(units, self.visit_steps)
    if finished:
      for end in self.ends:
        end()
    self.scheduler.submit(self.run)
    return used

  def visit_steps(self, perception):
    cost = 1
    for step in self.steps:
      result = step(perception)
      if result is not None:
        cost = max(cost, checked_cost(result))
    return cost

  def visit(self, units, on_visit=None):
    if units <= 0:
      return 0, False
    if self.visit_queue is None:
      self.visit_queue = collections.deque(self.perceptions.values())
    used = 0
    while self.visit_queue and used < units:
      perception = self.visit_queue.popleft()
      cost = 1
      if self.perceptions.get(perception.key) is perception and on_visit is not None:
        result = on_visit(perception)
        if result is not None:
          cost = checked_cost(result)
      used += cost
    finished = not self.visit_queue
    if finished:
      self.visit_queue = None
    return used, finished

  def state(self):
    return {"uid": self.uid, "peak": self.peak, "perceptions": [perception.state() for perception in self.perceptions.values()]}
