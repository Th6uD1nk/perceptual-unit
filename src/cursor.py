import math

EPSILON = 1e-9
EDGE_OFFSET = 1e-6

class Cursor:
  def __init__(self, x, y, dx, dy, source, target, energy, step, cooldown, attraction, distance_power, impact):
    if not (0 <= x <= 1 and 0 <= y <= 1):
      raise ValueError("position: must be inside the plane")
    if energy <= 0:
      raise ValueError("energy: must be greater than 0")
    if step <= 0:
      raise ValueError("step: must be greater than 0")
    for name, value in (("attraction", attraction), ("distance_power", distance_power), ("impact", impact)):
      if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError(f"{name}: must be a number of at least 0")
    if isinstance(cooldown, bool) or not isinstance(cooldown, int) or cooldown < 0:
      raise ValueError("cooldown: must be an integer of at least 0")
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
    self.step = step
    self.cooldown = cooldown
    self.attraction = attraction
    self.distance_power = distance_power
    self.impact = impact
    self.force_x = 0.0
    self.force_y = 0.0
    self.scheduler = None
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

  @property
  def now(self):
    return self.scheduler.ticks if self.scheduler is not None else 0

  def on_visit(self, perception):
    if perception.read and self.now - perception.read_tick >= self.cooldown:
      perception.read = False
    if not perception.read and self.touches(perception):
      self.hits.append(perception)
    if not perception.read:
      self.attract(perception)

  def attract(self, perception):
    dx, dy = perception.x - self.x, perception.y - self.y
    distance = math.hypot(dx, dy)
    if perception.energy <= 0 or distance <= perception.energy:
      return
    pull = perception.energy / distance ** self.distance_power
    self.force_x += pull * dx / distance
    self.force_y += pull * dy / distance

  def deflect(self, perception, energy_before):
    nx, ny = self.x - perception.x, self.y - perception.y
    length = math.hypot(nx, ny)
    if length == 0:
      nx, ny = -self.dx, -self.dy
    else:
      nx, ny = nx / length, ny / length
    tx, ty = -ny, nx
    side = tx * self.force_x + ty * self.force_y
    if abs(side) < EPSILON:
      side = tx * self.dx + ty * self.dy
    if side < 0:
      tx, ty = -tx, -ty
    share = min(1.0, self.impact * energy_before / self.source.peak)
    dx = (1 - share) * self.dx + share * tx
    dy = (1 - share) * self.dy + share * ty
    length = math.hypot(dx, dy)
    if length > 0:
      self.dx, self.dy = dx / length, dy / length
    else:
      self.dx, self.dy = tx, ty
    on_plane = self.source.perceptions.get(perception.key) is perception
    radius = (perception.energy if on_plane else 0.0) + EDGE_OFFSET
    self.x = max(0.0, min(1.0, perception.x + nx * radius))
    self.y = max(0.0, min(1.0, perception.y + ny * radius))

  def turn(self):
    dx = self.dx + self.attraction * self.force_x
    dy = self.dy + self.attraction * self.force_y
    length = math.hypot(dx, dy)
    if length > 0:
      self.dx, self.dy = dx / length, dy / length
    self.force_x = 0.0
    self.force_y = 0.0

  def finish(self, distance):
    if distance < 0:
      raise ValueError("distance: must not be negative")
    transferred = 0.0
    for perception in self.hits:
      if self.source.perceptions.get(perception.key) is not perception:
        continue
      before = perception.energy
      transferred += self.source.transfer(perception, self.target, self.energy)
      perception.read = True
      perception.read_tick = self.now
      self.deflect(perception, before)
    self.hits = []
    self.turn()
    self.advance(distance)
    return transferred

  def start(self, scheduler):
    self.scheduler = scheduler
    scheduler.submit(self.run)

  def run(self):
    used, finished = self.source.visit(math.inf, self.on_visit)
    if finished:
      self.finish(self.step)
    self.scheduler.submit(self.run)

def distance_to_segment(x, y, start_x, start_y, end_x, end_y):
  dx, dy = end_x - start_x, end_y - start_y
  length_squared = dx * dx + dy * dy
  along = 0.0 if length_squared == 0 else ((x - start_x) * dx + (y - start_y) * dy) / length_squared
  along = max(0.0, min(1.0, along))
  return math.hypot(x - (start_x + along * dx), y - (start_y + along * dy))
