import unittest

import support
from lexicon import Lexicon
from transcription import token_hash

class AddTest(unittest.TestCase):
  def setUp(self):
    self.lexicon = Lexicon(0.3)

  def test_a_word_is_known_by_its_hash(self):
    hash_ = self.lexicon.add("house")
    self.assertEqual(hash_, token_hash("house"))
    self.assertEqual(self.lexicon.word(hash_), "house")

  def test_adding_a_known_word_again_changes_nothing(self):
    self.lexicon.add("cat")
    self.lexicon.add("cats")
    before = self.lexicon.similar(token_hash("cat"))
    self.assertEqual(self.lexicon.add("cat"), token_hash("cat"))
    self.assertEqual(self.lexicon.similar(token_hash("cat")), before)
    self.assertEqual(len(self.lexicon.words), 2)

  def test_an_unknown_hash_gives_no_word_and_no_similar_word(self):
    self.assertIsNone(self.lexicon.word("unknown"))
    self.assertEqual(self.lexicon.similar("unknown"), {})

  def test_a_word_must_be_a_non_empty_string(self):
    for word in ("", 3, None, ["cat"]):
      with self.assertRaises(ValueError, msg=repr(word)):
        self.lexicon.add(word)

class SimilarityTest(unittest.TestCase):
  def test_the_similarity_is_the_dice_coefficient_of_the_bracketed_bigrams(self):
    lexicon = Lexicon(0.3)
    lexicon.add("cat")
    lexicon.add("cats")
    self.assertAlmostEqual(lexicon.similar(token_hash("cat"))[token_hash("cats")], 2 * 3 / (4 + 5))

  def test_the_similarity_is_the_same_in_both_directions_and_whatever_the_order_of_arrival(self):
    first = Lexicon(0.3)
    first.add("cat")
    first.add("cats")
    second = Lexicon(0.3)
    second.add("cats")
    second.add("cat")
    for lexicon in (first, second):
      self.assertEqual(lexicon.similar(token_hash("cat"))[token_hash("cats")], lexicon.similar(token_hash("cats"))[token_hash("cat")])
    self.assertEqual(first.similar(token_hash("cat")), second.similar(token_hash("cat")))

  def test_two_words_with_no_bigram_in_common_are_not_similar(self):
    lexicon = Lexicon(0.3)
    lexicon.add("cat")
    lexicon.add("dog")
    self.assertEqual(lexicon.similar(token_hash("cat")), {})

  def test_a_word_is_not_similar_to_itself(self):
    lexicon = Lexicon(0.3)
    lexicon.add("cat")
    self.assertEqual(lexicon.similar(token_hash("cat")), {})

  def test_a_similarity_below_the_floor_is_not_kept_and_one_at_the_floor_is(self):
    kept = Lexicon(2 * 3 / (4 + 5))
    dropped = Lexicon(0.7)
    for lexicon in (kept, dropped):
      lexicon.add("cat")
      lexicon.add("cats")
    self.assertIn(token_hash("cats"), kept.similar(token_hash("cat")))
    self.assertEqual(dropped.similar(token_hash("cat")), {})

  def test_the_answer_is_independent_of_the_stored_similarities(self):
    lexicon = Lexicon(0.3)
    lexicon.add("cat")
    lexicon.add("cats")
    lexicon.similar(token_hash("cat"))[token_hash("cats")] = 9.0
    self.assertAlmostEqual(lexicon.similar(token_hash("cat"))[token_hash("cats")], 2 * 3 / (4 + 5))

class FloorTest(unittest.TestCase):
  def test_the_floor_must_be_a_number_greater_than_zero_and_at_most_one(self):
    for floor in (0, -0.1, 1.1, "0.3", None, True):
      with self.assertRaises(ValueError, msg=repr(floor)):
        Lexicon(floor)

  def test_a_floor_of_one_is_accepted(self):
    Lexicon(1)

if __name__ == "__main__":
  unittest.main()
