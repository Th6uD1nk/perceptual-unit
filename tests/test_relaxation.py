import math
import unittest

import support
from memory import Memory
from plane import Plane
from relaxation import Relaxation
from scheduler import Scheduler
from transcription import token_hash

CONFIG = {"memory": {"floor": 0.3, "threshold": 0.5, "orbit": [0.05, 0.1], "window": 2, "recent": 3, "decay": 0.3, "range": 0.5, "rest": 0.03, "far": 0.25, "base": 0.2, "rate": 1.0, "coexpression": 1.0, "kappa": 1.0, "amplify": 2.0}}

class RelaxationTest(unittest.TestCase):
  def setUp(self):
    self.memory = Memory(CONFIG)
    self.plane = Plane({"uid": "A", "peak": 4.0}, support.moments())
    self.relaxation = Relaxation(self.memory, self.plane)

  def add(self, word, x, y, energy=1.0):
    self.memory.add(word)
    self.plane.receive(token_hash(word), x, y, energy)
    return self.plane.perceptions[(token_hash(word), x, y, 0)]

  def scheduler(self, budget=0):
    scheduler = Scheduler({"scheduler": {"tick": 1.0, "budget": budget, "moment": 1000}})
    self.relaxation.start(scheduler)
    return scheduler

  def test_a_visited_perception_is_moved_to_the_position_of_the_pull_and_keyed_there(self):
    cat = self.add("cat", 0.3, 0.5)
    self.add("cats", 0.7, 0.5)
    x, y, _ = self.memory.pull(cat, self.plane)
    self.relaxation.on_visit(cat)
    self.assertEqual((cat.x, cat.y), (x, y))
    self.assertIs(self.plane.perceptions[cat.key], cat)

  def test_the_visit_gives_back_the_cost_of_the_pull(self):
    cat = self.add("cat", 0.3, 0.5)
    self.add("dog", 0.5, 0.5)
    self.add("cats", 0.6, 0.5)
    self.assertEqual(self.relaxation.on_visit(cat), 2)

  def test_similar_words_come_closer_over_the_passes_of_the_plane(self):
    cat = self.add("cat", 0.3, 0.5)
    cats = self.add("cats", 0.7, 0.5)
    self.scheduler().advance(5.0)
    self.assertLess(math.hypot(cat.x - cats.x, cat.y - cats.y), 0.4)

  def test_nothing_happens_on_an_empty_plane(self):
    self.scheduler().advance(5.0)
    self.assertEqual(self.plane.perceptions, {})

  def test_a_pass_cut_by_the_budget_moves_only_the_perceptions_already_visited(self):
    perceptions = [self.add(word, x, y) for word, x, y in (("cat", 0.2, 0.2), ("dog", 0.5, 0.2), ("pig", 0.2, 0.5), ("cow", 0.5, 0.5))]
    before = [(perception.x, perception.y) for perception in perceptions]
    self.scheduler(budget=4).advance(1.0)
    moved = [(perception.x, perception.y) != position for perception, position in zip(perceptions, before)]
    self.assertEqual(moved, [True, True, False, False])

  def test_the_energy_of_the_plane_is_neither_created_nor_lost(self):
    for word, x, y, energy in (("cat", 0.2, 0.2, 1.0), ("cats", 0.5, 0.2, 2.0), ("dog", 0.2, 0.5, 0.5), ("pig", 0.5, 0.5, 1.5)):
      self.add(word, x, y, energy)
    self.scheduler().advance(50.0)
    self.assertAlmostEqual(sum(perception.energy for perception in self.plane.perceptions.values()), 5.0)

  def test_the_relaxation_and_another_step_share_one_pass_and_the_greatest_cost_counts(self):
    for word, x, y in (("cat", 0.2, 0.2), ("dog", 0.5, 0.2), ("pig", 0.2, 0.5), ("cow", 0.5, 0.5)):
      self.add(word, x, y)
    seen = []
    scheduler = Scheduler({"scheduler": {"tick": 1.0, "budget": 0, "moment": 1000}})
    self.plane.register(scheduler, lambda perception: seen.append(perception.hash))
    self.relaxation.start(scheduler)
    self.assertEqual(self.plane.run(100), 12)
    self.assertEqual(len(seen), 4)

if __name__ == "__main__":
  unittest.main()
