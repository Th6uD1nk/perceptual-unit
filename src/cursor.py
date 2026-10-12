import math

class Cursor:
  def __init__(self, x, y, dx, dy, source, target, energy):
    if not (0 <= x <= 1 and 0 <= y <= 1):
      raise ValueError("position: must be inside the plane")
    if energy <= 0:
      raise ValueError("energy: must be greater than 0")
    length = math.hypot(dx, dy)
    if length == 0:
      raise ValueError("direction: must not be null")
    self.x = x
    self.y = y
    self.dx = dx / length
    self.dy = dy / length
    self.source = source
    self.target = target
    self.energy = energy
    self.segment = None
    self.hits = []

  def advance(self, distance):
    if distance < 0:
      raise ValueError("distance: must not be negative")
    start_x, start_y = self.x, self.y
    self.x += self.dx * distance
    self.y += self.dy * distance
    while self.x < 0 or self.x > 1 or self.y < 0 or self.y > 1:
      if self.x < 0:
        self.x, self.dx = -self.x, -self.dx
      elif self.x > 1:
        self.x, self.dx = 2 - self.x, -self.dx
      if self.y < 0:
        self.y, self.dy = -self.y, -self.dy
      elif self.y > 1:
        self.y, self.dy = 2 - self.y, -self.dy
    self.segment = (start_x, start_y, self.x, self.y)

  def touches(self, perception):
    if self.segment is None or perception.energy <= 0:
      return False
    start_x, start_y, end_x, end_y = self.segment
    radius = perception.energy
    if math.hypot(start_x - perception.x, start_y - perception.y) <= radius:
      return False
    return distance_to_segment(perception.x, perception.y, start_x, start_y, end_x, end_y) <= radius

  def on_visit(self, perception):
    if self.touches(perception):
      self.hits.append(perception)

  def finish(self, distance):
    if distance < 0:
      raise ValueError("distance: must not be negative")
    transferred = 0.0
    for perception in self.hits:
      transferred += self.source.transfer(perception, self.target, self.energy)
    self.hits = []
    self.advance(distance)
    return transferred

def distance_to_segment(x, y, start_x, start_y, end_x, end_y):
  dx, dy = end_x - start_x, end_y - start_y
  length_squared = dx * dx + dy * dy
  along = 0.0 if length_squared == 0 else ((x - start_x) * dx + (y - start_y) * dy) / length_squared
  along = max(0.0, min(1.0, along))
  return math.hypot(x - (start_x + along * dx), y - (start_y + along * dy))
