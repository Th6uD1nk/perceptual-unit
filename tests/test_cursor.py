import json
import math
import unittest

import support
from scheduler import Scheduler
from validation import validate_cursor
from cursor import Cursor
from generator import Generator
from perception import Perception
from plane import Plane

STILL = 1e-9

def make_config(energy=0.0625, step=0.25, cooldown=0, attraction=0.0, distance_power=2.0, impact=0.0, cycle=1000):
  return {"energy": energy, "step": step, "cooldown": cooldown, "attraction": attraction, "distance_power": distance_power, "impact": impact, "cycle": cycle}

def make_cursor(x, y, dx, dy, source=None, target=None, generator=None, **settings):
  source = source if source is not None else Plane({"uid": "A", "peak": 10.0})
  target = target if target is not None else Plane({"uid": "C", "peak": 10.0})
  cursor = Cursor(make_config(**settings), source, target, generator if generator is not None else Generator(1))
  cursor.place(x, y, dx, dy)
  return cursor

class PlacementTest(unittest.TestCase):
  def test_a_new_cursor_is_at_the_center_and_heads_right(self):
    cursor = Cursor(make_config(), Plane({"uid": "A", "peak": 1.0}), Plane({"uid": "C", "peak": 1.0}), Generator(1))
    self.assertEqual((cursor.x, cursor.y, cursor.dx, cursor.dy), (0.5, 0.5, 1.0, 0.0))

  def test_the_direction_is_normalized(self):
    cursor = make_cursor(0.5, 0.5, 3.0, 4.0)
    self.assertAlmostEqual(cursor.dx, 0.6)
    self.assertAlmostEqual(cursor.dy, 0.8)

  def test_a_null_direction_is_refused(self):
    with self.assertRaises(ValueError):
      make_cursor(0.5, 0.5, 0.0, 0.0)

  def test_a_position_outside_the_plane_is_refused(self):
    for x, y in ((1.5, 0.5), (0.5, -0.1), (-0.1, 1.1)):
      with self.assertRaises(ValueError):
        make_cursor(x, y, 1.0, 0.0)

  def test_a_position_on_the_edge_is_accepted(self):
    make_cursor(0.0, 1.0, 1.0, 0.0)

  def test_a_refused_placement_leaves_the_cursor_where_it_was(self):
    cursor = make_cursor(0.25, 0.5, 1.0, 0.0)
    with self.assertRaises(ValueError):
      cursor.place(2.0, 0.5, 0.0, 1.0)
    self.assertEqual((cursor.x, cursor.y, cursor.dx, cursor.dy), (0.25, 0.5, 1.0, 0.0))

  def test_a_placement_forgets_the_last_segment_the_hits_and_the_force(self):
    cursor = make_cursor(0.25, 0.5, 1.0, 0.0)
    cursor.advance(0.25)
    cursor.hits.append("hit")
    cursor.force_x = 1.0
    cursor.place(0.5, 0.5, 0.0, 1.0)
    self.assertIsNone(cursor.segment)
    self.assertEqual(cursor.hits, [])
    self.assertEqual((cursor.force_x, cursor.force_y), (0.0, 0.0))

  def test_there_is_no_segment_before_the_first_move(self):
    self.assertIsNone(make_cursor(0.5, 0.5, 1.0, 0.0).segment)

