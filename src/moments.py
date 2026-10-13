class Moments:
  def __init__(self, scheduler):
    self.scheduler = scheduler
    self.seen = scheduler.moment
    self.counts = {}
    self.recorded = {}

  def current(self):
    moment = self.scheduler.moment
    if moment != self.seen:
      self.seen = moment
      for old in [old for old in self.recorded if old < moment and not self.count(old)]:
        del self.recorded[old]
    return moment

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
      return
    del self.counts[moment]
    if moment < self.scheduler.moment:
      self.recorded.pop(moment, None)

  def record(self, hashes):
    event = list(hashes)
    entry = self.recorded.setdefault(self.current(), {"events": [], "contexts": {}})
    entry["events"].append(event)
    for index, middle in enumerate(event):
      left = event[index - 1] if index > 0 else None
      right = event[index + 1] if index + 1 < len(event) else None
      middles = entry["contexts"].setdefault((left, right), {})
      middles[middle] = middles.get(middle, 0) + 1
    return list(event)

  def events(self, moment):
    self.current()
    return [list(event) for event in self.recorded.get(moment, {"events": []})["events"]]

  def contexts(self, moment):
    self.current()
    return {neighbors: dict(middles) for neighbors, middles in self.recorded.get(moment, {"contexts": {}})["contexts"].items()}
