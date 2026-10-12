import unittest

import support
from plane import Plane

class PlaneTest(unittest.TestCase):
  def test_a_new_plane_holds_no_perception(self):
    self.assertEqual(Plane({"uid": "A"}).perceptions, {})

  def test_two_planes_do_not_share_their_perceptions(self):
    first = Plane({"uid": "A"})
    second = Plane({"uid": "C"})
    first.perceptions["key"] = "value"
    self.assertEqual(second.perceptions, {})

if __name__ == "__main__":
  unittest.main()
