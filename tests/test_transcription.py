import unittest

import support
from transcription import token_hash, token_position, tokenize

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

class TokenizeTest(unittest.TestCase):
  def test_the_text_is_split_on_spaces_and_punctuation_and_lowercased(self):
    self.assertEqual(tokenize("Hello, World!"), ["hello", "world"])

  def test_the_order_and_the_duplicates_are_kept(self):
    self.assertEqual(tokenize("a b a"), ["a", "b", "a"])

  def test_an_inner_apostrophe_is_kept_and_the_apostrophes_of_the_edges_are_not(self):
    self.assertEqual(tokenize("don't 'quoted'"), ["don't", "quoted"])

  def test_the_typographic_apostrophe_is_the_same_as_the_straight_one(self):
    self.assertEqual(tokenize("don\u2019t"), tokenize("don't"))

  def test_accents_digits_and_underscores_are_part_of_the_words(self):
    self.assertEqual(tokenize("café 42 snake_case"), ["café", "42", "snake_case"])

  def test_a_hyphen_separates_two_words(self):
    self.assertEqual(tokenize("well-known"), ["well", "known"])

  def test_a_text_without_any_word_gives_an_empty_list(self):
    for text in ("", "   ", "?!, ..."):
      self.assertEqual(tokenize(text), [], repr(text))

  def test_a_value_that_is_not_a_text_is_refused(self):
    for value in (3, None, ["a"]):
      with self.assertRaises(ValueError, msg=repr(value)):
        tokenize(value)

if __name__ == "__main__":
  unittest.main()
