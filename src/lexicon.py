import collections

from transcription import token_hash

class Lexicon:
  def __init__(self, floor):
    self.floor = floor
    self.words = {}
    self.grams = {}
    self.index = collections.defaultdict(set)
    self.similarities = {}

  def add(self, word):
    if not isinstance(word, str) or not word:
      raise ValueError("word: must be a non-empty string")
    hash_ = token_hash(word)
    if hash_ in self.words:
      return hash_
    padded = "<" + word + ">"
    grams = {padded[index:index + 2] for index in range(len(padded) - 1)}
    shared = collections.Counter()
    for gram in grams:
      for other in self.index[gram]:
        shared[other] += 1
    mine = self.similarities.setdefault(hash_, {})
    for other, count in shared.items():
      score = 2.0 * count / (len(grams) + len(self.grams[other]))
      if score >= self.floor:
        mine[other] = score
        self.similarities[other][hash_] = score
    self.words[hash_] = word
    self.grams[hash_] = grams
    for gram in grams:
      self.index[gram].add(hash_)
    return hash_

  def word(self, hash_):
    return self.words.get(hash_)

  def similar(self, hash_):
    return dict(self.similarities.get(hash_, {}))
