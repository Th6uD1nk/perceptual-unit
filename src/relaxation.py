class Relaxation:
  def __init__(self, memory, plane, kind="shape"):
    self.memory = memory
    self.plane = plane
    self.kind = kind

  def on_visit(self, perception):
    if self.kind == "usage":
      x, y, cost = self.memory.pull_usage(perception, self.plane, self.plane.moments)
    else:
      x, y, cost = self.memory.pull(perception, self.plane)
    self.plane.move(perception, x, y)
    return cost

  def start(self, scheduler):
    self.plane.register(scheduler, self.on_visit)
