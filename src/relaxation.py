class Relaxation:
  def __init__(self, memory, plane):
    self.memory = memory
    self.plane = plane

  def on_visit(self, perception):
    x, y, cost = self.memory.pull(perception, self.plane)
    self.plane.move(perception, x, y)
    return cost

  def start(self, scheduler):
    self.plane.register(scheduler, self.on_visit)
