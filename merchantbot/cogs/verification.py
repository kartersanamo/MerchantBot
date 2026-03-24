from __future__ import annotations

import discord
from discord.ext import commands

from merchantbot.bot import MerchantBot


async def apply_verified_state(*, bot: MerchantBot, discord_user_id: int, username: str) -> None:
  guild = bot.get_guild(bot.settings.discord_guild_id)
  if guild is None:
    return
  member = guild.get_member(discord_user_id)
  if member is None:
    member = await guild.fetch_member(discord_user_id)
  role = guild.get_role(bot.settings.verified_role_id)
  if role and role not in member.roles:
    await member.add_roles(role, reason="MCMerchant account synced")
  await member.edit(nick=username[:32], reason="MCMerchant account synced")
  await bot.event_logger.send(
    title="Member Verified",
    description=f"{member.mention} synced their account.",
    severity="success",
    fields=[("username", username)],
  )


async def remove_verified_state(*, bot: MerchantBot, discord_user_id: int) -> None:
  guild = bot.get_guild(bot.settings.discord_guild_id)
  if guild is None:
    return
  member = guild.get_member(discord_user_id)
  if member is None:
    member = await guild.fetch_member(discord_user_id)
  role = guild.get_role(bot.settings.verified_role_id)
  if role and role in member.roles:
    await member.remove_roles(role, reason="MCMerchant account unsynced")
  await member.edit(nick=None, reason="MCMerchant account unsynced")
  await bot.event_logger.send(
    title="Member Unverified",
    description=f"{member.mention} unsynced their account.",
    severity="warn",
  )


class VerificationCog(commands.Cog):
  def __init__(self, bot: MerchantBot) -> None:
    self.bot = bot


async def setup(bot: commands.Bot) -> None:
  assert isinstance(bot, MerchantBot)
  await bot.add_cog(VerificationCog(bot), guild=discord.Object(id=bot.settings.discord_guild_id))

