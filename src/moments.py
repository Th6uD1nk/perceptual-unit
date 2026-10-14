class Moments:
  def __init__(self, scheduler, window):
    self.scheduler = scheduler
    self.window = window
    self.seen = scheduler.moment
    self.counts = {}
    self.recorded = {}
    self.totals = {}
    self.link_totals = {}

  @property
  def ticks(self):
    return self.scheduler.ticks

  def current(self):
    moment = self.scheduler.moment
    if moment != self.seen:
      self.seen = moment
      for old in [old for old in self.recorded if old < moment and not self.count(old)]:
        self.release(old)
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
      self.release(moment)

  def release(self, moment):
    entry = self.recorded.pop(moment, None)
    if entry is None:
      return
    for neighbors, middles in entry["contexts"].items():
      total = self.totals[neighbors]
      for middle, number in middles.items():
        total[middle] -= number
        if not total[middle]:
          del total[middle]
      if not total:
        del self.totals[neighbors]
    for pair, number in entry["links"].items():
      self.link_totals[pair] -= number
      if not self.link_totals[pair]:
        del self.link_totals[pair]

  def record(self, hashes):
    event = list(hashes)
    entry = self.recorded.setdefault(self.current(), {"events": [], "contexts": {}, "links": {}})
    entry["events"].append(event)
    for index, middle in enumerate(event):
      left = event[index - 1] if index > 0 else None
      right = event[index + 1] if index + 1 < len(event) else None
      middles = entry["contexts"].setdefault((left, right), {})
      middles[middle] = middles.get(middle, 0) + 1
      total = self.totals.setdefault((left, right), {})
      total[middle] = total.get(middle, 0) + 1
    made = set()
    for first in range(len(event)):
      stop = len(event) if self.window == 0 else min(len(event), first + 1 + self.window)
      for second in range(first + 1, stop):
        if event[first] != event[second]:
          made.add(tuple(sorted((event[first], event[second]))))
    for pair in made:
      entry["links"][pair] = entry["links"].get(pair, 0) + 1
      self.link_totals[pair] = self.link_totals.get(pair, 0) + 1
    return list(event)

  def link(self, first, second):
    return self.link_totals.get(tuple(sorted((first, second))), 0)

  def links_of(self, moment):
    self.current()
    return dict(self.recorded.get(moment, {"links": {}})["links"])

  def events(self, moment):
    self.current()
    return [list(event) for event in self.recorded.get(moment, {"events": []})["events"]]

  def contexts(self, moment):
    self.current()
    return {neighbors: dict(middles) for neighbors, middles in self.recorded.get(moment, {"contexts": {}})["contexts"].items()}

  def between(self, left, right):
    return dict(self.totals.get((left, right), {}))
