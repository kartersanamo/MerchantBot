from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import aiosqlite


class Storage:
  def __init__(self, db_path: Path) -> None:
    self._db_path = db_path

  async def setup(self) -> None:
    self._db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(self._db_path) as db:
      await db.executescript(
        """
        PRAGMA journal_mode=WAL;

        CREATE TABLE IF NOT EXISTS webhook_events (
          event_id TEXT PRIMARY KEY,
          event_type TEXT NOT NULL,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS panel_messages (
          panel_name TEXT NOT NULL,
          channel_id TEXT NOT NULL,
          message_id TEXT NOT NULL,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tickets (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ticket_number INTEGER NOT NULL,
          channel_id TEXT UNIQUE NOT NULL,
          owner_id TEXT NOT NULL,
          status TEXT NOT NULL,
          category_key TEXT NOT NULL,
          option_key TEXT NOT NULL,
          claimed_by_id TEXT,
          transcript_path TEXT,
          opened_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          closed_at DATETIME
        );

        CREATE TABLE IF NOT EXISTS ticket_meta (
          id INTEGER PRIMARY KEY CHECK (id = 1),
          next_ticket_number INTEGER NOT NULL
        );

        INSERT OR IGNORE INTO ticket_meta(id, next_ticket_number) VALUES (1, 1);

        CREATE TABLE IF NOT EXISTS ticket_messages (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ticket_channel_id TEXT NOT NULL,
          author_id TEXT NOT NULL,
          content TEXT,
          attachments_json TEXT,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
      )
      await db.commit()

  async def record_webhook_event(self, event_id: str, event_type: str) -> bool:
    async with aiosqlite.connect(self._db_path) as db:
      try:
        await db.execute(
          "INSERT INTO webhook_events(event_id, event_type) VALUES (?, ?)",
          (event_id, event_type),
        )
        await db.commit()
        return True
      except aiosqlite.IntegrityError:
        return False

  async def save_panel_message(self, panel_name: str, channel_id: int, message_id: int) -> None:
    async with aiosqlite.connect(self._db_path) as db:
      await db.execute(
        "INSERT INTO panel_messages(panel_name, channel_id, message_id) VALUES (?, ?, ?)",
        (panel_name, str(channel_id), str(message_id)),
      )
      await db.commit()

  async def next_ticket_number(self) -> int:
    async with aiosqlite.connect(self._db_path) as db:
      row = await (await db.execute("SELECT next_ticket_number FROM ticket_meta WHERE id = 1")).fetchone()
      current = int(row[0]) if row else 1
      await db.execute("UPDATE ticket_meta SET next_ticket_number = ? WHERE id = 1", (current + 1,))
      await db.commit()
      return current

  async def create_ticket(
    self,
    *,
    ticket_number: int,
    channel_id: int,
    owner_id: int,
    category_key: str,
    option_key: str,
  ) -> None:
    async with aiosqlite.connect(self._db_path) as db:
      await db.execute(
        """
        INSERT INTO tickets(ticket_number, channel_id, owner_id, status, category_key, option_key)
        VALUES (?, ?, ?, 'open', ?, ?)
        """,
        (ticket_number, str(channel_id), str(owner_id), category_key, option_key),
      )
      await db.commit()

  async def get_open_ticket_by_owner(self, owner_id: int) -> dict[str, Any] | None:
    async with aiosqlite.connect(self._db_path) as db:
      row = await (
        await db.execute(
          "SELECT ticket_number, channel_id, category_key, option_key FROM tickets WHERE owner_id = ? AND status = 'open' ORDER BY id DESC LIMIT 1",
          (str(owner_id),),
        )
      ).fetchone()
      if not row:
        return None
      return {
        "ticket_number": int(row[0]),
        "channel_id": int(row[1]),
        "category_key": row[2],
        "option_key": row[3],
      }

  async def count_open_tickets_by_owner(self, owner_id: int) -> int:
    async with aiosqlite.connect(self._db_path) as db:
      row = await (
        await db.execute(
          "SELECT COUNT(*) FROM tickets WHERE owner_id = ? AND status = 'open'",
          (str(owner_id),),
        )
      ).fetchone()
      return int(row[0]) if row else 0

  async def get_latest_ticket_timestamps(self, owner_id: int) -> dict[str, str | None]:
    async with aiosqlite.connect(self._db_path) as db:
      opened_row = await (
        await db.execute(
          "SELECT opened_at FROM tickets WHERE owner_id = ? ORDER BY id DESC LIMIT 1",
          (str(owner_id),),
        )
      ).fetchone()
      closed_row = await (
        await db.execute(
          """
          SELECT closed_at
          FROM tickets
          WHERE owner_id = ? AND status = 'closed' AND closed_at IS NOT NULL
          ORDER BY id DESC LIMIT 1
          """,
          (str(owner_id),),
        )
      ).fetchone()
      return {
        "opened_at": opened_row[0] if opened_row else None,
        "closed_at": closed_row[0] if closed_row else None,
      }

  async def get_ticket_by_channel(self, channel_id: int) -> dict[str, Any] | None:
    async with aiosqlite.connect(self._db_path) as db:
      row = await (
        await db.execute(
          """
          SELECT ticket_number, owner_id, status, category_key, option_key, claimed_by_id
          FROM tickets WHERE channel_id = ? LIMIT 1
          """,
          (str(channel_id),),
        )
      ).fetchone()
      if not row:
        return None
      return {
        "ticket_number": int(row[0]),
        "owner_id": int(row[1]),
        "status": row[2],
        "category_key": row[3],
        "option_key": row[4],
        "claimed_by_id": int(row[5]) if row[5] else None,
      }

  async def set_ticket_status(
    self,
    channel_id: int,
    *,
    status: str,
    claimed_by_id: int | None = None,
    transcript_path: str | None = None,
  ) -> None:
    async with aiosqlite.connect(self._db_path) as db:
      await db.execute(
        """
        UPDATE tickets
        SET status = ?,
            claimed_by_id = COALESCE(?, claimed_by_id),
            transcript_path = COALESCE(?, transcript_path),
            closed_at = CASE WHEN ? = 'closed' THEN CURRENT_TIMESTAMP ELSE closed_at END
        WHERE channel_id = ?
        """,
        (status, str(claimed_by_id) if claimed_by_id else None, transcript_path, status, str(channel_id)),
      )
      await db.commit()

  async def save_ticket_message(
    self,
    channel_id: int,
    author_id: int,
    content: str | None,
    attachments: list[str],
  ) -> None:
    async with aiosqlite.connect(self._db_path) as db:
      await db.execute(
        """
        INSERT INTO ticket_messages(ticket_channel_id, author_id, content, attachments_json)
        VALUES (?, ?, ?, ?)
        """,
        (str(channel_id), str(author_id), content or "", json.dumps(attachments)),
      )
      await db.commit()

  async def list_closed_tickets_for_owner(self, owner_id: int, limit: int = 20) -> list[dict[str, Any]]:
    async with aiosqlite.connect(self._db_path) as db:
      rows = await (
        await db.execute(
          """
          SELECT ticket_number, category_key, option_key, transcript_path, closed_at
          FROM tickets
          WHERE owner_id = ? AND status = 'closed'
          ORDER BY id DESC
          LIMIT ?
          """,
          (str(owner_id), limit),
        )
      ).fetchall()
      return [
        {
          "ticket_number": int(r[0]),
          "category_key": r[1],
          "option_key": r[2],
          "transcript_path": r[3],
          "closed_at": r[4],
        }
        for r in rows
      ]

