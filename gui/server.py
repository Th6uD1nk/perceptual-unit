import json
import sys
from pathlib import Path

GUI_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(GUI_DIR.parent / "src"))

from unit import Unit

CONFIG_PATH = GUI_DIR / "config.json"

def load_unit(path=CONFIG_PATH):
  return Unit(json.loads(Path(path).read_text()))
