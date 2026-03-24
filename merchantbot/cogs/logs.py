from __future__ import annotations

import discord
from discord.ext import commands

from merchantbot.bot import MerchantBot


class LogsCog(commands.Cog):
  def __init__(self, bot: MerchantBot) -> None:
    self.bot = bot

  @commands.Cog.listener()
  async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
    if before.guild.id != self.bot.settings.discord_guild_id:
      return
    fields: list[tuple[str, str]] = []
    if before.nick != after.nick:
      fields.append(("nickname", f"`{before.nick}` -> `{after.nick}`"))
    before_roles = {r.id for r in before.roles}
    after_roles = {r.id for r in after.roles}
    added = [r.mention for r in after.roles if r.id not in before_roles]
    removed = [r.mention for r in before.roles if r.id not in after_roles]
    if added:
      fields.append(("roles_added", ", ".join(added)))
    if removed:
      fields.append(("roles_removed", ", ".join(removed)))
    if fields:
      await self.bot.event_logger.send(
        title="Member Updated",
        description=f"{after.mention} profile changed.",
        fields=fields,
      )

  @commands.Cog.listener()
  async def on_message_delete(self, message: discord.Message) -> None:
    if not message.guild or message.guild.id != self.bot.settings.discord_guild_id or message.author.bot:
      return
    await self.bot.event_logger.send(
      title="Message Deleted",
      description=f"Message from {message.author.mention} deleted in {message.channel.mention}.",
      fields=[("content", (message.content or "[no text]")[:1024])],
      severity="warn",
    )

  @commands.Cog.listener()
  async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
    if not before.guild or before.guild.id != self.bot.settings.discord_guild_id or before.author.bot:
      return
    if before.content == after.content:
      return
    await self.bot.event_logger.send(
      title="Message Edited",
      description=f"{before.author.mention} edited a message in {before.channel.mention}.",
      fields=[("before", before.content[:1024] or "[no text]"), ("after", after.content[:1024] or "[no text]")],
    )

  @commands.Cog.listener()
  async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
    if channel.guild.id != self.bot.settings.discord_guild_id:
      return
    await self.bot.event_logger.send(
      title="Channel Created",
      description=f"{channel.mention if isinstance(channel, discord.TextChannel) else channel.name}",
    )

  @commands.Cog.listener()
  async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
    if channel.guild.id != self.bot.settings.discord_guild_id:
      return
    await self.bot.event_logger.send(
      title="Channel Deleted",
      description=channel.name,
      severity="warn",
    )


async def setup(bot: commands.Bot) -> None:
  assert isinstance(bot, MerchantBot)
  await bot.add_cog(LogsCog(bot), guild=discord.Object(id=bot.settings.discord_guild_id))

