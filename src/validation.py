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
