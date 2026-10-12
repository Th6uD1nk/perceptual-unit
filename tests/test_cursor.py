import math
import unittest

import support
from cursor import Cursor
from perception import Perception
from plane import Plane

class CreationTest(unittest.TestCase):
  def test_the_direction_is_normalized(self):
    cursor = Cursor(0.5, 0.5, 3.0, 4.0)
    self.assertAlmostEqual(cursor.dx, 0.6)
    self.assertAlmostEqual(cursor.dy, 0.8)

  def test_a_null_direction_is_refused(self):
    with self.assertRaises(ValueError):
      Cursor(0.5, 0.5, 0.0, 0.0)

  def test_a_position_outside_the_plane_is_refused(self):
    for x, y in ((1.5, 0.5), (0.5, -0.1), (-0.1, 1.1)):
      with self.assertRaises(ValueError):
        Cursor(x, y, 1.0, 0.0)

  def test_a_position_on_the_edge_is_accepted(self):
    Cursor(0.0, 1.0, 1.0, 0.0)

  def test_there_is_no_segment_before_the_first_move(self):
    self.assertIsNone(Cursor(0.5, 0.5, 1.0, 0.0).segment)

class AdvanceTest(unittest.TestCase):
  def test_the_cursor_moves_along_its_direction_by_the_distance(self):
    cursor = Cursor(0.2, 0.2, 1.0, 0.0)
    cursor.advance(0.3)
    self.assertAlmostEqual(cursor.x, 0.5)
    self.assertAlmostEqual(cursor.y, 0.2)

  def test_a_diagonal_move_covers_the_requested_distance(self):
    cursor = Cursor(0.1, 0.1, 1.0, 1.0)
    cursor.advance(0.2)
    self.assertAlmostEqual(math.hypot(cursor.x - 0.1, cursor.y - 0.1), 0.2)

  def test_a_zero_distance_does_not_move_the_cursor(self):
    cursor = Cursor(0.4, 0.6, 1.0, 1.0)
    cursor.advance(0.0)
    self.assertEqual((cursor.x, cursor.y), (0.4, 0.6))

  def test_a_negative_distance_is_refused(self):
    with self.assertRaises(ValueError):
      Cursor(0.4, 0.6, 1.0, 1.0).advance(-0.1)

  def test_the_segment_goes_from_the_old_to_the_new_position(self):
    cursor = Cursor(0.2, 0.2, 1.0, 0.0)
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
      cursor = Cursor(*start)
      cursor.advance(0.3)
      for actual, wanted in zip((cursor.x, cursor.y, cursor.dx, cursor.dy), expected):
        self.assertAlmostEqual(actual, wanted, msg=repr(start))

  def test_the_cursor_bounces_on_two_edges_in_a_corner(self):
    cursor = Cursor(0.9, 0.9, 1.0, 1.0)
    cursor.advance(0.3 * math.sqrt(2))
    self.assertAlmostEqual(cursor.x, 0.8)
    self.assertAlmostEqual(cursor.y, 0.8)
    self.assertLess(cursor.dx, 0.0)
    self.assertLess(cursor.dy, 0.0)

  def test_the_cursor_stays_in_the_plane_whatever_the_distance(self):
    cursor = Cursor(0.3, 0.7, 2.0, 1.0)
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
  cursor = Cursor(0.25, 0.5, 1.0, 0.0)
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
    self.assertFalse(Cursor(0.25, 0.5, 1.0, 0.0).touches(perception(0.25, 0.5, 0.5)))

  def test_nothing_is_touched_by_a_move_of_zero_distance(self):
    cursor = Cursor(0.25, 0.5, 1.0, 0.0)
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

if __name__ == "__main__":
  unittest.main()
