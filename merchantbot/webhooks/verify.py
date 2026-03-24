from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class VerifySyncedPayload:
  discord_user_id: int
  username: str


@dataclass(slots=True)
class VerifyUnsyncedPayload:
  discord_user_id: int

