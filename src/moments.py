class Moments:
  def __init__(self, scheduler):
    self.scheduler = scheduler
    self.counts = {}

  def current(self):
    return self.scheduler.moment

  def count(self, moment):
    return self.counts.get(moment, 0)

  def born(self, moment):
    self.counts[moment] = self.count(moment) + 1

  def died(self, moment):
    remaining = self.count(moment) - 1
    if remaining < 0:
      raise ValueError("moment: no perception left to die")
    if remaining:
      self.counts[moment] = remaining
    else:
      del self.counts[moment]
