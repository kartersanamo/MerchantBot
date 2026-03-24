from __future__ import annotations

import discord
from discord.ext import commands

from merchantbot.bot import MerchantBot


class WelcomeCog(commands.Cog):
  def __init__(self, bot: MerchantBot) -> None:
    self.bot = bot

  @commands.Cog.listener()
  async def on_member_join(self, member: discord.Member) -> None:
    if member.guild.id != self.bot.settings.discord_guild_id:
      return
    channel = member.guild.get_channel(self.bot.settings.welcome_channel_id)
    if not isinstance(channel, discord.TextChannel):
      return
    embed = discord.Embed(
      title="Welcome to MCMerchant",
      description=(
        f"Hey {member.mention}, welcome to the official MCMerchant Discord.\n\n"
        "Use the verify channel to sync your account and unlock full access."
      ),
      color=discord.Color.from_rgb(0, 224, 152),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await channel.send(embed=embed)

  @commands.Cog.listener()
  async def on_member_remove(self, member: discord.Member) -> None:
    if member.guild.id != self.bot.settings.discord_guild_id:
      return
    channel = member.guild.get_channel(self.bot.settings.welcome_channel_id)
    if not isinstance(channel, discord.TextChannel):
      return
    embed = discord.Embed(
      description=f"**{member}** left the server.",
      color=discord.Color.from_rgb(0, 224, 152),
    )
    await channel.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
  assert isinstance(bot, MerchantBot)
  await bot.add_cog(WelcomeCog(bot), guild=discord.Object(id=bot.settings.discord_guild_id))

