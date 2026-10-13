import unittest

import support
from spring import spring_force

class ForceTest(unittest.TestCase):
  def test_the_force_is_zero_at_the_rest_distance(self):
    self.assertEqual(spring_force(0.2, 0.2, 1.0), 0.0)

  def test_the_force_attracts_beyond_the_rest_distance_and_repels_below_it(self):
    self.assertGreater(spring_force(0.5, 0.2, 1.0), 0.0)
    self.assertLess(spring_force(0.1, 0.2, 1.0), 0.0)

  def test_the_force_is_zero_at_the_reach_and_beyond_it(self):
    for distance in (1.0, 1.5):
      self.assertEqual(spring_force(distance, 0.2, 1.0), 0.0, distance)

  def test_the_force_is_zero_for_a_distance_that_is_not_positive(self):
    for distance in (0.0, -0.1):
      self.assertEqual(spring_force(distance, 0.2, 1.0), 0.0, distance)

  def test_the_force_has_the_values_of_the_cubic_profile(self):
    self.assertAlmostEqual(spring_force(1 / 3, 0.0, 1.0), 0.25)
    self.assertAlmostEqual(spring_force(0.6, 0.2, 1.0), 0.135)

  def test_a_rest_distance_that_reaches_the_reach_leaves_the_profile_unscaled(self):
    self.assertAlmostEqual(spring_force(0.5, 1.0, 1.0), -0.125)
    self.assertAlmostEqual(spring_force(0.5, 2.0, 1.0), -0.375)

  def test_a_reach_that_is_not_positive_or_a_negative_rest_is_refused(self):
    with self.assertRaises(ValueError):
      spring_force(0.5, 0.2, 0.0)
    with self.assertRaises(ValueError):
      spring_force(0.5, -0.1, 1.0)

if __name__ == "__main__":
  unittest.main()
