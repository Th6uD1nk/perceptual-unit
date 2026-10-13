import math

from lexicon import Lexicon
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

  def position(self, hash_, kind):
    if kind not in MAPS:
      raise ValueError("kind: must be 'shape' or 'usage'")
    return self.positions[kind].get(hash_)
