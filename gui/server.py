import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

GUI_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(GUI_DIR.parent / "src"))

from unit import Unit

CONFIG_PATH = GUI_DIR / "config.json"
PAGE_PATH = GUI_DIR / "index.html"
HOST = "127.0.0.1"
DEFAULT_PORT = 8100
TOKEN_ENERGY = 0.0625

def load_unit(path=CONFIG_PATH):
  return Unit(json.loads(Path(path).read_text()))

class Handler(BaseHTTPRequestHandler):
  def do_GET(self):
    if self.path == "/":
      self.send_body(200, "text/html; charset=utf-8", PAGE_PATH.read_bytes())
    elif self.path == "/api/state":
      self.send_json(200, self.server.unit.state())
    else:
      self.send_error(404)

  def do_POST(self):
    if self.path != "/api/token":
      self.send_error(404)
      return
    try:
      payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
      if not isinstance(payload, dict):
        raise ValueError("body: must be an object")
      self.server.unit.feed(payload.get("token"), TOKEN_ENERGY)
    except ValueError as error:
      self.send_json(400, {"error": str(error)})
      return
    self.send_json(200, self.server.unit.state())

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

def make_server(unit, port):
  server = ThreadingHTTPServer((HOST, port), Handler)
  server.unit = unit
  return server

def main(arguments):
  port = int(arguments[0]) if arguments else DEFAULT_PORT
  server = make_server(load_unit(), port)
  print(f"Serving the perceptual unit on http://{HOST}:{port}")
  try:
    server.serve_forever()
  except KeyboardInterrupt:
    pass
  finally:
    server.server_close()

if __name__ == "__main__":
  main(sys.argv[1:])
