import math
import unittest
from types import SimpleNamespace

import support
from memory import Memory
from moments import Moments
from plane import Plane
from transcription import token_angle, token_hash, token_position

BASE = {"floor": 0.3, "threshold": 0.5, "orbit": [0.05, 0.1], "window": 2, "recent": 3, "decay": 0.3, "range": 0.5, "rest": 0.03, "far": 0.25, "base": 0.2, "rate": 1.0, "coexpression": 1.0, "kappa": 1.0, "amplify": 2.0}

def config(**changes):
  return {"memory": dict(BASE, **changes)}

CONFIG = config()

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
    memory = Memory(config(threshold=0.9))
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
    memory = Memory(config(orbit=[0.9, 0.9]))
    memory.add(self.base)
    for word in (self.base + "s", self.base + "es", self.base + "ed", self.base + "ing"):
      x, y = memory.position(memory.add(word), "shape")
      self.assertTrue(0.0 <= x <= 1.0 and 0.0 <= y <= 1.0)

class BirthTest(unittest.TestCase):
  def setUp(self):
    self.memory = Memory(CONFIG)
    self.clock = SimpleNamespace(moment=0)
    self.plane = Plane({"uid": "A", "peak": 4.0}, Moments(self.clock, 2))
    self.base = central_word()
    self.similar = self.base + "s"

  def live(self, word, x, y, energy=1.0, moment=0):
    self.clock.moment = moment
    self.plane.receive(self.memory.add(word), x, y, energy)

  def birth(self, word):
    return self.memory.birth(word, self.memory.add(word), self.plane)

  def test_a_word_without_any_living_perception_is_born_at_its_anchor(self):
    self.assertEqual(self.birth(self.similar), token_position(self.similar))

  def test_a_similar_word_that_is_only_in_the_lexicon_does_not_attract_the_birth(self):
    self.memory.add(self.base)
    self.assertEqual(self.birth(self.similar), token_position(self.similar))

  def test_a_word_is_born_on_the_orbit_of_a_living_similar_perception(self):
    self.live(self.base, 0.4, 0.4)
    score = self.memory.lexicon.similar(self.memory.add(self.similar))[self.memory.add(self.base)]
    x, y = self.birth(self.similar)
    self.assertAlmostEqual(math.hypot(x - 0.4, y - 0.4), 0.05 + (1.0 - score) * 0.1)
    self.assertAlmostEqual(math.atan2(y - 0.4, x - 0.4) % math.tau, token_angle(self.similar) * math.tau)

  def test_a_living_similar_perception_of_an_older_moment_counts(self):
    self.live(self.base, 0.4, 0.4, moment=0)
    self.clock.moment = 1
    x, y = self.birth(self.similar)
    self.assertLess(math.hypot(x - 0.4, y - 0.4), 0.16)

  def test_a_word_below_the_threshold_is_born_at_its_anchor(self):
    memory = Memory(config(threshold=0.99))
    self.memory = memory
    self.live(self.base, 0.4, 0.4)
    self.assertEqual(self.birth(self.similar), token_position(self.similar))

  def test_the_most_similar_living_word_is_the_one_it_is_born_around(self):
    far = self.base + "x" + self.base
    self.live(far, 0.8, 0.8)
    self.live(self.base, 0.4, 0.4)
    x, y = self.birth(self.similar)
    self.assertLess(math.hypot(x - 0.4, y - 0.4), 0.16)

  def test_the_strongest_living_perception_of_the_neighbor_is_chosen(self):
    self.live(self.base, 0.4, 0.4, energy=1.0)
    self.live(self.base, 0.2, 0.2, energy=2.0)
    x, y = self.birth(self.similar)
    self.assertLess(math.hypot(x - 0.2, y - 0.2), 0.16)

  def test_a_word_that_is_already_living_is_born_at_its_strongest_perception(self):
    self.live(self.similar, 0.6, 0.6, energy=1.0)
    self.live(self.similar, 0.7, 0.7, energy=2.0)
    self.live(self.base, 0.4, 0.4)
    self.assertEqual(self.birth(self.similar), (0.7, 0.7))

  def test_the_position_stays_in_the_plane_when_the_orbit_overflows(self):
    self.memory = Memory(config(orbit=[0.9, 0.9]))
    self.live(self.base, 0.99, 0.99)
    for word in (self.base + "s", self.base + "es", self.base + "ed"):
      x, y = self.birth(word)
      self.assertTrue(0.0 <= x <= 1.0 and 0.0 <= y <= 1.0)

  def test_nothing_is_modified_by_a_birth(self):
    self.live(self.base, 0.4, 0.4)
    before = {key: (p.x, p.y, p.energy) for key, p in self.plane.perceptions.items()}
    self.birth(self.similar)
    self.assertEqual(before, {key: (p.x, p.y, p.energy) for key, p in self.plane.perceptions.items()})

