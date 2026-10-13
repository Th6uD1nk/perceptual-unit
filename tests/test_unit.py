import copy
import json
import math
import unittest

import support
from generator import Generator
from plane import Plane
from transcription import token_hash, token_position
from unit import Unit

MEMORY = {"floor": 0.3, "threshold": 0.5, "orbit": [0.05, 0.1], "window": 2, "recent": 3, "decay": 0.3, "range": 0.5, "rest": 0.03, "far": 0.25, "base": 0.2, "rate": 1.0, "coexpression": 1.0, "kappa": 1.0, "amplify": 2.0}

def entry(uid, peak=1.0, transfers=None, relax=None):
  return {"uid": uid, "peak": peak, "relax": relax, "transfers": transfers if transfers is not None else []}

def transfer(target, **changes):
  return dict({"target": target, "energy": 0.0625, "step": 0.25, "cooldown": 0, "attraction": 0.0, "distance_power": 2.0, "impact": 0.0, "cycle": 10}, **changes)

def make_config(planes, tick=4.0, seed=1, moment=1000):
  return {"scheduler": {"tick": tick, "budget": 0, "moment": moment}, "random": {"seed": seed}, "memory": MEMORY, "planes": planes}

CONFIG = make_config([entry("A", 4.0), entry("C", 2.0), entry("D", 1.0)])

class InstantiationTest(unittest.TestCase):
  def test_the_unit_creates_one_plane_per_entry(self):
    unit = Unit(CONFIG)
    self.assertEqual(len(unit.planes), 3)
    for plane in unit.planes.values():
      self.assertIsInstance(plane, Plane)

  def test_the_planes_are_found_by_uid(self):
    self.assertEqual(Unit(CONFIG).planes["C"].uid, "C")

  def test_the_order_of_the_config_is_kept(self):
    unit = Unit(make_config([entry("D"), entry("A")]))
    self.assertEqual(list(unit.planes), ["D", "A"])

  def test_each_plane_receives_its_own_peak(self):
    unit = Unit(CONFIG)
    self.assertEqual([plane.peak for plane in unit.planes.values()], [4.0, 2.0, 1.0])

  def test_two_units_do_not_share_their_planes(self):
    first = Unit(CONFIG)
    second = Unit(CONFIG)
    self.assertIsNot(first.planes["A"], second.planes["A"])

  def test_the_unit_keeps_its_own_copy_of_the_config(self):
    config = copy.deepcopy(CONFIG)
    unit = Unit(config)
    config["planes"].append({"uid": "Z"})
    config["planes"][0]["uid"] = "B"
    self.assertEqual(list(unit.planes), ["A", "C", "D"])
    self.assertEqual(unit.config, CONFIG)

class SchedulerTest(unittest.TestCase):
  def test_an_update_advances_the_ticks_by_the_tick_duration_of_the_config(self):
    unit = Unit(make_config([entry("A")], tick=2.0))
    self.assertEqual(unit.update(10.0), 5)
    self.assertEqual(unit.ticks, 5)

  def test_two_units_do_not_share_their_scheduler(self):
    first = Unit(CONFIG)
    second = Unit(CONFIG)
    first.update(8.0)
    self.assertEqual(second.ticks, 0)

class GeneratorTest(unittest.TestCase):
  def test_the_generator_of_the_unit_is_seeded_by_the_config(self):
    unit = Unit(make_config([entry("A")], seed=7))
    self.assertEqual(unit.generator.random(), Generator(7).random())

  def test_two_units_do_not_share_their_generator(self):
    first = Unit(CONFIG)
    second = Unit(CONFIG)
    expected = Generator(1).random()
    first.generator.random()
    self.assertEqual(second.generator.random(), expected)

