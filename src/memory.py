import math

from lexicon import Lexicon
from spring import spring_force
from transcription import token_angle, token_position
from validation import validate_memory

class Memory:
  def __init__(self, config):
    validate_memory(config)
    section = config["memory"]
    self.lexicon = Lexicon(section["floor"])
    self.threshold = section["threshold"]
    self.orbit = section["orbit"]
    self.reach = section["range"]
    self.rest = section["rest"]
    self.far = section["far"]
    self.base = section["base"]
    self.rate = section["rate"]
    self.coexpression = section["coexpression"]
    self.kappa = section["kappa"]
    self.amplify = section["amplify"]

  def birth(self, word, hash_, plane):
    own = plane.living(hash_)
    if own:
      strongest = max(own, key=lambda perception: perception.energy)
      return strongest.x, strongest.y
    best = None
    for other, score in self.lexicon.similar(hash_).items():
      if score < self.threshold:
        continue
      for perception in plane.living(other):
        if best is None or (score, perception.energy) > (best[0], best[1].energy):
          best = (score, perception)
    if best is None:
      return token_position(word)
    score, neighbor = best
    radius = self.orbit[0] + (1.0 - score) * self.orbit[1]
    angle = token_angle(word) * math.tau
    return (max(0.0, min(1.0, neighbor.x + radius * math.cos(angle))), max(0.0, min(1.0, neighbor.y + radius * math.sin(angle))))

  def pull(self, perception, plane):
    similar = self.lexicon.similar(perception.hash)

    def terms(other):
      score = similar.get(other.hash, 0.0)
      affinity = score if score >= self.threshold else 0.0
      return affinity, max(affinity, self.base), 1.0

    return self.spring_pull(perception, plane, terms)

  def pull_usage(self, perception, plane, moments):
    links = moments.links_of(perception.moment)

    def terms(other):
      link = 1.0 - math.exp(-links.get(tuple(sorted((perception.hash, other.hash))), 0) / self.kappa)
      expression = other.energy / plane.peak
      affinity = min(1.0, max(self.coexpression * expression, link))
      return affinity, max(expression, self.base), 1.0 + self.amplify * link

    return self.spring_pull(perception, plane, terms)

  def spring_pull(self, perception, plane, terms):
    neighbors = [other for other in plane.of_moment(perception.moment) if other is not perception]
    cost = max(1, len(neighbors))
    fx = fy = weight = 0.0
    for other in neighbors:
      dx, dy = other.x - perception.x, other.y - perception.y
      distance = math.hypot(dx, dy)
      if distance == 0.0 or distance >= self.reach:
        continue
      affinity, level, boost = terms(other)
      rest = self.far - (self.far - self.rest) * affinity
      force = level * boost * spring_force(distance, rest, self.reach) / distance
      fx += force * dx
      fy += force * dy
      weight += level * (1.0 - distance / self.reach)
    if weight <= 0.0:
      return perception.x, perception.y, cost
    step = self.rate / (perception.energy / plane.peak * weight)
    dx, dy = step * fx, step * fy
    length = math.hypot(dx, dy)
    if length > self.reach:
      dx, dy = dx * self.reach / length, dy * self.reach / length
    return max(0.0, min(1.0, perception.x + dx)), max(0.0, min(1.0, perception.y + dy)), cost
