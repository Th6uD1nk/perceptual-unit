import math
import unittest

import support
from memory import Memory
from transcription import token_angle, token_hash, token_position

CONFIG = {"memory": {"floor": 0.3, "threshold": 0.5, "orbit": [0.05, 0.1], "window": 2, "recent": 3, "decay": 0.3}}

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
    memory = Memory({"memory": {"floor": 0.3, "threshold": 0.9, "orbit": [0.05, 0.1], "window": 2, "recent": 3, "decay": 0.3}})
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
    memory = Memory({"memory": {"floor": 0.3, "threshold": 0.5, "orbit": [0.9, 0.9], "window": 2, "recent": 3, "decay": 0.3}})
    memory.add(self.base)
    for word in (self.base + "s", self.base + "es", self.base + "ed", self.base + "ing"):
      x, y = memory.position(memory.add(word), "shape")
      self.assertTrue(0.0 <= x <= 1.0 and 0.0 <= y <= 1.0)

class ObserveTest(unittest.TestCase):
  def memory(self, window=2, recent=3, decay=0.3):
    return Memory({"memory": dict(CONFIG["memory"], window=window, recent=recent, decay=decay)})

  def test_a_word_repeated_in_a_flow_counts_once_and_counts_again_in_the_next_flow(self):
    memory = self.memory()
    memory.observe(["a", "b", "a"])
    self.assertEqual((memory.count(token_hash("a")), memory.count(token_hash("b"))), (1, 1))
    memory.observe(["a"])
    self.assertEqual(memory.count(token_hash("a")), 2)

  def test_an_unknown_word_counts_zero(self):
    self.assertEqual(self.memory().count("unknown"), 0)

  def test_the_flow_gives_back_the_hashes_in_order_and_the_words_enter_the_lexicon(self):
    memory = self.memory()
    hashes, expression = memory.observe(["a", "b", "a"])
    self.assertEqual(hashes, [token_hash("a"), token_hash("b"), token_hash("a")])
    self.assertEqual(memory.lexicon.word(token_hash("b")), "b")

  def test_the_words_within_the_window_are_linked_and_the_others_are_not(self):
    memory = self.memory(window=2)
    memory.observe(["a", "b", "c", "d"])
    strengths = {pair: memory.strength(token_hash(pair[0]), token_hash(pair[1])) for pair in ("ab", "ac", "bc", "bd", "cd", "ad")}
    self.assertEqual(strengths, {"ab": 1.0, "ac": 1.0, "bc": 1.0, "bd": 1.0, "cd": 1.0, "ad": 0.0})

  def test_a_window_of_zero_links_all_the_words_of_the_flow(self):
    memory = self.memory(window=0)
    memory.observe(["a", "b", "c", "d"])
    self.assertEqual(memory.strength(token_hash("a"), token_hash("d")), 1.0)

  def test_a_pair_that_appears_several_times_in_a_flow_is_linked_once(self):
    memory = self.memory()
    memory.observe(["a", "b", "a", "b"])
    self.assertEqual(memory.strength(token_hash("a"), token_hash("b")), 1.0)

  def test_the_expression_of_a_first_flow_holds_its_words_at_one(self):
    _, expression = self.memory().observe(["a", "b"])
    self.assertEqual(expression, {token_hash("a"): 1.0, token_hash("b"): 1.0})

  def test_the_words_of_the_previous_flow_are_expressed_at_the_decay_and_those_of_the_current_flow_at_one(self):
    memory = self.memory()
    memory.observe(["a", "b"])
    _, expression = memory.observe(["b", "c"])
    self.assertEqual(expression, {token_hash("a"): 0.3, token_hash("b"): 1.0, token_hash("c"): 1.0})

  def test_a_word_of_several_older_flows_keeps_the_strongest_expression(self):
    memory = self.memory()
    memory.observe(["a"])
    memory.observe(["a"])
    _, expression = memory.observe(["x"])
    self.assertAlmostEqual(expression[token_hash("a")], 0.3)

  def test_a_flow_that_is_too_old_is_forgotten(self):
    memory = self.memory(recent=2)
    for word in ("a", "b", "c"):
      memory.observe([word])
    _, expression = memory.observe(["d"])
    self.assertEqual(sorted(expression), sorted(token_hash(word) for word in ("b", "c", "d")))
    self.assertAlmostEqual(expression[token_hash("c")], 0.3)
    self.assertAlmostEqual(expression[token_hash("b")], 0.09)

  def test_the_expression_given_back_is_independent_of_what_the_memory_keeps(self):
    memory = self.memory()
    _, expression = memory.observe(["a"])
    expression[token_hash("a")] = 9.0
    _, next_expression = memory.observe(["b"])
    self.assertAlmostEqual(next_expression[token_hash("a")], 0.3)

  def test_a_word_is_never_linked_to_itself(self):
    memory = self.memory()
    memory.observe(["a", "a"])
    self.assertEqual(memory.strengths, {})

  def test_the_link_is_the_same_in_both_directions_and_adds_up_from_flow_to_flow(self):
    memory = self.memory()
    memory.observe(["a", "b"])
    memory.observe(["b", "a"])
    self.assertEqual(memory.strength(token_hash("a"), token_hash("b")), 2.0)
    self.assertEqual(memory.strength(token_hash("b"), token_hash("a")), 2.0)

  def test_an_invalid_flow_is_refused_and_changes_nothing(self):
    memory = self.memory()
    for words in ([], "text", ["a", ""], ["a", 3]):
      with self.assertRaises(ValueError, msg=repr(words)):
        memory.observe(words)
    self.assertEqual((memory.counts, memory.strengths, memory.lexicon.words), ({}, {}, {}))

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

  def test_the_window_is_required(self):
    config = self.with_changes()
    del config["memory"]["window"]
    self.assertIn("config.memory.window", self.rejected(config))

  def test_the_window_must_be_an_integer_of_at_least_zero(self):
    for window in (-1, 1.5, "2", None, True):
      self.assertIn("config.memory.window", self.rejected(self.with_changes(window=window)), repr(window))

  def test_a_window_of_zero_is_accepted(self):
    Memory(self.with_changes(window=0))

  def test_recent_and_the_decay_are_required(self):
    for key in ("recent", "decay"):
      config = self.with_changes()
      del config["memory"][key]
      self.assertIn(f"config.memory.{key}", self.rejected(config), key)

  def test_recent_must_be_an_integer_of_at_least_one(self):
    for recent in (0, -1, 1.5, "3", None, True):
      self.assertIn("config.memory.recent", self.rejected(self.with_changes(recent=recent)), repr(recent))

  def test_the_decay_must_be_a_number_between_zero_and_one_and_the_limits_are_accepted(self):
    for decay in (-0.1, 1.1, "0.3", None, True):
      self.assertIn("config.memory.decay", self.rejected(self.with_changes(decay=decay)), repr(decay))
    Memory(self.with_changes(decay=0))
    Memory(self.with_changes(decay=1))

  def test_the_orbit_is_required(self):
    config = self.with_changes()
    del config["memory"]["orbit"]
    self.assertIn("config.memory.orbit", self.rejected(config))

  def test_the_orbit_must_be_a_list_of_two_numbers_of_at_least_zero(self):
    for orbit in ([0.05], [0.05, 0.1, 0.2], [-0.1, 0.1], ["a", 0.1], [0.05, True], 0.05, None):
      self.assertIn("config.memory.orbit", self.rejected(self.with_changes(orbit=orbit)), repr(orbit))

if __name__ == "__main__":
  unittest.main()