class CursorsTest(unittest.TestCase):
  CONFIG = make_config([
    entry("A", transfers=[transfer("C", energy=0.0625, step=0.25, cycle=10), transfer("D", energy=0.125, step=0.5, cycle=20)]),
    entry("C", transfers=[transfer("A", energy=0.03125, step=0.125, cycle=30)]),
    entry("D")
  ])

  def starts(self, seed):
    config = copy.deepcopy(self.CONFIG)
    config["random"]["seed"] = seed
    return [(cursor.x, cursor.y, cursor.dx, cursor.dy) for cursor in Unit(config).cursors]

  def test_the_unit_creates_one_cursor_per_transfer_in_the_order_of_the_config_holding_its_own_planes(self):
    unit = Unit(self.CONFIG)
    self.assertEqual(len(unit.cursors), 3)
    for cursor, (source, target) in zip(unit.cursors, [("A", "C"), ("A", "D"), ("C", "A")]):
      self.assertIs(cursor.source, unit.planes[source])
      self.assertIs(cursor.target, unit.planes[target])

  def test_each_cursor_receives_the_settings_of_its_own_transfer(self):
    unit = Unit(self.CONFIG)
    self.assertEqual([cursor.energy for cursor in unit.cursors], [0.0625, 0.125, 0.03125])
    self.assertEqual([cursor.step for cursor in unit.cursors], [0.25, 0.5, 0.125])
    self.assertEqual([cursor.cycle for cursor in unit.cursors], [10, 20, 30])

  def test_all_the_cursors_share_the_generator_of_the_unit(self):
    unit = Unit(self.CONFIG)
    for cursor in unit.cursors:
      self.assertIs(cursor.generator, unit.generator)

  def test_the_cursors_draw_their_start_one_after_the_other_in_the_generator_of_the_unit(self):
    generator = Generator(1)
    expected = []
    for _ in range(3):
      x, y, angle = generator.random(), generator.random(), generator.random() * math.tau
      expected.append((x, y))
    self.assertEqual([(x, y) for x, y, dx, dy in self.starts(1)], expected)

  def test_the_cursors_wait_for_the_first_tick_before_moving(self):
    for cursor in Unit(self.CONFIG).cursors:
      self.assertIsNone(cursor.segment)

  def test_the_cursors_run_at_every_tick_of_the_unit(self):
    unit = Unit(self.CONFIG)
    unit.update(12.0)
    for cursor in unit.cursors:
      self.assertEqual(cursor.moved_tick, 3)
      self.assertIsNotNone(cursor.segment)

  def test_a_unit_without_transfers_has_no_cursor(self):
    self.assertEqual(Unit(CONFIG).cursors, [])

class EndToEndTest(unittest.TestCase):
  def unit(self):
    plane = entry("A", peak=1.0, transfers=[transfer("C", energy=0.01, step=0.05, cooldown=5, attraction=1.0, cycle=50)])
    unit = Unit(make_config([plane, entry("C", peak=1.0)], tick=1.0))
    unit.feed_flow(["house"], 0.2)
    return unit

  def advance(self, unit, ticks):
    for _ in range(ticks):
      unit.update(1.0)

  def energy(self, plane):
    return sum(perception.energy for perception in plane.perceptions.values())

  def test_the_energy_fed_into_the_first_plane_reaches_the_target_plane_at_the_same_triplet(self):
    unit = self.unit()
    self.advance(unit, 40)
    x, y = token_position("house")
    arrived = unit.planes["C"].perceptions[(token_hash("house"), x, y, 0)]
    self.assertGreater(arrived.energy, 0.0)
    self.assertLess(unit.planes["A"].perceptions[(token_hash("house"), x, y, 0)].energy, 0.2)

  def test_the_energy_is_neither_created_nor_lost_by_the_transfers(self):
    unit = self.unit()
    self.advance(unit, 40)
    self.assertAlmostEqual(self.energy(unit.planes["A"]) + self.energy(unit.planes["C"]), 0.2)

  def test_the_count_of_the_moment_follows_the_perceptions_of_all_the_planes(self):
    unit = self.unit()
    self.assertEqual(unit.moments.count(0), 1)
    self.advance(unit, 40)
    self.assertEqual(unit.moments.count(0), 2)
    self.advance(unit, 760)
    self.assertEqual(unit.moments.count(0), 1)

  def test_a_source_perception_that_is_read_until_it_is_empty_leaves_its_plane(self):
    unit = self.unit()
    self.advance(unit, 800)
    self.assertEqual(unit.planes["A"].perceptions, {})
    self.assertAlmostEqual(self.energy(unit.planes["C"]), 0.2)