class ConfigTest(unittest.TestCase):
  def rejected(self, config):
    with self.assertRaises(ValueError) as caught:
      Cursor(config, Plane({"uid": "A", "peak": 1.0}), Plane({"uid": "C", "peak": 1.0}), Generator(1))
    return str(caught.exception)

  def test_a_config_must_be_an_object(self):
    self.assertIn("config:", self.rejected([]))

  def test_the_errors_carry_the_path_given_by_the_caller(self):
    path = "config.planes[0].transfers[1]"
    missing = make_config()
    del missing["step"]
    invalid = make_config(cooldown=-1)
    for config, expected in (([], path + ":"), (missing, path + ".step"), (invalid, path + ".cooldown")):
      with self.assertRaises(ValueError) as caught:
        validate_cursor(config, path)
      self.assertIn(expected, str(caught.exception))

  def test_every_setting_is_required(self):
    for key in make_config():
      config = make_config()
      del config[key]
      self.assertIn(f"config.{key}", self.rejected(config), key)

  def test_the_energy_and_the_step_must_be_numbers_greater_than_zero(self):
    for key in ("energy", "step"):
      for value in (0, -1, "1", None, True):
        config = make_config()
        config[key] = value
        self.assertIn(f"config.{key}", self.rejected(config), repr((key, value)))

  def test_the_attraction_the_distance_power_and_the_impact_must_be_numbers_of_at_least_zero(self):
    for key in ("attraction", "distance_power", "impact"):
      for value in (-1, "1", None, True):
        config = make_config()
        config[key] = value
        self.assertIn(f"config.{key}", self.rejected(config), repr((key, value)))

  def test_the_cooldown_must_be_an_integer_of_at_least_zero(self):
    for value in (-1, 1.5, "2", True, None):
      config = make_config()
      config["cooldown"] = value
      self.assertIn("config.cooldown", self.rejected(config), repr(value))

  def test_the_cycle_must_be_an_integer_of_at_least_one(self):
    for value in (0, -1, 1.5, "3", True, None):
      config = make_config()
      config["cycle"] = value
      self.assertIn("config.cycle", self.rejected(config), repr(value))

  def test_zero_is_accepted_for_the_settings_that_allow_it(self):
    Cursor(make_config(attraction=0, distance_power=0, impact=0, cooldown=0), Plane({"uid": "A", "peak": 1.0}), Plane({"uid": "C", "peak": 1.0}), Generator(1))

class AdvanceTest(unittest.TestCase):
  def test_the_cursor_moves_along_its_direction_by_the_distance(self):
    cursor = make_cursor(0.2, 0.2, 1.0, 0.0)
    cursor.advance(0.3)
    self.assertAlmostEqual(cursor.x, 0.5)
    self.assertAlmostEqual(cursor.y, 0.2)

  def test_a_diagonal_move_covers_the_requested_distance(self):
    cursor = make_cursor(0.1, 0.1, 1.0, 1.0)
    cursor.advance(0.2)
    self.assertAlmostEqual(math.hypot(cursor.x - 0.1, cursor.y - 0.1), 0.2)

  def test_a_zero_distance_does_not_move_the_cursor(self):
    cursor = make_cursor(0.4, 0.6, 1.0, 1.0)
    cursor.advance(0.0)
    self.assertEqual((cursor.x, cursor.y), (0.4, 0.6))

  def test_a_negative_distance_is_refused(self):
    with self.assertRaises(ValueError):
      make_cursor(0.4, 0.6, 1.0, 1.0).advance(-0.1)

  def test_the_segment_goes_from_the_old_to_the_new_position(self):
    cursor = make_cursor(0.2, 0.2, 1.0, 0.0)
    cursor.advance(0.3)
    start_x, start_y, end_x, end_y = cursor.segment
    self.assertEqual((start_x, start_y), (0.2, 0.2))
    self.assertAlmostEqual(end_x, 0.5)
    self.assertAlmostEqual(end_y, 0.2)

class BounceTest(unittest.TestCase):
  def test_the_cursor_bounces_on_each_edge(self):
    cases = (
      ((0.1, 0.5, -1.0, 0.0), (0.2, 0.5, 1.0, 0.0)),
      ((0.9, 0.5, 1.0, 0.0), (0.8, 0.5, -1.0, 0.0)),
      ((0.5, 0.1, 0.0, -1.0), (0.5, 0.2, 0.0, 1.0)),
      ((0.5, 0.9, 0.0, 1.0), (0.5, 0.8, 0.0, -1.0)),
    )
    for start, expected in cases:
      cursor = make_cursor(*start)
      cursor.advance(0.3)
      for actual, wanted in zip((cursor.x, cursor.y, cursor.dx, cursor.dy), expected):
        self.assertAlmostEqual(actual, wanted, msg=repr(start))

  def test_the_cursor_bounces_on_two_edges_in_a_corner(self):
    cursor = make_cursor(0.9, 0.9, 1.0, 1.0)
    cursor.advance(0.3 * math.sqrt(2))
    self.assertAlmostEqual(cursor.x, 0.8)
    self.assertAlmostEqual(cursor.y, 0.8)
    self.assertLess(cursor.dx, 0.0)
    self.assertLess(cursor.dy, 0.0)

  def test_the_cursor_stays_in_the_plane_whatever_the_distance(self):
    cursor = make_cursor(0.3, 0.7, 2.0, 1.0)
    for distance in (0.5, 5.3, 12.7, 100.1):
      cursor.advance(distance)
      self.assertTrue(0.0 <= cursor.x <= 1.0)
      self.assertTrue(0.0 <= cursor.y <= 1.0)
      self.assertAlmostEqual(math.hypot(cursor.dx, cursor.dy), 1.0)

