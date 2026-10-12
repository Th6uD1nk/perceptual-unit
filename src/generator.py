MASK_64 = (1 << 64) - 1

class Generator:
  def __init__(self, seed):
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
      raise ValueError("seed: must be an integer of at least 0")
    self.state = seed & MASK_64

  def next(self):
    self.state = (self.state + 0x9E3779B97F4A7C15) & MASK_64
    value = self.state
    value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & MASK_64
    value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & MASK_64
    return value ^ (value >> 31)

  def random(self):
    return (self.next() >> 11) * (1.0 / 9007199254740992.0)

  def draw(self, count):
    if count < 1:
      raise ValueError("count: must be at least 1")
    return int(self.random() * count)