def similar_pair_in_range():
  for base in ("cat", "dog", "pig", "cow", "hen", "bee", "fox", "owl", "ant", "ape", "elk", "emu", "yak", "rat", "bat"):
    first, second = token_position(base), token_position(base + "s")
    distance = math.hypot(first[0] - second[0], first[1] - second[1])
    if 0.2 < distance < 0.45:
      return base, base + "s"
  raise AssertionError("no similar pair in range")

class RelaxationTest(unittest.TestCase):
  def unit(self, relax):
    return Unit(make_config([entry("A", peak=4.0, relax=relax)], tick=1.0))

  def distance(self, unit, words):
    first, second = (next(perception for perception in unit.planes["A"].perceptions.values() if perception.hash == token_hash(word)) for word in words)
    return math.hypot(first.x - second.x, first.y - second.y)

  def test_the_unit_has_a_memory_made_from_its_section_of_the_config(self):
    unit = self.unit(None)
    self.assertEqual(unit.memory.reach, MEMORY["range"])
    self.assertEqual(unit.memory.lexicon.floor, MEMORY["floor"])

  def test_the_words_of_a_flow_enter_the_lexicon_of_the_memory(self):
    unit = self.unit(None)
    unit.feed_flow(["cat", "cats"], 1.0)
    self.assertEqual(unit.memory.lexicon.word(token_hash("cats")), "cats")
    self.assertIn(token_hash("cats"), unit.memory.lexicon.similar(token_hash("cat")))

  def test_the_words_of_a_relaxed_plane_that_look_alike_come_closer_and_those_of_a_plain_plane_do_not(self):
    words = list(similar_pair_in_range())
    relaxed, plain = self.unit("shape"), self.unit(None)
    for unit in (relaxed, plain):
      unit.feed_flow(words, 1.0)
    before = self.distance(plain, words)
    for unit in (relaxed, plain):
      unit.update(30.0)
    self.assertAlmostEqual(self.distance(plain, words), before)
    self.assertLess(self.distance(relaxed, words), before)

  def test_a_usage_plane_gets_a_usage_relaxation_and_its_words_move(self):
    words = list(similar_pair_in_range())
    unit = self.unit("usage")
    self.assertEqual([relaxation.kind for relaxation in unit.relaxations], ["usage"])
    unit.feed_flow(words, 1.0)
    before = {key: (p.x, p.y) for key, p in unit.planes["A"].perceptions.items()}
    unit.update(30.0)
    after = {p.key: (p.x, p.y) for p in unit.planes["A"].perceptions.values()}
    self.assertNotEqual(sorted(before.values()), sorted(after.values()))

  def test_a_word_is_deposited_near_a_living_similar_perception_and_otherwise_at_its_anchor(self):
    words = list(similar_pair_in_range())
    unit = self.unit(None)
    unit.feed_flow(words[:1], 1.0)
    first = next(iter(unit.planes["A"].perceptions.values()))
    unit.feed_flow(words[1:], 1.0)
    second = [p for p in unit.planes["A"].perceptions.values() if p is not first][0]
    self.assertLess(math.hypot(second.x - first.x, second.y - first.y), 0.16)
    self.assertNotEqual((second.x, second.y), token_position(words[1]))

  def test_a_word_fed_again_is_deposited_on_its_living_perception(self):
    unit = self.unit(None)
    unit.feed_flow(["cat"], 1.0)
    unit.feed_flow(["cat"], 1.0)
    self.assertEqual(len(unit.planes["A"].perceptions), 1)

  def test_nothing_moves_in_a_unit_that_has_received_nothing(self):
    unit = self.unit("shape")
    unit.update(50.0)
    self.assertEqual(unit.planes["A"].perceptions, {})

  def test_the_energy_is_conserved_when_a_relaxed_plane_also_transfers(self):
    first, second = similar_pair_in_range()
    plane = entry("A", peak=1.0, relax="shape", transfers=[transfer("C", energy=0.01, step=0.05, cooldown=5, attraction=1.0, cycle=50)])
    unit = Unit(make_config([plane, entry("C", peak=1.0)], tick=1.0))
    unit.feed_flow([first, second], 0.2)
    unit.update(40.0)
    total = sum(perception.energy for name in ("A", "C") for perception in unit.planes[name].perceptions.values())
    self.assertAlmostEqual(total, 0.4)
    self.assertGreater(sum(perception.energy for perception in unit.planes["C"].perceptions.values()), 0.0)