class ObserveTest(unittest.TestCase):
  def memory(self, window=2, recent=3, decay=0.3):
    return Memory(config(window=window, recent=recent, decay=decay))

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

class RelaxTest(unittest.TestCase):
  def setUp(self):
    self.memory = Memory(CONFIG)
    self.cat = self.memory.add("cat")
    self.cats = self.memory.add("cats")
    self.dog = self.memory.add("dog")
    self.place(self.memory, cat=(0.02, 0.02), cats=(0.98, 0.98), dog=(0.02, 0.98))

  def place(self, memory, **positions):
    for name, position in positions.items():
      memory.positions["shape"][token_hash(name)] = position

  def distance(self, memory, first, second):
    ax, ay = memory.position(token_hash(first), "shape")
    bx, by = memory.position(token_hash(second), "shape")
    return math.hypot(bx - ax, by - ay)

  def test_two_similar_words_that_are_far_apart_come_closer_when_they_appear_together(self):
    self.place(self.memory, cat=(0.3, 0.5), cats=(0.7, 0.5))
    self.memory.observe(["cat", "cats"])
    self.assertLess(self.distance(self.memory, "cat", "cats"), 0.4)

  def test_two_dissimilar_words_that_are_far_apart_come_closer_too(self):
    self.place(self.memory, cat=(0.3, 0.5), dog=(0.7, 0.5))
    self.memory.observe(["cat", "dog"])
    self.assertLess(self.distance(self.memory, "cat", "dog"), 0.4)

  def test_two_words_that_are_closer_than_their_rest_distance_move_apart(self):
    self.place(self.memory, cat=(0.5, 0.5), dog=(0.6, 0.5))
    self.memory.observe(["cat", "dog"])
    self.assertGreater(self.distance(self.memory, "cat", "dog"), 0.1)

  def test_a_neighbor_beyond_the_reach_has_no_effect(self):
    self.place(self.memory, cat=(0.1, 0.5), dog=(0.9, 0.5))
    self.memory.observe(["cat"])
    self.assertEqual(self.memory.position(self.cat, "shape"), (0.1, 0.5))

  def test_only_the_words_of_the_flow_move_but_the_others_still_act(self):
    self.place(self.memory, cat=(0.3, 0.5), dog=(0.6, 0.5))
    self.memory.observe(["cat"])
    self.assertNotEqual(self.memory.position(self.cat, "shape"), (0.3, 0.5))
    self.assertEqual(self.memory.position(self.dog, "shape"), (0.6, 0.5))

  def test_a_word_seen_in_more_flows_moves_less(self):
    fresh = Memory(CONFIG)
    fresh.add("cat")
    fresh.add("dog")
    self.place(fresh, cat=(0.3, 0.5), dog=(0.6, 0.5))
    fresh.observe(["cat"])
    old = Memory(CONFIG)
    old.add("cat")
    old.add("dog")
    self.place(old, cat=(0.3, 0.5), dog=(0.6, 0.5))
    old.counts[token_hash("cat")] = 3
    old.observe(["cat"])
    moved_fresh = abs(fresh.position(token_hash("cat"), "shape")[0] - 0.3)
    moved_old = abs(old.position(token_hash("cat"), "shape")[0] - 0.3)
    self.assertAlmostEqual(moved_fresh / moved_old, 4.0)

  def test_the_moves_of_a_flow_do_not_depend_on_the_order_of_its_words(self):
    other = Memory(CONFIG)
    other.add("cat")
    other.add("cats")
    other.add("dog")
    for memory in (self.memory, other):
      self.place(memory, cat=(0.3, 0.5), cats=(0.5, 0.6), dog=(0.6, 0.4))
    self.memory.observe(["cat", "cats", "dog"])
    other.observe(["dog", "cats", "cat"])
    self.assertEqual(self.memory.positions["shape"], other.positions["shape"])

  def test_the_positions_stay_in_the_plane(self):
    self.place(self.memory, cat=(0.02, 0.5), dog=(0.05, 0.5))
    self.memory.observe(["cat", "dog"])
    for position in self.memory.positions["shape"].values():
      self.assertTrue(0.0 <= position[0] <= 1.0 and 0.0 <= position[1] <= 1.0)

  def test_the_usage_map_does_not_move(self):
    before = dict(self.memory.positions["usage"])
    self.place(self.memory, cat=(0.3, 0.5), cats=(0.7, 0.5))
    self.memory.observe(["cat", "cats"])
    self.assertEqual(self.memory.positions["usage"], before)

  def test_a_word_without_any_weight_does_not_move(self):
    memory = Memory(config(base=0))
    memory.add("cat")
    memory.add("dog")
    self.place(memory, cat=(0.3, 0.5), dog=(0.6, 0.5))
    memory.observe(["cat"])
    self.assertEqual(memory.position(token_hash("cat"), "shape"), (0.3, 0.5))

