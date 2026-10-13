import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from types import SimpleNamespace

from moments import Moments

def moments(moment=0, window=2):
  return Moments(SimpleNamespace(moment=moment), window)
