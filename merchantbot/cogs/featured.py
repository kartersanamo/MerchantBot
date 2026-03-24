from __future__ import annotations

from urllib.parse import urlparse

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from merchantbot.bot import MerchantBot


def _is_admin(member: discord.Member, admin_role_ids: list[int]) -> bool:
  if member.guild_permissions.administrator:
    return True
  if not admin_role_ids:
    return member.guild_permissions.manage_guild
  return any(role.id in set(admin_role_ids) for role in member.roles)


async def fetch_plugin_summary(url: str) -> dict[str, str]:
  plugin_name = url.rstrip("/").split("/")[-1].replace("-", " ").title()
  summary = "Featured plugin on MCMerchant."
  async with aiohttp.ClientSession() as session:
    try:
      async with session.get(url, timeout=10) as response:
        if response.status == 200:
          html = await response.text()
          if "<h1" in html:
            start = html.lower().find("<h1")
            end = html.lower().find("</h1>", start)
            if start != -1 and end != -1:
              content = html[html.find(">", start) + 1:end].strip()
              if content:
                plugin_name = content
    except Exception:
      pass
  return {"name": plugin_name, "summary": summary}


async def send_plugin_announcement(bot: MerchantBot, event_type: str, payload: dict) -> None:
  guild = bot.get_guild(bot.settings.discord_guild_id)
  if guild is None:
    return
  channel = guild.get_channel(bot.settings.loader_api_channel_id)
  if not isinstance(channel, discord.TextChannel):
    return
  plugin_name = payload.get("plugin_name", "Unknown Plugin")
  developer_name = payload.get("developer_name", "Unknown Developer")
  url = payload.get("url", bot.settings.mcmerchant_base_url)
  version_name = payload.get("version_name")
  changelog = payload.get("changelog")
  price_label = payload.get("price_label")
  title = "New Plugin Published" if event_type == "plugin.created" else "New Plugin Version Published"
  embed = discord.Embed(
    title=title,
    description=f"**{plugin_name}** by **{developer_name}**",
    color=discord.Color.from_rgb(0, 224, 152) if event_type == "plugin.created" else discord.Color.from_rgb(0, 224, 152),
    url=url,
  )
  if version_name:
    embed.add_field(name="Version", value=version_name, inline=True)
  if price_label:
    embed.add_field(name="Price", value=price_label, inline=True)
  if changelog:
    embed.add_field(name="Changelog", value=str(changelog)[:1024], inline=False)
  embed.add_field(name="Link", value=url, inline=False)
  await channel.send(embed=embed)


class FeaturedCog(commands.Cog):
  def __init__(self, bot: MerchantBot) -> None:
    self.bot = bot

  @app_commands.guild_only()
  @app_commands.command(name="feature", description="Feature a plugin in the featured channel.")
  async def feature(self, interaction: discord.Interaction, plugin_url: str) -> None:
    if not isinstance(interaction.user, discord.Member):
      await interaction.response.send_message("Guild-only command.", ephemeral=True)
      return
    if not _is_admin(interaction.user, self.bot.settings.parsed_admin_role_ids):
      await interaction.response.send_message("You do not have permission.", ephemeral=True)
      return
    parsed = urlparse(plugin_url)
    if parsed.scheme not in {"http", "https"}:
      await interaction.response.send_message("Invalid plugin URL.", ephemeral=True)
      return
    await interaction.response.send_message("Creating featured plugin post...", ephemeral=True)
    info = await fetch_plugin_summary(plugin_url)
    guild = interaction.guild
    channel = guild.get_channel(self.bot.settings.featured_channel_id)
    if not isinstance(channel, discord.TextChannel):
      await interaction.edit_original_response(content="Featured channel is not configured correctly.")
      return
    embed = discord.Embed(
      title=f"Featured: {info['name']}",
      description=info["summary"],
      color=discord.Color.from_rgb(0, 224, 152),
      url=plugin_url,
    )
    embed.add_field(name="Plugin Link", value=plugin_url, inline=False)
    await channel.send(embed=embed)
    await interaction.edit_original_response(content=f"Featured plugin posted to {channel.mention}.")


async def setup(bot: commands.Bot) -> None:
  assert isinstance(bot, MerchantBot)
  await bot.add_cog(FeaturedCog(bot), guild=discord.Object(id=bot.settings.discord_guild_id))