class ConfigWiringTest(unittest.TestCase):
  def rejected(self, config):
    with self.assertRaises(ValueError) as caught:
      Unit(config)
    return str(caught.exception)

  def test_the_memory_section_is_required_by_the_unit(self):
    config = make_config([entry("A")])
    del config["memory"]
    self.assertIn("config.memory", self.rejected(config))

  def test_the_relax_of_a_plane_is_required_and_must_be_null_or_shape(self):
    plane = entry("A")
    del plane["relax"]
    self.assertIn("config.planes[0].relax", self.rejected(make_config([plane])))
    for relax in ("other", 3, True, ["shape"]):
      self.assertIn("config.planes[0].relax", self.rejected(make_config([entry("A", relax=relax)])), repr(relax))
    Unit(make_config([entry("A", relax="shape")]))
    Unit(make_config([entry("A", relax="usage")]))

class FlowTest(unittest.TestCase):
  def perception(self, unit, token, moment=0):
    x, y = token_position(token)
    return unit.planes["A"].perceptions[(token_hash(token), x, y, moment)]

  def test_each_word_of_a_flow_becomes_a_perception_of_the_first_plane(self):
    unit = Unit(CONFIG)
    unit.feed_flow(["a", "b", "c"], 1.0)
    self.assertEqual([self.perception(unit, token).energy for token in ("a", "b", "c")], [1.0, 1.0, 1.0])
    self.assertEqual(len(unit.planes["A"].perceptions), 3)
    self.assertEqual(unit.planes["C"].perceptions, {})
    self.assertEqual(unit.planes["D"].perceptions, {})

  def test_a_word_repeated_in_a_flow_reinforces_its_perception(self):
    unit = Unit(CONFIG)
    unit.feed_flow(["a", "b", "a"], 1.0)
    self.assertEqual(len(unit.planes["A"].perceptions), 2)
    self.assertEqual(self.perception(unit, "a").energy, 2.0)

  def test_the_event_of_the_flow_holds_the_hashes_in_order_with_their_duplicates(self):
    unit = Unit(CONFIG)
    unit.feed_flow(["a", "b", "a"], 1.0)
    self.assertEqual(unit.moments.events(0), [[token_hash("a"), token_hash("b"), token_hash("a")]])

  def test_the_flow_builds_the_contexts_of_the_moment_from_the_hashes_of_its_words(self):
    unit = Unit(CONFIG)
    unit.feed_flow(["a", "b"], 1.0)
    a, b = token_hash("a"), token_hash("b")
    self.assertEqual(unit.moments.contexts(0), {(None, b): {a: 1}, (a, None): {b: 1}})

  def test_the_flow_links_the_words_within_the_window_of_the_config_in_the_moment(self):
    unit = Unit(CONFIG)
    unit.feed_flow(["a", "b", "c", "d"], 1.0)
    hashes = [token_hash(word) for word in "abcd"]
    self.assertEqual(unit.moments.link(hashes[0], hashes[2]), 1)
    self.assertEqual(unit.moments.link(hashes[0], hashes[3]), 0)

  def test_a_flow_of_another_moment_records_its_event_in_that_moment(self):
    unit = Unit(make_config([entry("A", peak=4.0)], tick=1.0, moment=2))
    unit.feed_flow(["a"], 1.0)
    unit.update(2.0)
    unit.feed_flow(["b"], 1.0)
    self.assertEqual(unit.moments.events(0), [[token_hash("a")]])
    self.assertEqual(unit.moments.events(1), [[token_hash("b")]])

  def test_the_flow_gives_back_the_energy_accepted_for_each_word(self):
    unit = Unit(CONFIG)
    self.assertEqual(unit.feed_flow(["a", "b"], 6.0), [4.0, 4.0])
    self.assertEqual(Unit(CONFIG).feed_flow(["a", "a"], 3.0), [3.0, 1.0])

  def test_an_invalid_flow_is_refused_without_any_perception_or_event(self):
    unit = Unit(CONFIG)
    for tokens in ([], "text", ["a", ""], ["a", 3], [None]):
      with self.assertRaises(ValueError, msg=repr(tokens)):
        unit.feed_flow(tokens, 1.0)
    self.assertEqual(unit.planes["A"].perceptions, {})
    self.assertEqual(unit.moments.events(0), [])

