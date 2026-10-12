import unittest

import support
from transcription import token_hash, token_position

class HashTest(unittest.TestCase):
  def test_the_hash_of_a_token_is_its_sha256_in_hexadecimal(self):
    self.assertEqual(token_hash("abc"), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

  def test_two_tokens_have_two_hashes(self):
    self.assertNotEqual(token_hash("house"), token_hash("cat"))

  def test_a_token_with_accents_has_a_hash_of_the_same_length(self):
    self.assertEqual(len(token_hash("café")), 64)

class PositionTest(unittest.TestCase):
  def test_a_token_always_gets_the_same_position(self):
    self.assertEqual(token_position("house"), token_position("house"))

  def test_two_tokens_get_two_positions(self):
    self.assertNotEqual(token_position("house"), token_position("cat"))

  def test_a_position_is_always_in_zero_inclusive_and_one_exclusive(self):
    for index in range(500):
      x, y = token_position(f"token{index}")
      self.assertTrue(0.0 <= x < 1.0)
      self.assertTrue(0.0 <= y < 1.0)

if __name__ == "__main__":
  unittest.main()
