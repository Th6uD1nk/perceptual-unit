MIN_TICK_MS = 0.001

def fail(path, message):
  raise ValueError(f"{path}: {message}")

def validate_plane(entry, path, known):
  if not isinstance(entry, dict):
    fail(path, "must be an object")
  if "uid" not in entry:
    fail(f"{path}.uid", "missing")
  uid = entry["uid"]
  if not isinstance(uid, str) or not uid:
    fail(f"{path}.uid", "must be a non-empty string")
  if uid in known:
    fail(f"{path}.uid", f"{uid!r} is already used by another plane")
  known.add(uid)
  if "peak" not in entry:
    fail(f"{path}.peak", "missing")
  peak = entry["peak"]
  if isinstance(peak, bool) or not isinstance(peak, (int, float)) or peak <= 0:
    fail(f"{path}.peak", "must be a number greater than 0")
  if "relax" not in entry:
    fail(f"{path}.relax", "missing")
  if entry["relax"] not in (None, "shape", "usage"):
    fail(f"{path}.relax", "must be null, 'shape' or 'usage'")

def validate_transfers(entry, path, known):
  if "transfers" not in entry:
    fail(f"{path}.transfers", "missing")
  transfers = entry["transfers"]
  if not isinstance(transfers, list):
    fail(f"{path}.transfers", "must be a list")
  for index, transfer in enumerate(transfers):
    where = f"{path}.transfers[{index}]"
    if not isinstance(transfer, dict):
      fail(where, "must be an object")
    if "target" not in transfer:
      fail(f"{where}.target", "missing")
    target = transfer["target"]
    if target is not None and (not isinstance(target, str) or target not in known):
      fail(f"{where}.target", "must be null or the uid of an existing plane")
    if target == entry["uid"]:
      fail(f"{where}.target", "must be another plane")
    validate_cursor(transfer, where)

def validate_config(config):
  if not isinstance(config, dict):
    fail("config", "must be an object")
  if "planes" not in config:
    fail("config.planes", "missing")
  planes = config["planes"]
  if not isinstance(planes, list) or not planes:
    fail("config.planes", "must be a non-empty list")
  known = set()
  for index, entry in enumerate(planes):
    validate_plane(entry, f"config.planes[{index}]", known)
  for index, entry in enumerate(planes):
    validate_transfers(entry, f"config.planes[{index}]", known)
  validate_scheduler(config)
  validate_random(config)
  validate_memory(config)

def validate_scheduler(config):
  if not isinstance(config, dict):
    fail("config", "must be an object")
  if "scheduler" not in config:
    fail("config.scheduler", "missing")
  section = config["scheduler"]
  if not isinstance(section, dict):
    fail("config.scheduler", "must be an object")
  if "tick" not in section:
    fail("config.scheduler.tick", "missing")
  tick = section["tick"]
  if isinstance(tick, bool) or not isinstance(tick, (int, float)) or tick < MIN_TICK_MS:
    fail("config.scheduler.tick", f"must be a number of at least {MIN_TICK_MS}")
  if "budget" not in section:
    fail("config.scheduler.budget", "missing")
  budget = section["budget"]
  if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0:
    fail("config.scheduler.budget", "must be an integer of at least 0")
  if "moment" not in section:
    fail("config.scheduler.moment", "missing")
  moment = section["moment"]
  if isinstance(moment, bool) or not isinstance(moment, int) or moment < 1:
    fail("config.scheduler.moment", "must be an integer of at least 1")

def validate_random(config):
  if "random" not in config:
    fail("config.random", "missing")
  section = config["random"]
  if not isinstance(section, dict):
    fail("config.random", "must be an object")
  if "seed" not in section:
    fail("config.random.seed", "missing")
  seed = section["seed"]
  if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
    fail("config.random.seed", "must be an integer of at least 0")

def validate_memory(config):
  if not isinstance(config, dict):
    fail("config", "must be an object")
  if "memory" not in config:
    fail("config.memory", "missing")
  section = config["memory"]
  if not isinstance(section, dict):
    fail("config.memory", "must be an object")
  if "floor" not in section:
    fail("config.memory.floor", "missing")
  floor = section["floor"]
  if isinstance(floor, bool) or not isinstance(floor, (int, float)) or not 0 < floor <= 1:
    fail("config.memory.floor", "must be a number greater than 0 and at most 1")
  if "threshold" not in section:
    fail("config.memory.threshold", "missing")
  threshold = section["threshold"]
  if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not floor <= threshold <= 1:
    fail("config.memory.threshold", "must be a number at least equal to the floor and at most 1")
  if "orbit" not in section:
    fail("config.memory.orbit", "missing")
  orbit = section["orbit"]
  if not isinstance(orbit, list) or len(orbit) != 2 or any(isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0 for value in orbit):
    fail("config.memory.orbit", "must be a list of two numbers of at least 0")
  if "window" not in section:
    fail("config.memory.window", "missing")
  window = section["window"]
  if isinstance(window, bool) or not isinstance(window, int) or window < 0:
    fail("config.memory.window", "must be an integer of at least 0")
  for key in ("range", "rest", "far", "base", "rate", "coexpression", "kappa", "amplify"):
    if key not in section:
      fail(f"config.memory.{key}", "missing")
    value = section[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
      fail(f"config.memory.{key}", "must be a number")
  if section["range"] <= 0:
    fail("config.memory.range", "must be greater than 0")
  if section["rest"] < 0:
    fail("config.memory.rest", "must be at least 0")
  if section["far"] < section["rest"]:
    fail("config.memory.far", "must be at least the rest")
  if section["base"] < 0:
    fail("config.memory.base", "must be at least 0")
  if section["rate"] <= 0:
    fail("config.memory.rate", "must be greater than 0")
  if section["coexpression"] < 0:
    fail("config.memory.coexpression", "must be at least 0")
  if section["kappa"] <= 0:
    fail("config.memory.kappa", "must be greater than 0")
  if section["amplify"] < 0:
    fail("config.memory.amplify", "must be at least 0")

def validate_cursor(config, path="config"):
  if not isinstance(config, dict):
    fail(path, "must be an object")
  for key, strict in (("energy", True), ("step", True), ("attraction", False), ("distance_power", False), ("impact", False)):
    if key not in config:
      fail(f"{path}.{key}", "missing")
    value = config[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or (value <= 0 if strict else value < 0):
      fail(f"{path}.{key}", "must be a number greater than 0" if strict else "must be a number of at least 0")
  for key, minimum in (("cooldown", 0), ("cycle", 1)):
    if key not in config:
      fail(f"{path}.{key}", "missing")
    value = config[key]
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
      fail(f"{path}.{key}", f"must be an integer of at least {minimum}")