class BetweenTest(unittest.TestCase):
  def test_a_flow_fed_twice_gives_a_count_of_two_for_the_word_between_its_neighbors(self):
    unit = Unit(CONFIG)
    unit.feed_flow(["a", "b", "c"], 1.0)
    unit.feed_flow(["a", "b", "c"], 1.0)
    self.assertEqual(unit.between("a", "c"), [{"hash": token_hash("b"), "count": 2, "energy": None}])

  def test_the_words_are_sorted_by_count_and_then_by_hash(self):
    unit = Unit(CONFIG)
    unit.feed_flow(["a", "b", "c"], 1.0)
    unit.feed_flow(["a", "b", "c"], 1.0)
    unit.feed_flow(["a", "x", "c"], 1.0)
    unit.feed_flow(["a", "y", "c"], 1.0)
    answer = unit.between("a", "c")
    self.assertEqual(answer[0]["hash"], token_hash("b"))
    self.assertEqual([entry["hash"] for entry in answer[1:]], sorted([token_hash("x"), token_hash("y")]))

  def test_the_counts_of_two_moments_add_up(self):
    unit = Unit(make_config([entry("A", peak=4.0)], tick=1.0, moment=2))
    unit.feed_flow(["a", "b", "c"], 1.0)
    unit.update(2.0)
    unit.feed_flow(["a", "b", "c"], 1.0)
    self.assertEqual(unit.between("a", "c")[0]["count"], 2)

  def test_an_edge_of_a_flow_is_asked_with_none(self):
    unit = Unit(CONFIG)
    unit.feed_flow(["a", "b"], 1.0)
    self.assertEqual([entry["hash"] for entry in unit.between(None, "b")], [token_hash("a")])
    self.assertEqual([entry["hash"] for entry in unit.between("a", None)], [token_hash("b")])

  def test_unknown_neighbors_give_an_empty_list(self):
    unit = Unit(CONFIG)
    unit.feed_flow(["a", "b", "c"], 1.0)
    self.assertEqual(unit.between("a", "z"), [])

  def test_with_a_plane_the_energy_of_each_word_orders_the_answer_before_the_count(self):
    unit = Unit(CONFIG)
    unit.feed_flow(["a", "cat", "c"], 1.0)
    unit.feed_flow(["a", "dog", "c"], 3.0)
    answer = unit.between("a", "c", "A")
    self.assertEqual([entry["hash"] for entry in answer], [token_hash("dog"), token_hash("cat")])
    self.assertEqual([entry["energy"] for entry in answer], [3.0, 1.0])

  def test_a_word_without_perception_in_the_plane_has_no_energy(self):
    unit = Unit(CONFIG)
    unit.feed_flow(["a", "b", "c"], 1.0)
    self.assertEqual(unit.between("a", "c", "C")[0]["energy"], 0.0)

  def test_an_unknown_plane_or_an_invalid_neighbor_is_refused(self):
    unit = Unit(CONFIG)
    for arguments in (("a", "b", "Z"), (3, "b"), ("", "b"), ("a", ["b"])):
      with self.assertRaises(ValueError, msg=repr(arguments)):
        unit.between(*arguments)

  def test_a_released_moment_no_longer_counts_in_the_answer(self):
    unit = Unit(make_config([entry("A", peak=4.0)], tick=1.0, moment=2))
    unit.feed_flow(["a", "b", "c"], 1.0)
    unit.update(2.0)
    for perception in list(unit.planes["A"].perceptions.values()):
      unit.planes["A"].take(perception, 10.0)
    self.assertEqual(unit.between("a", "c"), [])

