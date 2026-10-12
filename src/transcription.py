import hashlib
import struct

def token_hash(token):
  return hashlib.sha256(token.encode("utf-8")).hexdigest()

def token_position(token):
  x, y = struct.unpack(">II", hashlib.sha256(token.encode("utf-8")).digest()[:8])
  return x / 4294967296.0, y / 4294967296.0