def perception(x, y, energy):
  found = Perception("token", x, y)
  found.energy = energy
  return found

def moved_cursor():
  cursor = make_cursor(0.25, 0.5, 1.0, 0.0)
  cursor.advance(0.5)
  return cursor

class CollisionTest(unittest.TestCase):
  def test_a_perception_on_the_path_is_touched(self):
    self.assertTrue(moved_cursor().touches(perception(0.5, 0.5, 0.0625)))

  def test_a_perception_whose_circle_only_brushes_the_segment_is_touched(self):
    self.assertTrue(moved_cursor().touches(perception(0.5, 0.75, 0.25)))

  def test_a_perception_whose_circle_stops_short_of_the_end_is_touched(self):
    self.assertTrue(moved_cursor().touches(perception(0.875, 0.5, 0.125)))

  def test_a_perception_out_of_reach_is_not_touched(self):
    cursor = moved_cursor()
    cases = ((0.5, 0.75, 0.125), (0.875, 0.5, 0.0625), (0.0625, 0.5, 0.0625), (0.5, 0.9, 0.125))
    for x, y, energy in cases:
      self.assertFalse(cursor.touches(perception(x, y, energy)), msg=repr((x, y, energy)))

  def test_a_perception_that_already_contains_the_start_is_not_touched(self):
    self.assertFalse(moved_cursor().touches(perception(0.25, 0.5, 0.125)))

  def test_a_perception_without_energy_is_not_touched(self):
    self.assertFalse(moved_cursor().touches(perception(0.5, 0.5, 0.0)))

  def test_nothing_is_touched_before_the_first_move(self):
    self.assertFalse(make_cursor(0.25, 0.5, 1.0, 0.0).touches(perception(0.25, 0.5, 0.5)))

  def test_nothing_is_touched_by_a_move_of_zero_distance(self):
    cursor = make_cursor(0.25, 0.5, 1.0, 0.0)
    cursor.advance(0.0)
    self.assertFalse(cursor.touches(perception(0.5, 0.5, 0.125)))

  def test_a_visit_of_a_plane_records_only_the_perceptions_touched_in_visit_order(self):
    plane = Plane({"uid": "A", "peak": 10.0})
    plane.receive("far", 0.5, 0.9, 0.0625)
    plane.receive("first", 0.375, 0.5, 0.0625)
    plane.receive("brush", 0.5, 0.75, 0.25)
    plane.receive("behind", 0.0625, 0.5, 0.0625)
    cursor = moved_cursor()
    plane.visit(10, cursor.on_visit)
    self.assertEqual([hit.hash for hit in cursor.hits], ["first", "brush"])