class StateTest(unittest.TestCase):
  def test_the_state_gives_the_ticks_and_the_planes_in_the_order_of_the_config(self):
    unit = Unit(CONFIG)
    unit.update(8.0)
    state = unit.state()
    self.assertEqual(state["ticks"], 2)
    self.assertEqual([plane["uid"] for plane in state["planes"]], ["A", "C", "D"])

  def test_the_state_gives_the_moment_in_progress(self):
    unit = Unit(make_config([entry("A")], tick=1.0, moment=2))
    self.assertEqual(unit.state()["moment"], 0)
    unit.update(2.0)
    self.assertEqual(unit.state()["moment"], 1)

  def test_the_state_holds_the_perceptions_of_each_plane(self):
    unit = Unit(CONFIG)
    unit.planes["A"].receive("house", 0.25, 0.75, 1.0)
    unit.planes["D"].receive("cat", 0.5, 0.5, 0.5)
    planes = {plane["uid"]: plane for plane in unit.state()["planes"]}
    self.assertEqual([entry["hash"] for entry in planes["A"]["perceptions"]], ["house"])
    self.assertEqual(planes["C"]["perceptions"], [])
    self.assertEqual([entry["hash"] for entry in planes["D"]["perceptions"]], ["cat"])

  def test_the_state_lists_the_cursors_in_the_order_of_their_creation(self):
    unit = Unit(CursorsTest.CONFIG)
    unit.update(8.0)
    cursors = unit.state()["cursors"]
    self.assertEqual([(cursor["source"], cursor["target"]) for cursor in cursors], [("A", "C"), ("A", "D"), ("C", "A")])
    self.assertEqual(cursors[0], unit.cursors[0].state())

  def test_a_unit_without_transfers_has_no_cursor_in_its_state(self):
    self.assertEqual(Unit(CONFIG).state()["cursors"], [])

  def test_the_state_can_be_written_as_json(self):
    unit = Unit(CursorsTest.CONFIG)
    unit.planes["A"].receive("house", 0.25, 0.75, 1.0)
    unit.update(8.0)
    self.assertEqual(json.loads(json.dumps(unit.state())), unit.state())

  def test_reading_the_state_changes_nothing_and_gives_the_same_result(self):
    unit = Unit(CONFIG)
    unit.planes["A"].receive("house", 0.25, 0.75, 1.0)
    self.assertEqual(unit.state(), unit.state())

  def test_changing_the_state_does_not_change_the_unit(self):
    unit = Unit(CONFIG)
    unit.planes["A"].receive("house", 0.25, 0.75, 1.0)
    unit.state()["planes"][0]["perceptions"].clear()
    unit.state()["planes"][0]["peak"] = 99.0
    self.assertEqual(len(unit.planes["A"].perceptions), 1)
    self.assertEqual(unit.planes["A"].peak, 4.0)

