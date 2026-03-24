from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import discord
from discord.ext import commands

from merchantbot.config import Settings
from merchantbot.logging import DiscordEventLogger
from merchantbot.storage import Storage

log = logging.getLogger("merchantbot.bot")


class MerchantBot(commands.Bot):
  def __init__(self, settings: Settings) -> None:
    intents = discord.Intents.default()
    intents.members = True
    intents.guilds = True
    intents.messages = True
    intents.message_content = False

    super().__init__(command_prefix="!", intents=intents)
    self.settings = settings
    self.storage = Storage(settings.database_file)
    self.event_logger = DiscordEventLogger(bot=self, logs_channel_id=settings.logs_channel_id)
    self.webhook_runner: asyncio.Task[None] | None = None

  async def setup_hook(self) -> None:
    await self.storage.setup()
    for extension in (
      "merchantbot.cogs.panels",
      "merchantbot.cogs.verification",
      "merchantbot.cogs.welcome",
      "merchantbot.cogs.logs",
      "merchantbot.cogs.featured",
      "merchantbot.cogs.lookup",
      "merchantbot.ticketsystem.Cogs.sendtickets",
      "merchantbot.ticketsystem.Cogs.close",
      "merchantbot.ticketsystem.Cogs.private",
      "merchantbot.ticketsystem.Cogs.move",
      "merchantbot.ticketsystem.Cogs.rename",
      "merchantbot.ticketsystem.Cogs.add",
      "merchantbot.ticketsystem.Cogs.remove",
      "merchantbot.ticketsystem.Cogs.blacklist",
      "merchantbot.ticketsystem.Cogs.blacklistlist",
      "merchantbot.ticketsystem.Cogs.ticketlogs",
      "merchantbot.ticketsystem.Cogs.ticketcount",
      "merchantbot.ticketsystem.Cogs.activetickets",
      "merchantbot.ticketsystem.Cogs.oldest",
      "merchantbot.ticketsystem.Cogs.managetickets",
      "merchantbot.ticketsystem.Cogs.logs",
    ):
      await self.load_extension(extension)

    # Register persistent views.
    from merchantbot.ui.information import InformationPanelView
    from merchantbot.ui.verification import VerifyPanelView
    from merchantbot.ticketsystem.Cogs.sendtickets import TicketsView, TicketLogs
    from merchantbot.ui.getting_started import GettingStartedPanelView
    from merchantbot.ui.loader_api import LoaderApiPanelView

    self.add_view(InformationPanelView(self))
    self.add_view(VerifyPanelView(self))
    self.add_view(TicketsView())
    self.add_view(TicketLogs())
    self.add_view(GettingStartedPanelView())
    self.add_view(LoaderApiPanelView())

    from merchantbot.webhooks.server import start_webhook_server

    self.webhook_runner = asyncio.create_task(start_webhook_server(self), name="merchantbot-webhooks")

  async def on_ready(self) -> None:
    guild = discord.Object(id=self.settings.discord_guild_id)
    synced = await self.tree.sync(guild=guild)
    log.info("Logged in as %s (%s)", self.user, self.user.id if self.user else "?")
    log.info("Synced %s guild commands", len(synced))
    await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="MCMerchant"))
    await self.event_logger.send(
      title="Bot Started",
      description=f"MerchantBot is online as {self.user}.",
      severity="success",
    )

  async def close(self) -> None:
    if self.webhook_runner:
      self.webhook_runner.cancel()
    await super().close()

  @property
  def transcripts_dir(self) -> Path:
    path = Path("transcripts")
    path.mkdir(parents=True, exist_ok=True)
    return path

