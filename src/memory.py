from lexicon import Lexicon
from transcription import token_position
from validation import validate_memory

MAPS = ("shape", "usage")

class Memory:
  def __init__(self, config):
    validate_memory(config)
    self.lexicon = Lexicon(config["memory"]["floor"])
    self.positions = {"shape": {}, "usage": {}}

  def add(self, word):
    hash_ = self.lexicon.add(word)
    if hash_ not in self.positions["usage"]:
      anchor = token_position(word)
      self.positions["shape"][hash_] = anchor
      self.positions["usage"][hash_] = anchor
    return hash_

  def position(self, hash_, kind):
    if kind not in MAPS:
      raise ValueError("kind: must be 'shape' or 'usage'")
    return self.positions[kind].get(hash_)