class RejectionTest(unittest.TestCase):
  def rejected(self, config):
    with self.assertRaises(ValueError) as caught:
      Unit(config)
    return str(caught.exception)

  def test_a_config_must_be_an_object(self):
    self.assertIn("config", self.rejected([]))

  def test_the_planes_are_required(self):
    self.assertIn("config.planes", self.rejected({}))

  def test_the_planes_must_be_a_non_empty_list(self):
    self.assertIn("config.planes", self.rejected({"planes": []}))
    self.assertIn("config.planes", self.rejected({"planes": {"uid": "A"}}))

  def test_a_config_without_a_scheduler_is_refused(self):
    self.assertIn("config.scheduler", self.rejected({"planes": [entry("A")]}))

  def test_the_random_section_is_required(self):
    config = make_config([entry("A")])
    del config["random"]
    self.assertIn("config.random", self.rejected(config))

  def test_the_random_section_must_be_an_object(self):
    config = make_config([entry("A")])
    config["random"] = 7
    self.assertIn("config.random", self.rejected(config))

  def test_the_seed_is_required(self):
    config = make_config([entry("A")])
    config["random"] = {}
    self.assertIn("config.random.seed", self.rejected(config))

  def test_the_seed_must_be_an_integer_of_at_least_zero(self):
    for seed in (-1, 1.5, "1", None, True):
      self.assertIn("config.random.seed", self.rejected(make_config([entry("A")], seed=seed)), repr(seed))

  def test_the_transfers_of_a_plane_are_required(self):
    plane = entry("A")
    del plane["transfers"]
    self.assertIn("config.planes[0].transfers", self.rejected(make_config([plane])))

  def test_the_transfers_of_a_plane_must_be_a_list(self):
    self.assertIn("config.planes[0].transfers", self.rejected(make_config([entry("A", transfers={})])))

  def test_a_transfer_must_be_an_object(self):
    self.assertIn("config.planes[0].transfers[0]", self.rejected(make_config([entry("A", transfers=["C"]), entry("C")])))

  def test_a_transfer_needs_a_target(self):
    plane = transfer("C")
    del plane["target"]
    self.assertIn("config.planes[0].transfers[0].target", self.rejected(make_config([entry("A", transfers=[plane]), entry("C")])))

  def test_the_target_of_a_transfer_must_be_the_uid_of_an_existing_plane(self):
    for target in ("Z", 3, None):
      config = make_config([entry("A", transfers=[transfer(target)]), entry("C")])
      self.assertIn("config.planes[0].transfers[0].target", self.rejected(config), repr(target))

  def test_a_plane_cannot_transfer_to_itself(self):
    config = make_config([entry("A", transfers=[transfer("A")])])
    self.assertIn("another plane", self.rejected(config))

  def test_the_settings_of_a_transfer_are_validated_with_their_full_path(self):
    config = make_config([entry("A", transfers=[transfer("C"), transfer("C", step=0)]), entry("C")])
    self.assertIn("config.planes[0].transfers[1].step", self.rejected(config))

  def test_a_target_declared_after_its_source_several_transfers_to_one_target_and_a_return_transfer_are_accepted(self):
    Unit(make_config([entry("A", transfers=[transfer("C"), transfer("C", step=0.5)]), entry("C", transfers=[transfer("A")])]))

  def test_a_plane_must_be_an_object(self):
    self.assertIn("config.planes[1]", self.rejected({"planes": [entry("A"), "C"]}))

  def test_a_plane_needs_a_uid(self):
    self.assertIn("config.planes[0].uid", self.rejected({"planes": [{}]}))

  def test_a_uid_must_be_a_non_empty_string(self):
    for uid in ("", 3, None, ["A"]):
      self.assertIn("config.planes[0].uid", self.rejected({"planes": [entry(uid)]}), repr(uid))

  def test_a_plane_needs_a_peak(self):
    self.assertIn("config.planes[0].peak", self.rejected({"planes": [{"uid": "A"}]}))

  def test_a_peak_must_be_a_number_greater_than_zero(self):
    for peak in (0, -1, "1", None, True, [1]):
      self.assertIn("config.planes[0].peak", self.rejected({"planes": [entry("A", peak)]}), repr(peak))

  def test_a_uid_cannot_be_used_twice(self):
    message = self.rejected({"planes": [entry("A"), entry("C"), entry("A")]})
    self.assertIn("config.planes[2].uid", message)
    self.assertIn("already used", message)

if __name__ == "__main__":
  unittest.main()