class PullTest(unittest.TestCase):
  def setUp(self):
    self.memory = Memory(CONFIG)
    for word in ("cat", "cats", "dog"):
      self.memory.add(word)
    self.clock = SimpleNamespace(moment=0)
    self.plane = Plane({"uid": "A", "peak": 4.0}, Moments(self.clock, 2))

  def perception(self, word, x, y, energy=1.0, moment=0):
    self.clock.moment = moment
    self.plane.receive(token_hash(word), x, y, energy)
    return self.plane.perceptions[(token_hash(word), x, y, moment)]

  def test_a_similar_neighbor_attracts(self):
    cat = self.perception("cat", 0.3, 0.5)
    self.perception("cats", 0.7, 0.5)
    x, y, _ = self.memory.pull(cat, self.plane)
    self.assertGreater(x, 0.3)
    self.assertAlmostEqual(y, 0.5)

  def test_a_dissimilar_neighbor_attracts_beyond_the_far_distance_and_repels_below_it(self):
    cat = self.perception("cat", 0.3, 0.5)
    dog = self.perception("dog", 0.7, 0.5)
    self.assertGreater(self.memory.pull(cat, self.plane)[0], 0.3)
    self.plane.move(dog, 0.4, 0.5)
    self.assertLess(self.memory.pull(cat, self.plane)[0], 0.3)

  def test_a_neighbor_beyond_the_reach_has_no_effect_but_counts_in_the_cost(self):
    cat = self.perception("cat", 0.1, 0.5)
    self.perception("dog", 0.9, 0.5)
    self.assertEqual(self.memory.pull(cat, self.plane), (0.1, 0.5, 1))

  def test_a_neighbor_of_another_moment_neither_acts_nor_counts(self):
    cat = self.perception("cat", 0.3, 0.5)
    self.perception("cats", 0.7, 0.5, moment=1)
    self.assertEqual(self.memory.pull(cat, self.plane), (0.3, 0.5, 1))

  def test_two_perceptions_of_the_same_word_are_neighbors_without_affinity(self):
    first = self.perception("cat", 0.3, 0.5)
    self.perception("cat", 0.7, 0.5)
    self.assertGreater(self.memory.pull(first, self.plane)[0], 0.3)

  def test_a_perception_with_twice_the_energy_moves_half_as_far(self):
    moves = []
    for energy in (1.0, 2.0):
      plane = Plane({"uid": "B", "peak": 4.0}, Moments(self.clock, 2))
      plane.receive(token_hash("cat"), 0.3, 0.5, energy)
      plane.receive(token_hash("dog"), 0.7, 0.5, 1.0)
      cat = plane.perceptions[(token_hash("cat"), 0.3, 0.5, 0)]
      moves.append(self.memory.pull(cat, plane)[0] - 0.3)
    self.assertAlmostEqual(moves[0] / moves[1], 2.0)

  def test_the_move_of_a_nearly_empty_perception_is_capped_at_the_reach(self):
    cat = self.perception("cat", 0.3, 0.5, energy=0.001)
    self.perception("dog", 0.7, 0.5)
    x, y, _ = self.memory.pull(cat, self.plane)
    self.assertAlmostEqual(math.hypot(x - 0.3, y - 0.5), 0.5)

  def test_the_target_position_stays_in_the_plane(self):
    cat = self.perception("cat", 0.02, 0.5)
    self.perception("dog", 0.05, 0.5)
    x, y, _ = self.memory.pull(cat, self.plane)
    self.assertTrue(0.0 <= x <= 1.0 and 0.0 <= y <= 1.0)

  def test_a_perception_without_any_weight_stays_where_it_is(self):
    memory = Memory(config(base=0))
    memory.add("cat")
    memory.add("dog")
    cat = self.perception("cat", 0.3, 0.5)
    self.perception("dog", 0.7, 0.5)
    self.assertEqual(memory.pull(cat, self.plane), (0.3, 0.5, 1))

  def test_the_cost_is_the_number_of_neighbors_of_the_moment_and_one_for_a_perception_alone(self):
    cat = self.perception("cat", 0.3, 0.5)
    self.assertEqual(self.memory.pull(cat, self.plane)[2], 1)
    self.perception("dog", 0.5, 0.5)
    self.perception("cats", 0.6, 0.5)
    self.perception("dog", 0.9, 0.9)
    self.assertEqual(self.memory.pull(cat, self.plane)[2], 3)

  def test_the_affinity_comes_from_the_terms_given_to_the_spring_pull(self):
    cat = self.perception("cat", 0.3, 0.5)
    self.perception("dog", 0.4, 0.5)
    repelled = self.memory.spring_pull(cat, self.plane, lambda other: (0.0, 0.2, 1.0))[0]
    attracted = self.memory.spring_pull(cat, self.plane, lambda other: (1.0, 0.2, 1.0))[0]
    self.assertLess(repelled, 0.3)
    self.assertGreater(attracted, 0.3)

  def test_the_boost_of_the_terms_multiplies_the_force_and_not_the_weight(self):
    cat = self.perception("cat", 0.3, 0.5, energy=4.0)
    self.perception("dog", 0.7, 0.5)
    plain = self.memory.spring_pull(cat, self.plane, lambda other: (0.0, 0.2, 1.0))[0] - 0.3
    boosted = self.memory.spring_pull(cat, self.plane, lambda other: (0.0, 0.2, 2.0))[0] - 0.3
    self.assertAlmostEqual(boosted / plain, 2.0)

  def test_the_plane_is_not_modified_by_a_pull(self):
    cat = self.perception("cat", 0.3, 0.5)
    self.perception("cats", 0.7, 0.5)
    before = {key: (perception.x, perception.y, perception.energy) for key, perception in self.plane.perceptions.items()}
    self.memory.pull(cat, self.plane)
    after = {key: (perception.x, perception.y, perception.energy) for key, perception in self.plane.perceptions.items()}
    self.assertEqual(before, after)

