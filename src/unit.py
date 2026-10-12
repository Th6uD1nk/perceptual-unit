import copy

from plane import Plane
from validation import validate_config

class Unit:
  def __init__(self, config):
    validate_config(config)
    self.config = copy.deepcopy(config)
    self.planes = {entry["uid"]: Plane(entry) for entry in self.config["planes"]}
