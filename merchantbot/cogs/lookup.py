from __future__ import annotations

from typing import Any
from urllib.parse import quote

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from merchantbot.bot import MerchantBot


class LookupCog(commands.Cog):
  def __init__(self, bot: MerchantBot) -> None:
    self.bot = bot

  @app_commands.guild_only()
  @app_commands.command(
    name="verify-license",
    description="Verify a license key and return its status.",
  )
  async def verify_license(self, interaction: discord.Interaction, license: str) -> None:
    await interaction.response.defer(ephemeral=True, thinking=True)
    base = self.bot.settings.mcmerchant_base_url.rstrip("/")
    headers = {"Content-Type": "application/json"}
    if self.bot.settings.mcmerchant_bot_api_key:
      headers["x-mcmerchant-bot-key"] = self.bot.settings.mcmerchant_bot_api_key

    payload = {"license_key": license.strip()}
    url = f"{base}/api/v1/licenses/lookup"
    try:
      async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload, timeout=12) as response:
          data = await response.json(content_type=None)
    except Exception as exc:  # noqa: BLE001
      await interaction.followup.send(
        f"Could not verify license right now. Error: `{exc}`",
        ephemeral=True,
      )
      return

    if not isinstance(data, dict):
      await interaction.followup.send("Unexpected response from license service.", ephemeral=True)
      return

    if not data.get("found"):
      await interaction.followup.send(
        "License not found or invalid.",
        ephemeral=True,
      )
      return

    status = str(data.get("status", "unknown"))
    plugin_name = str(data.get("plugin_name", "Unknown"))
    plugin_slug = str(data.get("plugin_slug", "") or "")
    buyer = str(data.get("buyer_username", "Unknown"))
    expires_at = str(data.get("expires_at", "Never"))
    issued_at = str(data.get("issued_at", "Unknown"))
    key_preview = str(data.get("license_key_preview", "N/A"))

    embed = discord.Embed(
      title="License Verification",
      color=discord.Color.from_rgb(0, 224, 152) if status == "active" else discord.Color.from_rgb(0, 224, 152),
    )
    embed.add_field(name="Status", value=status, inline=True)
    embed.add_field(name="Plugin", value=plugin_name, inline=True)
    embed.add_field(name="Buyer", value=buyer, inline=True)
    embed.add_field(name="Issued", value=issued_at, inline=True)
    embed.add_field(name="Expires", value=expires_at, inline=True)
    embed.add_field(name="License", value=key_preview, inline=False)
    if plugin_slug:
      embed.add_field(
        name="Plugin Link",
        value=f"{base}/plugin/{plugin_slug}",
        inline=False,
      )
    await interaction.followup.send(embed=embed, ephemeral=True)

  @app_commands.guild_only()
  @app_commands.command(
    name="plugin-info",
    description="Look up a plugin by name and post info publicly.",
  )
  async def plugin_info(self, interaction: discord.Interaction, name: str) -> None:
    await interaction.response.defer(ephemeral=False, thinking=True)
    base = self.bot.settings.mcmerchant_base_url.rstrip("/")
    url = f"{base}/api/v1/plugins/search?q={quote(name.strip())}"
    headers = {}
    if self.bot.settings.mcmerchant_bot_api_key:
      headers["x-mcmerchant-bot-key"] = self.bot.settings.mcmerchant_bot_api_key

    try:
      async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=12) as response:
          data = await response.json(content_type=None)
    except Exception as exc:  # noqa: BLE001
      await interaction.followup.send(f"Could not load plugin info right now. Error: `{exc}`")
      return

    if not isinstance(data, dict):
      await interaction.followup.send("Unexpected response from plugin search service.")
      return

    plugins = data.get("plugins")
    if not isinstance(plugins, list) or not plugins:
      await interaction.followup.send(f"No plugin found for `{name}`.")
      return

    best = self._pick_best_plugin(name, plugins)
    plugin_name = str(best.get("name", "Unknown"))
    plugin_slug = str(best.get("slug", ""))
    tagline = str(best.get("tagline", ""))
    seller = str(best.get("seller_username", "Unknown"))
    downloads = int(best.get("total_downloads", 0) or 0)
    rating = float(best.get("rating", 0) or 0)
    price_cents = int(best.get("price_cents", 0) or 0)
    price_label = "Free" if price_cents <= 0 else f"${price_cents / 100:.2f}"
    plugin_url = f"{base}/plugin/{plugin_slug}" if plugin_slug else base

    embed = discord.Embed(
      title=plugin_name,
      description=tagline or "No tagline provided.",
      color=discord.Color.from_rgb(0, 224, 152),
      url=plugin_url,
    )
    cover = best.get("cover_image_url")
    if isinstance(cover, str) and cover:
      embed.set_thumbnail(url=cover)
    embed.add_field(name="Developer", value=seller, inline=True)
    embed.add_field(name="Price", value=price_label, inline=True)
    embed.add_field(name="Downloads", value=f"{downloads:,}", inline=True)
    embed.add_field(name="Rating", value=f"{rating:.1f}", inline=True)
    embed.add_field(name="Link", value=plugin_url, inline=False)
    await interaction.followup.send(embed=embed)

  @staticmethod
  def _pick_best_plugin(name: str, plugins: list[dict[str, Any]]) -> dict[str, Any]:
    lowered = name.strip().lower()
    for plugin in plugins:
      if str(plugin.get("name", "")).strip().lower() == lowered:
        return plugin
    return plugins[0]


async def setup(bot: commands.Bot) -> None:
  assert isinstance(bot, MerchantBot)
  await bot.add_cog(LookupCog(bot), guild=discord.Object(id=bot.settings.discord_guild_id))

