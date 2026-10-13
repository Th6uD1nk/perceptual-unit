class Moments:
  def __init__(self, scheduler):
    self.scheduler = scheduler

  def current(self):
    return self.scheduler.moment