class FinishTest(unittest.TestCase):
  def setUp(self):
    self.source = Plane({"uid": "A", "peak": 10.0})
    self.target = Plane({"uid": "C", "peak": 10.0})
    self.cursor = make_cursor(0.25, 0.5, 1.0, 0.0, self.source, self.target)
    self.cursor.advance(0.5)

  def run_pass(self):
    self.source.visit(10, self.cursor.on_visit)

  def test_a_touched_perception_is_read_and_its_energy_goes_to_the_target(self):
    self.source.receive("first", 0.5, 0.5, 0.125)
    self.run_pass()
    self.assertEqual(self.cursor.finish(1), 0.0625)
    self.assertEqual(self.source.perceptions[("first", 0.5, 0.5)].energy, 0.0625)
    self.assertEqual(self.target.perceptions[("first", 0.5, 0.5)].energy, 0.0625)

  def test_the_total_energy_of_all_the_reads_is_returned(self):
    self.source.receive("first", 0.5, 0.5, 0.125)
    self.source.receive("second", 0.625, 0.5, 0.125)
    self.run_pass()
    self.assertEqual(self.cursor.finish(1), 0.125)

  def test_a_perception_with_less_energy_than_a_read_gives_all_and_leaves_the_plane(self):
    self.source.receive("first", 0.5, 0.5, 0.03125)
    self.run_pass()
    self.assertEqual(self.cursor.finish(1), 0.03125)
    self.assertEqual(self.source.perceptions, {})

  def test_the_peak_of_the_target_is_respected_and_the_surplus_stays_in_the_source(self):
    target = Plane({"uid": "C", "peak": 0.03125})
    cursor = make_cursor(0.25, 0.5, 1.0, 0.0, self.source, target)
    cursor.advance(0.5)
    self.source.receive("first", 0.5, 0.5, 0.125)
    self.source.visit(10, cursor.on_visit)
    self.assertEqual(cursor.finish(1), 0.03125)
    self.assertEqual(self.source.perceptions[("first", 0.5, 0.5)].energy, 0.09375)

  def test_a_perception_removed_before_the_end_of_the_pass_is_not_read(self):
    self.source.receive("first", 0.5, 0.5, 0.125)
    self.run_pass()
    self.source.remove(self.cursor.hits[0])
    self.assertEqual(self.cursor.finish(1), 0.0)
    self.assertEqual(self.target.perceptions, {})

  def test_the_hits_are_emptied_by_the_end_of_the_pass(self):
    self.source.receive("first", 0.5, 0.5, 0.125)
    self.run_pass()
    self.cursor.finish(1)
    self.assertEqual(self.cursor.hits, [])

  def test_the_cursor_moves_after_the_reads_and_keeps_the_new_segment(self):
    self.source.receive("first", 0.5, 0.5, 0.125)
    self.run_pass()
    self.cursor.finish(1)
    start_x, start_y, end_x, end_y = self.cursor.segment
    self.assertAlmostEqual(end_x - start_x, 0.25)
    self.assertEqual((start_y, end_y), (0.5, 0.5))

  def test_a_pass_without_any_hit_transfers_nothing_and_moves_in_proportion_to_the_elapsed_ticks(self):
    cursor = make_cursor(0.0, 0.5, 1.0, 0.0, step=0.125)
    self.assertEqual(cursor.finish(2), 0.0)
    self.assertAlmostEqual(cursor.x, 0.25)

  def test_a_negative_elapsed_time_is_refused_before_anything_is_read(self):
    self.source.receive("first", 0.5, 0.5, 0.125)
    self.run_pass()
    with self.assertRaises(ValueError):
      self.cursor.finish(-1)
    self.assertEqual(self.target.perceptions, {})
    self.assertEqual(len(self.cursor.hits), 1)

class RunTest(unittest.TestCase):
  def setUp(self):
    self.scheduler = Scheduler({"scheduler": {"tick": 1.0, "budget": 0}})
    self.source = Plane({"uid": "A", "peak": 10.0})
    self.target = Plane({"uid": "C", "peak": 10.0})
    self.cursor = make_cursor(0.25, 0.5, 1.0, 0.0, self.source, self.target, step=0.125)
    self.cursor.start(self.scheduler)

  def ticks(self, count):
    self.scheduler.advance(float(count))

  def test_a_run_gives_back_the_number_of_perceptions_it_visited(self):
    self.source.receive("first", 0.5, 0.9, 0.0625)
    self.source.receive("second", 0.6, 0.9, 0.0625)
    self.assertEqual(self.cursor.run(10), 2)

  def test_a_started_cursor_waits_for_a_tick(self):
    self.assertEqual(self.cursor.segment, None)
    self.scheduler.advance(0.5)
    self.assertEqual(self.cursor.segment, None)

  def test_the_cursor_moves_by_its_step_at_every_tick_even_over_an_empty_plane(self):
    self.ticks(3)
    self.assertAlmostEqual(self.cursor.x, 0.625)
    self.assertEqual(self.cursor.segment, (0.5, 0.5, 0.625, 0.5))

  def test_the_perceptions_touched_by_a_move_are_read_at_the_end_of_the_next_pass(self):
    self.source.receive("first", 0.34375, 0.5, 0.0625)
    self.source.receive("second", 0.375, 0.5, 0.0625)
    self.ticks(1)
    self.assertEqual(self.target.perceptions, {})
    self.ticks(1)
    self.assertEqual(self.target.perceptions[("first", 0.34375, 0.5)].energy, 0.0625)
    self.assertEqual(self.target.perceptions[("second", 0.375, 0.5)].energy, 0.0625)

