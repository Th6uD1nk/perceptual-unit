import math
import unittest

import support
from memory import Memory
from transcription import token_angle, token_hash, token_position

CONFIG = {"memory": {"floor": 0.3, "threshold": 0.5, "orbit": [0.05, 0.1]}}

class AddTest(unittest.TestCase):
  def setUp(self):
    self.memory = Memory(CONFIG)

  def test_a_new_word_is_born_at_its_anchor_on_both_maps(self):
    hash_ = self.memory.add("house")
    self.assertEqual(hash_, token_hash("house"))
    self.assertEqual(self.memory.position(hash_, "shape"), token_position("house"))
    self.assertEqual(self.memory.position(hash_, "usage"), token_position("house"))

  def test_the_word_is_known_by_the_lexicon_of_the_memory(self):
    hash_ = self.memory.add("house")
    self.assertEqual(self.memory.lexicon.word(hash_), "house")

  def test_a_known_word_keeps_the_positions_it_has(self):
    hash_ = self.memory.add("house")
    self.memory.positions["usage"][hash_] = (0.1, 0.2)
    self.memory.positions["shape"][hash_] = (0.3, 0.4)
    self.assertEqual(self.memory.add("house"), hash_)
    self.assertEqual(self.memory.position(hash_, "usage"), (0.1, 0.2))
    self.assertEqual(self.memory.position(hash_, "shape"), (0.3, 0.4))

def central_word():
  for word in ("cat", "dog", "pig", "cow", "hen", "bee", "fox", "owl", "ant", "ape"):
    x, y = token_position(word)
    if 0.3 < x < 0.7 and 0.3 < y < 0.7:
      return word
  raise AssertionError("no central word")

class OrbitTest(unittest.TestCase):
  def setUp(self):
    self.memory = Memory(CONFIG)
    self.base = central_word()
    self.base_hash = self.memory.add(self.base)
    self.similar = self.base + "s"
    self.similar_hash = self.memory.add(self.similar)

  def test_a_similar_word_is_born_on_an_orbit_around_its_closest_neighbor_on_the_shape_map(self):
    score = self.memory.lexicon.similar(self.similar_hash)[self.base_hash]
    expected = 0.05 + (1.0 - score) * 0.1
    ax, ay = self.memory.position(self.base_hash, "shape")
    bx, by = self.memory.position(self.similar_hash, "shape")
    self.assertAlmostEqual(math.hypot(bx - ax, by - ay), expected)

  def test_the_orbit_angle_comes_from_the_hash_of_the_word(self):
    ax, ay = self.memory.position(self.base_hash, "shape")
    bx, by = self.memory.position(self.similar_hash, "shape")
    self.assertAlmostEqual(math.atan2(by - ay, bx - ax) % math.tau, token_angle(self.similar) * math.tau)

  def test_the_usage_map_is_left_at_the_anchor(self):
    self.assertEqual(self.memory.position(self.similar_hash, "usage"), token_position(self.similar))

  def test_a_word_below_the_threshold_is_born_at_its_anchor_on_the_shape_map(self):
    memory = Memory({"memory": {"floor": 0.3, "threshold": 0.9, "orbit": [0.05, 0.1]}})
    memory.add(self.base)
    hash_ = memory.add(self.similar)
    self.assertEqual(memory.position(hash_, "shape"), token_position(self.similar))

  def test_the_most_similar_neighbor_is_the_one_the_word_is_born_around(self):
    memory = Memory(CONFIG)
    far = memory.add(self.base + "x" + self.base)
    near = memory.add(self.base)
    hash_ = memory.add(self.similar)
    scores = memory.lexicon.similar(hash_)
    self.assertGreater(scores[near], scores.get(far, 0.0))
    ax, ay = memory.position(near, "shape")
    bx, by = memory.position(hash_, "shape")
    self.assertAlmostEqual(math.hypot(bx - ax, by - ay), 0.05 + (1.0 - scores[near]) * 0.1)

  def test_the_shape_position_stays_in_the_plane_when_the_orbit_overflows(self):
    memory = Memory({"memory": {"floor": 0.3, "threshold": 0.5, "orbit": [0.9, 0.9]}})
    memory.add(self.base)
    for word in (self.base + "s", self.base + "es", self.base + "ed", self.base + "ing"):
      x, y = memory.position(memory.add(word), "shape")
      self.assertTrue(0.0 <= x <= 1.0 and 0.0 <= y <= 1.0)

class PositionTest(unittest.TestCase):
  def test_an_unknown_hash_has_no_position(self):
    self.assertIsNone(Memory(CONFIG).position("unknown", "usage"))

  def test_an_unknown_map_is_refused(self):
    with self.assertRaises(ValueError):
      Memory(CONFIG).position(token_hash("house"), "other")

class ConfigTest(unittest.TestCase):
  def rejected(self, config):
    with self.assertRaises(ValueError) as caught:
      Memory(config)
    return str(caught.exception)

  def test_a_config_must_be_an_object(self):
    self.assertIn("config:", self.rejected([]))

  def test_the_memory_section_is_required_and_must_be_an_object(self):
    self.assertIn("config.memory", self.rejected({}))
    self.assertIn("config.memory", self.rejected({"memory": 0.3}))

  def test_the_floor_is_required(self):
    self.assertIn("config.memory.floor", self.rejected({"memory": {}}))

  def with_changes(self, **changes):
    return {"memory": dict(CONFIG["memory"], **changes)}

  def test_the_floor_must_be_a_number_greater_than_zero_and_at_most_one(self):
    for floor in (0, -0.1, 1.1, "0.3", None, True):
      self.assertIn("config.memory.floor", self.rejected(self.with_changes(floor=floor)), repr(floor))

  def test_the_threshold_is_required(self):
    config = self.with_changes()
    del config["memory"]["threshold"]
    self.assertIn("config.memory.threshold", self.rejected(config))

  def test_the_threshold_must_be_a_number_between_the_floor_and_one(self):
    for threshold in (0.29, 1.1, "0.5", None, True):
      self.assertIn("config.memory.threshold", self.rejected(self.with_changes(threshold=threshold)), repr(threshold))

  def test_the_orbit_is_required(self):
    config = self.with_changes()
    del config["memory"]["orbit"]
    self.assertIn("config.memory.orbit", self.rejected(config))

  def test_the_orbit_must_be_a_list_of_two_numbers_of_at_least_zero(self):
    for orbit in ([0.05], [0.05, 0.1, 0.2], [-0.1, 0.1], ["a", 0.1], [0.05, True], 0.05, None):
      self.assertIn("config.memory.orbit", self.rejected(self.with_changes(orbit=orbit)), repr(orbit))

if __name__ == "__main__":
  unittest.main()
