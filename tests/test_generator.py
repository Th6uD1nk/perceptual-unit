import unittest

import support
from generator import Generator

class SequenceTest(unittest.TestCase):
  def test_the_first_outputs_of_the_seed_zero_are_the_published_ones(self):
    generator = Generator(0)
    self.assertEqual([generator.next() for _ in range(3)], [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4, 0x06C45D188009454F])

  def test_the_same_seed_gives_the_same_sequence(self):
    first = Generator(7)
    second = Generator(7)
    self.assertEqual([first.random() for _ in range(10)], [second.random() for _ in range(10)])

  def test_two_seeds_give_two_sequences(self):
    first = Generator(7)
    second = Generator(8)
    self.assertNotEqual([first.random() for _ in range(10)], [second.random() for _ in range(10)])

  def test_a_random_value_is_always_in_zero_inclusive_and_one_exclusive(self):
    generator = Generator(3)
    for _ in range(1000):
      self.assertTrue(0.0 <= generator.random() < 1.0)

class DrawTest(unittest.TestCase):
  def test_a_draw_is_always_in_zero_and_the_count_exclusive(self):
    generator = Generator(3)
    values = {generator.draw(7) for _ in range(1000)}
    self.assertEqual(values, set(range(7)))

  def test_a_count_below_one_is_refused(self):
    for count in (0, -3):
      with self.assertRaises(ValueError):
        Generator(3).draw(count)

class SeedTest(unittest.TestCase):
  def test_a_seed_must_be_an_integer_of_at_least_zero(self):
    for seed in (-1, 1.5, "1", None, True):
      with self.assertRaises(ValueError, msg=repr(seed)):
        Generator(seed)

if __name__ == "__main__":
  unittest.main()