class CooldownTest(unittest.TestCase):
  def setUp(self):
    self.scheduler = Scheduler({"scheduler": {"tick": 1.0, "budget": 0}})
    self.source = Plane({"uid": "A", "peak": 10.0})
    self.target = Plane({"uid": "C", "peak": 10.0})
    self.source.receive("first", 0.5, 0.5, 0.125)
    self.perception = self.source.perceptions[("first", 0.5, 0.5)]
    self.cursor = self.make(2)

  def make(self, cooldown, target=None):
    cursor = make_cursor(0.25, 0.5, 1.0, 0.0, self.source, target or self.target, cooldown=cooldown)
    cursor.scheduler = self.scheduler
    return cursor

  def sweep(self, cursor=None):
    cursor = cursor or self.cursor
    cursor.x, cursor.y = 0.25, 0.5
    cursor.advance(0.5)
    self.source.visit(10, cursor.on_visit)
    return cursor.finish(0.0)

  def test_a_read_perception_is_marked_with_the_tick_of_its_reading(self):
    self.scheduler.advance(3.0)
    self.sweep()
    self.assertTrue(self.perception.read)
    self.assertEqual(self.perception.read_tick, 3)

  def test_a_read_perception_is_not_touched_again_during_the_cooldown(self):
    self.assertEqual(self.sweep(), 0.0625)
    self.scheduler.advance(1.0)
    self.assertEqual(self.sweep(), 0.0)
    self.assertEqual(self.perception.energy, 0.0625)

  def test_a_perception_is_touched_again_when_the_cooldown_is_over(self):
    self.sweep()
    self.scheduler.advance(2.0)
    self.assertEqual(self.sweep(), 0.0625)
    self.assertEqual(self.perception.read_tick, 2)

  def test_a_cooldown_of_zero_never_blocks(self):
    cursor = self.make(0)
    self.assertEqual(self.sweep(cursor), 0.0625)
    self.assertEqual(self.sweep(cursor), 0.0625)

  def test_a_perception_whose_target_refused_the_energy_is_still_marked_read(self):
    full = Plane({"uid": "C", "peak": 0.0625})
    full.receive("first", 0.5, 0.5, 0.0625)
    cursor = self.make(2, full)
    self.assertEqual(self.sweep(cursor), 0.0)
    self.assertTrue(self.perception.read)

  def test_the_mark_is_shared_between_the_cursors_of_a_plane(self):
    self.sweep()
    other = self.make(2)
    self.scheduler.advance(1.0)
    self.assertEqual(self.sweep(other), 0.0)

