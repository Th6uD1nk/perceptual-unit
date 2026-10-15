import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

GUI_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(GUI_DIR.parent / "src"))

from transcription import tokenize
from unit import Unit

CONFIG_PATH = GUI_DIR / "config.json"
PAGE_PATH = GUI_DIR / "index.html"
HOST = "127.0.0.1"
DEFAULT_PORT = 8100
CLOCK_INTERVAL_MS = 20

def read_config(path):
  return json.loads(Path(path).read_text())

def input_energy(config):
  section = config.get("input") if isinstance(config, dict) else None
  if not isinstance(section, dict) or "energy" not in section:
    raise ValueError("config.input.energy: missing")
  energy = section["energy"]
  if isinstance(energy, bool) or not isinstance(energy, (int, float)) or energy <= 0:
    raise ValueError("config.input.energy: must be a number greater than 0")
  return energy

def load_unit(path=CONFIG_PATH):
  return Unit(read_config(path))

def load_input_energy(path=CONFIG_PATH):
  return input_energy(read_config(path))

class Handler(BaseHTTPRequestHandler):
  def do_GET(self):
    if self.path == "/":
      self.send_body(200, "text/html; charset=utf-8", PAGE_PATH.read_bytes())
    elif self.path == "/api/state":
      with self.server.lock:
        state = self.server.unit.state()
      self.send_json(200, state)
    else:
      self.send_error(404)

  def do_POST(self):
    if self.path == "/api/reset":
      with self.server.lock:
        self.server.unit = Unit(self.server.unit.config)
        state = self.server.unit.state()
      self.send_json(200, state)
      return
    if self.path != "/api/text":
      self.send_error(404)
      return
    try:
      payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
      if not isinstance(payload, dict):
        raise ValueError("body: must be an object")
      words = tokenize(payload.get("text"))
      with self.server.lock:
        self.server.unit.feed_flow(words, self.server.energy)
        state = self.server.unit.state()
    except ValueError as error:
      self.send_json(400, {"error": str(error)})
      return
    self.send_json(200, state)

  def send_json(self, status, payload):
    self.send_body(status, "application/json", json.dumps(payload).encode("utf-8"))

  def send_body(self, status, content_type, body):
    self.send_response(status)
    self.send_header("Content-Type", content_type)
    self.send_header("Content-Length", str(len(body)))
    self.end_headers()
    self.wfile.write(body)

  def log_message(self, format, *args):
    pass

def step_clock(server, elapsed_ms):
  with server.lock:
    return server.unit.update(elapsed_ms)

def start_clock(server, interval_ms):
  stop = threading.Event()

  def run():
    last = time.monotonic()
    while not stop.wait(interval_ms / 1000.0):
      now = time.monotonic()
      step_clock(server, (now - last) * 1000.0)
      last = now

  threading.Thread(target=run, daemon=True).start()
  return stop

def make_server(unit, port, energy):
  server = ThreadingHTTPServer((HOST, port), Handler)
  server.unit = unit
  server.energy = energy
  server.lock = threading.Lock()
  return server

def main(arguments):
  port = int(arguments[0]) if arguments else DEFAULT_PORT
  server = make_server(load_unit(), port, load_input_energy())
  stop_clock = start_clock(server, CLOCK_INTERVAL_MS)
  print(f"Serving the perceptual unit on http://{HOST}:{port}")
  try:
    server.serve_forever()
  except KeyboardInterrupt:
    pass
  finally:
    stop_clock.set()
    server.server_close()

if __name__ == "__main__":
  main(sys.argv[1:])
