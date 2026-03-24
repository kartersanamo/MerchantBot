from __future__ import annotations

import logging
from typing import Any

import discord


def configure_python_logging(level: str) -> None:
  logging.basicConfig(
    level=getattr(logging, level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
  )


class DiscordEventLogger:
  def __init__(self, *, bot: discord.Client, logs_channel_id: int) -> None:
    self.bot = bot
    self.logs_channel_id = logs_channel_id
    self.log = logging.getLogger("merchantbot.events")

  async def send(
    self,
    *,
    title: str,
    description: str,
    severity: str = "info",
    fields: list[tuple[str, str]] | None = None,
  ) -> None:
    color = _severity_color(severity)
    embed = discord.Embed(title=title, description=description, color=color)
    if fields:
      for name, value in fields:
        embed.add_field(name=name, value=value[:1024], inline=False)
    embed.set_footer(text=f"severity={severity}")

    channel = self.bot.get_channel(self.logs_channel_id)
    if not isinstance(channel, discord.TextChannel):
      try:
        fetched = await self.bot.fetch_channel(self.logs_channel_id)
      except Exception as exc:  # noqa: BLE001
        self.log.warning("Could not fetch log channel: %s", exc)
        return
      if not isinstance(fetched, discord.TextChannel):
        self.log.warning("Configured logs channel is not text channel")
        return
      channel = fetched

    try:
      await channel.send(embed=embed)
    except Exception as exc:  # noqa: BLE001
      self.log.warning("Failed sending log embed: %s", exc)

  async def exception(self, title: str, error: Exception, extra: dict[str, Any] | None = None) -> None:
    fields: list[tuple[str, str]] = [("error_type", error.__class__.__name__), ("error", str(error))]
    if extra:
      fields.extend((k, str(v)) for k, v in extra.items())
    await self.send(title=title, description="An exception occurred.", severity="error", fields=fields)


def _severity_color(severity: str) -> discord.Color:
  if severity == "error":
    return discord.Color.from_rgb(0, 224, 152)
  if severity == "warn":
    return discord.Color.from_rgb(0, 224, 152)
  if severity == "success":
    return discord.Color.from_rgb(0, 224, 152)
  return discord.Color.from_rgb(0, 224, 152)