class AttractionTest(unittest.TestCase):
  def setUp(self):
    self.source = Plane({"uid": "A", "peak": 10.0})

  def turned(self, perceptions, attraction=1.0, distance_power=2.0, direction=(1.0, 0.0), elapsed=1):
    cursor = make_cursor(0.5, 0.5, *direction, self.source, attraction=attraction, distance_power=distance_power, step=STILL)
    for x, y, energy in perceptions:
      self.source.receive(f"p{x}-{y}", x, y, energy)
    self.source.visit(10, cursor.on_visit)
    cursor.finish(elapsed)
    return cursor

  def test_a_perception_turns_the_direction_toward_itself(self):
    cursor = self.turned([(0.5, 0.75, 0.0625)])
    self.assertAlmostEqual(cursor.dx, math.sqrt(0.5))
    self.assertAlmostEqual(cursor.dy, math.sqrt(0.5))

  def test_a_nearer_perception_turns_the_direction_more(self):
    near = self.turned([(0.5, 0.625, 0.03125)])
    self.source = Plane({"uid": "A", "peak": 10.0})
    far = self.turned([(0.5, 0.875, 0.03125)])
    self.assertGreater(near.dy, far.dy)

  def test_a_stronger_perception_turns_the_direction_more(self):
    weak = self.turned([(0.5, 0.75, 0.03125)])
    self.source = Plane({"uid": "A", "peak": 10.0})
    strong = self.turned([(0.5, 0.75, 0.125)])
    self.assertGreater(strong.dy, weak.dy)

  def test_without_attraction_the_direction_does_not_change(self):
    cursor = self.turned([(0.5, 0.75, 0.0625)], attraction=0.0)
    self.assertEqual((cursor.dx, cursor.dy), (1.0, 0.0))

  def test_a_distance_power_of_zero_ignores_the_distance(self):
    near = self.turned([(0.5, 0.625, 0.03125)], distance_power=0.0)
    self.source = Plane({"uid": "A", "peak": 10.0})
    far = self.turned([(0.5, 0.875, 0.03125)], distance_power=0.0)
    self.assertAlmostEqual(near.dy, far.dy)

  def test_a_perception_that_is_blocked_for_reading_exerts_no_attraction(self):
    cursor = make_cursor(0.5, 0.5, 1.0, 0.0, self.source, attraction=1.0, cooldown=5, step=STILL)
    self.source.receive("p", 0.5, 0.75, 0.0625)
    self.source.perceptions[("p", 0.5, 0.75)].read = True
    self.source.visit(10, cursor.on_visit)
    cursor.finish(1)
    self.assertEqual((cursor.dx, cursor.dy), (1.0, 0.0))

  def test_a_perception_attracts_again_once_its_cooldown_is_over(self):
    cursor = make_cursor(0.5, 0.5, 1.0, 0.0, self.source, attraction=1.0, cooldown=0, step=STILL)
    self.source.receive("p", 0.5, 0.75, 0.0625)
    self.source.perceptions[("p", 0.5, 0.75)].read = True
    self.source.visit(10, cursor.on_visit)
    cursor.finish(1)
    self.assertGreater(cursor.dy, 0.0)

  def test_a_perception_that_contains_the_cursor_exerts_nothing(self):
    cursor = self.turned([(0.5, 0.5, 0.125)])
    self.assertEqual((cursor.dx, cursor.dy), (1.0, 0.0))

  def test_two_opposite_perceptions_cancel_each_other(self):
    cursor = self.turned([(0.5, 0.75, 0.0625), (0.5, 0.25, 0.0625)])
    self.assertAlmostEqual(cursor.dx, 1.0)
    self.assertAlmostEqual(cursor.dy, 0.0)

  def test_a_force_that_cancels_the_direction_exactly_keeps_the_previous_direction(self):
    cursor = self.turned([(0.25, 0.5, 0.0625)])
    self.assertEqual((cursor.dx, cursor.dy), (1.0, 0.0))

  def test_the_direction_stays_normalized(self):
    cursor = self.turned([(0.5, 0.75, 0.0625), (0.75, 0.5, 0.125)])
    self.assertAlmostEqual(math.hypot(cursor.dx, cursor.dy), 1.0)

  def test_the_effect_of_the_attraction_is_proportional_to_the_elapsed_ticks(self):
    once = self.turned([(0.5, 0.75, 0.0625)], elapsed=1)
    self.source = Plane({"uid": "A", "peak": 10.0})
    twice = self.turned([(0.5, 0.75, 0.0625)], elapsed=2)
    self.assertAlmostEqual(twice.dy / twice.dx, 2 * once.dy / once.dx)

  def test_the_force_is_cleared_once_it_has_been_applied(self):
    cursor = self.turned([(0.5, 0.75, 0.0625)])
    direction = (cursor.dx, cursor.dy)
    cursor.finish(1)
    self.assertAlmostEqual(cursor.dx, direction[0])
    self.assertAlmostEqual(cursor.dy, direction[1])

