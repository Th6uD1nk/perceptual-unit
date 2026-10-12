import math

class Cursor:
  def __init__(self, x, y, dx, dy):
    if not (0 <= x <= 1 and 0 <= y <= 1):
      raise ValueError("position: must be inside the plane")
    length = math.hypot(dx, dy)
    if length == 0:
      raise ValueError("direction: must not be null")
    self.x = x
    self.y = y
    self.dx = dx / length
    self.dy = dy / length
    self.segment = None

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
