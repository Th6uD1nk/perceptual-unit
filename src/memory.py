import collections
import math

from lexicon import Lexicon
from spring import spring_force
from transcription import token_angle, token_position
from validation import validate_memory

MAPS = ("shape", "usage")

class Memory:
  def __init__(self, config):
    validate_memory(config)
    section = config["memory"]
    self.lexicon = Lexicon(section["floor"])
    self.threshold = section["threshold"]
    self.orbit = section["orbit"]
    self.window = section["window"]
    self.decay = section["decay"]
    self.reach = section["range"]
    self.rest = section["rest"]
    self.far = section["far"]
    self.base = section["base"]
    self.rate = section["rate"]
    self.recent = collections.deque(maxlen=section["recent"])
    self.counts = {}
    self.strengths = {}
    self.positions = {"shape": {}, "usage": {}}

  def add(self, word):
    hash_ = self.lexicon.add(word)
    if hash_ not in self.positions["usage"]:
      anchor = token_position(word)
      self.positions["usage"][hash_] = anchor
      self.positions["shape"][hash_] = self.birth_on_shape(word, hash_, anchor)
    return hash_

  def birth_on_shape(self, word, hash_, anchor):
    similar = self.lexicon.similar(hash_)
    if not similar:
      return anchor
    score, neighbor = max((score, other) for other, score in similar.items())
    if score < self.threshold:
      return anchor
    radius = self.orbit[0] + (1.0 - score) * self.orbit[1]
    angle = token_angle(word) * math.tau
    x, y = self.positions["shape"][neighbor]
    return (max(0.0, min(1.0, x + radius * math.cos(angle))), max(0.0, min(1.0, y + radius * math.sin(angle))))

  def observe(self, words):
    if not isinstance(words, list) or not words or any(not isinstance(word, str) or not word for word in words):
      raise ValueError("words: must be a non-empty list of non-empty strings")
    hashes = [self.add(word) for word in words]
    for hash_ in dict.fromkeys(hashes):
      self.counts[hash_] = self.count(hash_) + 1
    self.link(hashes)
    expression = self.express(hashes)
    self.relax_shape(hashes)
    self.recent.append(list(dict.fromkeys(hashes)))
    return hashes, expression

  def relax_shape(self, hashes):
    positions = self.positions["shape"]
    moved = {}
    for hash_ in dict.fromkeys(hashes):
      px, py = positions[hash_]
      similar = self.lexicon.similar(hash_)
      fx = fy = weight = 0.0
      for other, (ox, oy) in positions.items():
        dx, dy = ox - px, oy - py
        distance = math.hypot(dx, dy)
        if other == hash_ or distance == 0.0 or distance >= self.reach:
          continue
        score = similar.get(other, 0.0)
        affinity = score if score >= self.threshold else 0.0
        level = max(affinity, self.base)
        rest = self.far - (self.far - self.rest) * affinity
        pull = level * spring_force(distance, rest, self.reach) / distance
        fx += pull * dx
        fy += pull * dy
        weight += level * (1.0 - distance / self.reach)
      if weight > 0.0:
        step = self.rate / self.counts[hash_] / weight
        moved[hash_] = (max(0.0, min(1.0, px + step * fx)), max(0.0, min(1.0, py + step * fy)))
    positions.update(moved)

  def pull(self, perception, plane):
    similar = self.lexicon.similar(perception.hash)

    def terms(other):
      score = similar.get(other.hash, 0.0)
      affinity = score if score >= self.threshold else 0.0
      return affinity, max(affinity, self.base), 1.0

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

  def express(self, hashes):
    energies = {}
    for age, flow in enumerate(reversed(self.recent), 1):
      share = self.decay ** age
      for hash_ in flow:
        if energies.get(hash_, 0.0) < share:
          energies[hash_] = share
    for hash_ in hashes:
      energies[hash_] = 1.0
    return energies

  def link(self, hashes):
    made = set()
    for first in range(len(hashes)):
      stop = len(hashes) if self.window == 0 else min(len(hashes), first + 1 + self.window)
      for second in range(first + 1, stop):
        if hashes[first] != hashes[second]:
          made.add(tuple(sorted((hashes[first], hashes[second]))))
    for pair in made:
      self.strengths[pair] = self.strengths.get(pair, 0.0) + 1.0

  def count(self, hash_):
    return self.counts.get(hash_, 0)

  def strength(self, first, second):
    return self.strengths.get(tuple(sorted((first, second))), 0.0)

  def position(self, hash_, kind):
    if kind not in MAPS:
      raise ValueError("kind: must be 'shape' or 'usage'")
    return self.positions[kind].get(hash_)
