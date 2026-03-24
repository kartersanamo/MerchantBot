from __future__ import annotations

import hashlib
import hmac
import time


def verify_hmac_signature(*, raw_body: bytes, timestamp: str, signature: str, secret: str) -> bool:
  if not timestamp or not signature or not secret:
    return False
  try:
    ts = int(timestamp)
  except ValueError:
    return False
  if abs(int(time.time()) - ts) > 300:
    return False

  payload = f"{timestamp}.".encode("utf-8") + raw_body
  digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
  # Allow either raw hex or prefixed form.
  normalized = signature.removeprefix("sha256=")
  return hmac.compare_digest(digest, normalized)