class PullUsageTest(unittest.TestCase):
  def setUp(self):
    self.memory = Memory(config(rate=0.05))
    self.clock = SimpleNamespace(moment=0)
    self.moments = Moments(self.clock, 2)
    self.plane = Plane({"uid": "A", "peak": 4.0}, self.moments)

  def perception(self, word, x, y, energy=1.0, moment=0):
    self.clock.moment = moment
    self.plane.receive(token_hash(word), x, y, energy)
    return self.plane.perceptions[(token_hash(word), x, y, moment)]

  def link(self, first, second, times=1, moment=0):
    self.clock.moment = moment
    for _ in range(times):
      self.moments.record([token_hash(first), token_hash(second)])

  def shift(self, memory=None, moment=0):
    cat = self.plane.perceptions[(token_hash("cat"), 0.3, 0.5, moment)]
    return (memory or self.memory).pull_usage(cat, self.plane, self.moments)[0] - 0.3

  def test_a_linked_neighbor_attracts_and_a_neighbor_without_link_repels(self):
    self.perception("cat", 0.3, 0.5)
    self.perception("dog", 0.5, 0.5)
    self.assertLess(self.shift(Memory(config(rate=0.05, coexpression=0))), 0.0)
    self.link("cat", "dog")
    self.assertGreater(self.shift(Memory(config(rate=0.05, coexpression=0))), 0.0)

  def test_the_link_saturates_with_its_strength(self):
    self.perception("cat", 0.3, 0.5)
    self.perception("dog", 0.4, 0.5)
    self.link("cat", "dog")
    weak = self.shift()
    self.link("cat", "dog", times=2)
    strong = self.shift()
    self.link("cat", "dog", times=50)
    saturated = self.shift()
    self.link("cat", "dog", times=500)
    self.assertGreater(strong, weak)
    self.assertGreater(saturated, strong)
    self.assertAlmostEqual(self.shift(), saturated, places=3)

  def test_the_amplification_strengthens_the_force_of_a_linked_neighbor(self):
    self.perception("cat", 0.3, 0.5, energy=4.0)
    self.perception("dog", 0.6, 0.5)
    self.link("cat", "dog")
    plain = self.shift(Memory(config(rate=0.05, amplify=0)))
    amplified = self.shift(Memory(config(rate=0.05, amplify=2.0)))
    self.assertGreater(amplified, plain)

  def test_a_neighbor_of_another_moment_has_no_effect(self):
    cat = self.perception("cat", 0.3, 0.5)
    self.perception("dog", 0.4, 0.5, moment=1)
    self.assertEqual(self.memory.pull_usage(cat, self.plane, self.moments), (0.3, 0.5, 1))

  def test_the_expression_of_a_neighbor_attracts_through_the_coexpression_without_link(self):
    self.perception("cat", 0.3, 0.5)
    self.perception("dog", 0.4, 0.5, energy=4.0)
    self.assertGreater(self.shift(Memory(config(rate=0.05, coexpression=1.0))), 0.0)
    self.assertLess(self.shift(Memory(config(rate=0.05, coexpression=0.0))), 0.0)

  def test_a_neighbor_without_link_and_with_almost_no_energy_still_acts_at_the_base_level(self):
    self.perception("cat", 0.3, 0.5)
    self.perception("dog", 0.4, 0.5, energy=0.01)
    self.assertLess(self.shift(), 0.0)

  def test_the_cost_is_the_number_of_neighbors_of_the_moment(self):
    cat = self.perception("cat", 0.3, 0.5)
    self.assertEqual(self.memory.pull_usage(cat, self.plane, self.moments)[2], 1)
    self.perception("dog", 0.5, 0.5)
    self.perception("bird", 0.6, 0.5)
    self.perception("fish", 0.9, 0.9, moment=1)
    self.assertEqual(self.memory.pull_usage(cat, self.plane, self.moments)[2], 2)

  def test_nothing_is_modified_by_a_pull(self):
    cat = self.perception("cat", 0.3, 0.5)
    self.perception("dog", 0.4, 0.5)
    self.link("cat", "dog")
    before = ({key: (p.x, p.y, p.energy) for key, p in self.plane.perceptions.items()}, self.moments.links_of(0), self.moments.link_totals.copy())
    self.memory.pull_usage(cat, self.plane, self.moments)
    after = ({key: (p.x, p.y, p.energy) for key, p in self.plane.perceptions.items()}, self.moments.links_of(0), self.moments.link_totals.copy())
    self.assertEqual(before, after)

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
    return config(**changes)

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

  def test_the_spring_settings_are_required_and_must_be_numbers(self):
    for key in ("range", "rest", "far", "base", "rate", "coexpression", "kappa", "amplify"):
      config_without = self.with_changes()
      del config_without["memory"][key]
      self.assertIn(f"config.memory.{key}", self.rejected(config_without), key)
      for value in ("0.5", None, True):
        self.assertIn(f"config.memory.{key}", self.rejected(self.with_changes(**{key: value})), repr((key, value)))

  def test_the_range_and_the_rate_must_be_greater_than_zero(self):
    for key in ("range", "rate"):
      for value in (0, -1):
        self.assertIn(f"config.memory.{key}", self.rejected(self.with_changes(**{key: value})), repr((key, value)))

  def test_the_kappa_must_be_greater_than_zero_and_the_coexpression_and_the_amplification_at_least_zero(self):
    for value in (0, -1):
      self.assertIn("config.memory.kappa", self.rejected(self.with_changes(kappa=value)), repr(value))
    for key in ("coexpression", "amplify"):
      self.assertIn(f"config.memory.{key}", self.rejected(self.with_changes(**{key: -0.1})), key)
      Memory(self.with_changes(**{key: 0}))

  def test_the_rest_and_the_base_must_be_at_least_zero_and_the_far_distance_at_least_the_rest(self):
    for key in ("rest", "base"):
      self.assertIn(f"config.memory.{key}", self.rejected(self.with_changes(**{key: -0.1})), key)
    self.assertIn("config.memory.far", self.rejected(self.with_changes(rest=0.3, far=0.2)))
    Memory(self.with_changes(rest=0.2, far=0.2, base=0))

  def test_the_orbit_is_required(self):
    config = self.with_changes()
    del config["memory"]["orbit"]
    self.assertIn("config.memory.orbit", self.rejected(config))

  def test_the_orbit_must_be_a_list_of_two_numbers_of_at_least_zero(self):
    for orbit in ([0.05], [0.05, 0.1, 0.2], [-0.1, 0.1], ["a", 0.1], [0.05, True], 0.05, None):
      self.assertIn("config.memory.orbit", self.rejected(self.with_changes(orbit=orbit)), repr(orbit))

if __name__ == "__main__":
  unittest.main()
