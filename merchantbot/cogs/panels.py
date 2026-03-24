from __future__ import annotations

from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from merchantbot.bot import MerchantBot
from merchantbot.ticketsystem.Cogs.sendtickets import TicketLogs, TicketsView
from merchantbot.ui.getting_started import GettingStartedPanelView, build_getting_started_embed
from merchantbot.ui.information import InformationPanelView, build_information_embed
from merchantbot.ui.loader_api import LoaderApiPanelView, build_loader_api_embed
from merchantbot.ui.verification import VerifyPanelView, build_verify_embed

PanelOption = Literal["Information", "Verify", "Tickets", "Getting Started", "Loader And Api"]


class PanelsCog(commands.Cog):
  def __init__(self, bot: MerchantBot) -> None:
    self.bot = bot

  def _is_admin(self, member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
      return True
    allowed = set(self.bot.settings.parsed_admin_role_ids)
    if not allowed:
      return member.guild_permissions.manage_guild
    return any(role.id in allowed for role in member.roles)

  @app_commands.guild_only()
  @app_commands.command(name="send-message", description="Send one of the configured MCMerchant panel messages.")
  @app_commands.describe(option="Which panel to send")
  async def send_message(self, interaction: discord.Interaction, option: PanelOption) -> None:
    if not isinstance(interaction.user, discord.Member):
      await interaction.response.send_message("Guild-only command.", ephemeral=True)
      return
    if not self._is_admin(interaction.user):
      await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
      return

    await interaction.response.send_message("Publishing panel...", ephemeral=True)
    channel, embed, view = self._build_panel(option)
    if option == "Tickets":
      first = await channel.send(embed=embed, view=view)
      third = await channel.send(
        embed=discord.Embed(
          description="Want to see your previous tickets? Use the envelope button below.",
          color=discord.Color.from_rgb(0, 224, 152),
        ),
        view=TicketLogs(),
      )
      await self.bot.storage.save_panel_message(option, channel.id, first.id)
      await self.bot.storage.save_panel_message(option, channel.id, third.id)
    else:
      msg = await channel.send(embed=embed, view=view)
      await self.bot.storage.save_panel_message(option, channel.id, msg.id)
    await interaction.edit_original_response(content=f"Published `{option}` to {channel.mention}.")

  def _build_panel(self, option: PanelOption) -> tuple[discord.TextChannel, discord.Embed, discord.ui.View]:
    guild = self.bot.get_guild(self.bot.settings.discord_guild_id)
    if guild is None:
      raise RuntimeError("Guild not found in cache.")

    if option == "Information":
      channel = guild.get_channel(self.bot.settings.information_channel_id)
      if not isinstance(channel, discord.TextChannel):
        raise RuntimeError("Information channel missing or invalid.")
      return channel, build_information_embed(), InformationPanelView(self.bot)
    if option == "Verify":
      channel = guild.get_channel(self.bot.settings.verify_channel_id)
      if not isinstance(channel, discord.TextChannel):
        raise RuntimeError("Verify channel missing or invalid.")
      return channel, build_verify_embed(), VerifyPanelView(self.bot)
    if option == "Tickets":
      channel = guild.get_channel(self.bot.settings.tickets_channel_id)
      if not isinstance(channel, discord.TextChannel):
        raise RuntimeError("Tickets channel missing or invalid.")
      embed = discord.Embed(
        title="Open a Support Ticket",
        description=(
          "Choose a ticket category below.\n\n"
          "Please include all relevant details. A staff member will respond soon."
        ),
        color=discord.Color.from_rgb(0, 224, 152),
      )
      view = TicketsView()
      return channel, embed, view
    if option == "Getting Started":
      channel = guild.get_channel(self.bot.settings.getting_started_channel_id)
      if not isinstance(channel, discord.TextChannel):
        raise RuntimeError("Getting Started channel missing or invalid.")
      return channel, build_getting_started_embed(), GettingStartedPanelView()

    channel = guild.get_channel(self.bot.settings.loader_api_channel_id)
    if not isinstance(channel, discord.TextChannel):
      raise RuntimeError("Loader/API channel missing or invalid.")
    return channel, build_loader_api_embed(), LoaderApiPanelView()

  @commands.Cog.listener()
  async def on_ready(self) -> None:
    guild_obj = discord.Object(id=self.bot.settings.discord_guild_id)
    self.bot.tree.copy_global_to(guild=guild_obj)


async def setup(bot: commands.Bot) -> None:
  assert isinstance(bot, MerchantBot)
  cog = PanelsCog(bot)
  await bot.add_cog(cog, guild=discord.Object(id=bot.settings.discord_guild_id))

