def spring_force(distance, rest, reach):
  if reach <= 0:
    raise ValueError("reach: must be greater than 0")
  if rest < 0:
    raise ValueError("rest: must be at least 0")
  if distance <= 0 or distance >= reach:
    return 0.0
  taper = 1.0 - distance / reach
  force = taper * taper * (distance - rest)
  if rest < reach:
    force *= 27.0 * reach / (16.0 * (reach - rest))
  return force