class DeflectionTest(unittest.TestCase):
  def setUp(self):
    self.source = Plane({"uid": "A", "peak": 0.25})

  def read(self, energy=0.125, impact=1.0, others=()):
    cursor = make_cursor(0.25, 0.5, 1.0, 0.0, self.source, impact=impact, step=STILL)
    cursor.advance(0.5)
    self.source.receive("hit", 0.5, 0.5, energy)
    for name, x, y, other_energy in others:
      self.source.receive(name, x, y, other_energy)
    self.source.visit(10, cursor.on_visit)
    cursor.finish(1)
    return cursor

  def test_the_direction_is_deflected_toward_the_tangent_of_the_perception(self):
    cursor = self.read()
    self.assertAlmostEqual(cursor.dx, math.sqrt(0.5))
    self.assertAlmostEqual(cursor.dy, math.sqrt(0.5))

  def test_an_impact_of_zero_does_not_deflect(self):
    cursor = self.read(impact=0.0)
    self.assertEqual((cursor.dx, cursor.dy), (1.0, 0.0))

  def test_a_perception_with_more_energy_deflects_more(self):
    weak = self.read(energy=0.0625)
    self.source = Plane({"uid": "A", "peak": 0.25})
    strong = self.read(energy=0.125)
    self.assertGreater(strong.dy, weak.dy)

  def test_the_deflection_is_capped_at_the_tangent(self):
    cursor = self.read(impact=100.0)
    self.assertAlmostEqual(cursor.dx, 0.0)
    self.assertAlmostEqual(cursor.dy, 1.0)

  def test_the_side_of_the_tangent_follows_the_attraction(self):
    cursor = self.read(others=[("below", 0.75, 0.25, 0.0625)])
    self.assertLess(cursor.dy, 0.0)

  def test_the_cursor_is_placed_on_the_edge_of_what_is_left_of_the_perception(self):
    cursor = self.read()
    self.assertAlmostEqual(cursor.x, 0.5625, places=5)
    self.assertAlmostEqual(cursor.y, 0.5, places=5)

  def test_the_cursor_is_placed_at_the_center_of_a_perception_emptied_by_the_read(self):
    cursor = self.read(energy=0.03125)
    self.assertAlmostEqual(cursor.x, 0.5, places=5)
    self.assertAlmostEqual(cursor.y, 0.5, places=5)

  def test_a_cursor_at_the_center_of_the_perception_is_placed_opposite_to_its_direction(self):
    cursor = make_cursor(0.5, 0.5, 1.0, 0.0, self.source, step=STILL)
    self.source.receive("hit", 0.5, 0.5, 0.125)
    cursor.hits.append(self.source.perceptions[("hit", 0.5, 0.5)])
    cursor.finish(1)
    self.assertAlmostEqual(cursor.x, 0.4375, places=5)
    self.assertAlmostEqual(cursor.y, 0.5, places=5)

  def test_the_placement_stays_in_the_plane(self):
    cursor = make_cursor(0.99, 0.5, 1.0, 0.0, self.source, step=STILL)
    self.source.receive("hit", 0.9375, 0.5, 0.125)
    cursor.hits.append(self.source.perceptions[("hit", 0.9375, 0.5)])
    cursor.finish(1)
    self.assertAlmostEqual(cursor.x, 1.0, places=5)

  def test_a_perception_removed_before_the_end_of_the_pass_deflects_nothing(self):
    cursor = make_cursor(0.25, 0.5, 1.0, 0.0, self.source, impact=1.0, step=STILL)
    cursor.advance(0.5)
    self.source.receive("hit", 0.5, 0.5, 0.125)
    self.source.visit(10, cursor.on_visit)
    self.source.remove(cursor.hits[0])
    cursor.finish(1)
    self.assertEqual((cursor.dx, cursor.dy), (1.0, 0.0))
    self.assertAlmostEqual(cursor.x, 0.75)

class BudgetRunTest(unittest.TestCase):
  def setUp(self):
    self.scheduler = Scheduler({"scheduler": {"tick": 1.0, "budget": 2}})

  def plane(self, uid, count):
    plane = Plane({"uid": uid, "peak": 10.0})
    for index in range(count):
      plane.receive(f"far{index}", 0.1 * index, 0.9, 0.0625)
    return plane

  def started(self, uid, count):
    cursor = make_cursor(0.25, 0.5, 1.0, 0.0, self.plane(uid, count), step=0.125)
    cursor.start(self.scheduler)
    return cursor

  def ticks(self, count):
    self.scheduler.advance(float(count))

  def test_a_pass_cut_by_the_budget_moves_the_cursor_only_when_it_is_complete(self):
    cursor = self.started("A", 4)
    self.ticks(1)
    self.assertEqual(cursor.x, 0.25)
    self.ticks(1)
    self.assertAlmostEqual(cursor.x, 0.5)

  def test_a_pass_that_uses_exactly_the_budget_completes_in_one_tick(self):
    cursor = self.started("A", 2)
    self.ticks(3)
    self.assertAlmostEqual(cursor.x, 0.625)

  def test_two_cursors_share_the_budget_and_take_turns(self):
    first = self.started("A", 2)
    second = self.started("B", 2)
    self.ticks(1)
    self.assertAlmostEqual(first.x, 0.375)
    self.assertEqual(second.x, 0.25)
    self.ticks(1)
    self.assertAlmostEqual(first.x, 0.375)
    self.assertAlmostEqual(second.x, 0.5)
    self.ticks(1)
    self.assertAlmostEqual(first.x, 0.625)

  def test_a_placement_notes_the_tick_of_the_move(self):
    cursor = make_cursor(0.25, 0.5, 1.0, 0.0)
    cursor.scheduler = self.scheduler
    self.ticks(4)
    cursor.place(0.5, 0.5, 1.0, 0.0)
    self.assertEqual(cursor.moved_tick, 4)

  def test_the_end_of_a_pass_notes_the_tick_of_the_move(self):
    cursor = make_cursor(0.25, 0.5, 1.0, 0.0)
    cursor.scheduler = self.scheduler
    self.ticks(5)
    cursor.finish(1)
    self.assertEqual(cursor.moved_tick, 5)

