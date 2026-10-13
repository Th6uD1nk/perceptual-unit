import unittest

import support
from memory import Memory
from transcription import token_hash, token_position

CONFIG = {"memory": {"floor": 0.3}}

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

  def test_the_floor_must_be_a_number_greater_than_zero_and_at_most_one(self):
    for floor in (0, -0.1, 1.1, "0.3", None, True):
      self.assertIn("config.memory.floor", self.rejected({"memory": {"floor": floor}}), repr(floor))

if __name__ == "__main__":
  unittest.main()
