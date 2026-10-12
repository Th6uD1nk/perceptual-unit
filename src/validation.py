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

def validate_clock(config):
  if not isinstance(config, dict):
    fail("config", "must be an object")
  if "clock" not in config:
    fail("config.clock", "missing")
  clock = config["clock"]
  if not isinstance(clock, dict):
    fail("config.clock", "must be an object")
  if "tick" not in clock:
    fail("config.clock.tick", "missing")
  tick = clock["tick"]
  if isinstance(tick, bool) or not isinstance(tick, (int, float)) or tick < MIN_TICK_MS:
    fail("config.clock.tick", f"must be a number of at least {MIN_TICK_MS}")