class StateTest(unittest.TestCase):
  def test_the_state_gives_the_planes_the_position_and_the_direction_without_segment_before_the_first_move(self):
    cursor = make_cursor(0.25, 0.5, 3.0, 4.0)
    self.assertEqual(cursor.state(), {"source": "A", "target": "C", "x": 0.25, "y": 0.5, "dx": 0.6, "dy": 0.8, "segment": None})

  def test_the_state_gives_the_segment_of_the_last_move_as_a_list(self):
    cursor = make_cursor(0.25, 0.5, 1.0, 0.0)
    cursor.advance(0.5)
    self.assertEqual(cursor.state()["segment"], [0.25, 0.5, 0.75, 0.5])

  def test_the_state_can_be_written_as_json(self):
    cursor = make_cursor(0.25, 0.5, 1.0, 0.0)
    self.assertEqual(json.loads(json.dumps(cursor.state())), cursor.state())
    cursor.advance(0.5)
    self.assertEqual(json.loads(json.dumps(cursor.state())), cursor.state())

  def test_changing_the_state_does_not_change_the_cursor(self):
    cursor = make_cursor(0.25, 0.5, 1.0, 0.0)
    cursor.advance(0.5)
    state = cursor.state()
    state["segment"][0] = 9.0
    state["x"] = 9.0
    self.assertEqual(cursor.segment, (0.25, 0.5, 0.75, 0.5))
    self.assertEqual(cursor.x, 0.75)

class Script:
  def __init__(self, *values):
    self.values = list(values)

  def random(self):
    return self.values.pop(0)

class CycleTest(unittest.TestCase):
  def setUp(self):
    self.scheduler = Scheduler({"scheduler": {"tick": 1.0, "budget": 0}})

  def cursor(self, generator, cycle=3):
    cursor = make_cursor(0.25, 0.5, 1.0, 0.0, generator=generator, cycle=cycle)
    cursor.scheduler = self.scheduler
    return cursor

  def test_a_restart_places_the_cursor_inside_the_plane_with_a_unit_direction(self):
    cursor = make_cursor(0.5, 0.5, 1.0, 0.0, generator=Generator(4))
    for _ in range(20):
      cursor.restart()
      self.assertTrue(0.0 <= cursor.x <= 1.0)
      self.assertTrue(0.0 <= cursor.y <= 1.0)
      self.assertAlmostEqual(math.hypot(cursor.dx, cursor.dy), 1.0)

  def test_a_restart_draws_the_abscissa_then_the_ordinate_then_the_angle(self):
    cursor = make_cursor(0.5, 0.5, 1.0, 0.0, generator=Script(0.25, 0.75, 0.25))
    cursor.restart()
    self.assertEqual((cursor.x, cursor.y), (0.25, 0.75))
    self.assertAlmostEqual(cursor.dx, 0.0)
    self.assertAlmostEqual(cursor.dy, 1.0)

  def test_a_cursor_restarts_at_the_end_of_its_cycle(self):
    cursor = self.cursor(Script(0.25, 0.75, 0.0))
    self.scheduler.advance(3.0)
    cursor.finish(0.0)
    self.assertEqual((cursor.x, cursor.y), (0.25, 0.75))
    self.assertIsNone(cursor.segment)

  def test_a_cursor_does_not_restart_before_the_end_of_its_cycle(self):
    cursor = self.cursor(Script())
    self.scheduler.advance(2.0)
    cursor.finish(0.0)
    self.assertEqual((cursor.x, cursor.y), (0.25, 0.5))

  def test_the_next_cycle_is_counted_from_the_restart(self):
    cursor = self.cursor(Script(0.25, 0.75, 0.0, 0.5, 0.5, 0.0))
    self.scheduler.advance(3.0)
    cursor.finish(0.0)
    self.scheduler.advance(2.0)
    cursor.finish(0.0)
    self.assertEqual((cursor.x, cursor.y), (0.25, 0.75))
    self.scheduler.advance(1.0)
    cursor.finish(0.0)
    self.assertEqual((cursor.x, cursor.y), (0.5, 0.5))

  def test_starting_a_cursor_records_the_tick_where_its_cycle_begins(self):
    self.scheduler.advance(4.0)
    cursor = make_cursor(0.25, 0.5, 1.0, 0.0)
    cursor.start(self.scheduler)
    self.assertEqual(cursor.cycle_start, 4)

if __name__ == "__main__":
  unittest.main()
