from __future__ import annotations

import discord

from merchantbot.bot import MerchantBot

EMBED_COLOR = discord.Color.from_rgb(0, 224, 152)


class RolesSelect(discord.ui.Select):
  def __init__(self, roles: list[discord.Role], role_ids: list[int], member: discord.Member) -> None:
    options = [
      discord.SelectOption(
        label=role.name[:100],
        value=str(role.id),
        default=role in member.roles,
      )
      for role in roles[:25]
    ]
    super().__init__(
      placeholder="Pick your server roles",
      min_values=0,
      max_values=max(1, min(10, len(options))) if options else 1,
      custom_id="merchantbot_roles_select",
      options=options,
    )
    self._allowed = set(role_ids)

  async def callback(self, interaction: discord.Interaction) -> None:
    if not isinstance(interaction.user, discord.Member):
      await interaction.response.send_message("This can only be used in a server.", ephemeral=True)
      return
    member = interaction.user
    selected_ids = {int(value) for value in self.values}
    allowed_roles = [r for r in interaction.guild.roles if r.id in self._allowed]
    selected = [r for r in allowed_roles if r.id in selected_ids]
    to_add = [r for r in selected if r not in member.roles]
    to_remove = [r for r in allowed_roles if r in member.roles and r not in selected]
    if to_add:
      await member.add_roles(*to_add, reason="Self-assign role menu")
    if to_remove:
      await member.remove_roles(*to_remove, reason="Self-assign role menu")
    names = ", ".join(r.name for r in selected) if selected else "No roles selected"
    await interaction.response.send_message(f"Updated roles: {names}", ephemeral=True)


class RolesSelectView(discord.ui.View):
  def __init__(self, roles: list[discord.Role], role_ids: list[int], member: discord.Member) -> None:
    super().__init__(timeout=120)
    self.add_item(RolesSelect(roles, role_ids, member))


class InformationPanelView(discord.ui.View):
  def __init__(self, bot: MerchantBot) -> None:
    super().__init__(timeout=None)
    self.bot = bot
    self.add_item(
      discord.ui.Button(
        label="MCMerchant",
        url=bot.settings.mcmerchant_base_url,
        style=discord.ButtonStyle.link,
      )
    )

  @discord.ui.button(label="Roles", style=discord.ButtonStyle.secondary, custom_id="merchantbot_info_roles")
  async def roles(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
      await interaction.response.send_message("This can only be used in a server.", ephemeral=True)
      return

    role_ids = self.bot.settings.parsed_self_assignable_role_ids
    if not role_ids:
      await interaction.response.send_message(
        "Self-assignable roles are not configured yet.",
        ephemeral=True,
      )
      return

    configured_roles = [interaction.guild.get_role(role_id) for role_id in role_ids]
    available_roles = [role for role in configured_roles if role is not None]
    if not available_roles:
      await interaction.response.send_message(
        "Configured self-assignable roles were not found in this server.",
        ephemeral=True,
      )
      return

    await interaction.response.send_message(
      "Choose your roles from the dropdown.",
      view=RolesSelectView(available_roles, role_ids, interaction.user),
      ephemeral=True,
    )

  @discord.ui.button(label="Rules", style=discord.ButtonStyle.secondary, custom_id="merchantbot_info_rules")
  async def rules(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
    embed = discord.Embed(
      title="MCMerchant Discord Rules",
      description=(
        "Please follow these rules to keep the server safe and useful for everyone.\n\n"
        "1. Follow Discord Terms of Service and Community Guidelines at all times.\n"
        "2. Be respectful: no harassment, hate speech, threats, or personal attacks.\n"
        "3. No spam, flood, excessive pings, or disruptive behavior.\n"
        "4. Keep discussions in the correct channels and stay on topic.\n"
        "5. No scam links, malware, phishing, doxxing, or account selling.\n"
        "6. No NSFW content, gore, or otherwise inappropriate media.\n"
        "7. Use tickets for support; do not DM staff for normal support requests.\n"
        "8. No advertising or self-promotion without staff approval.\n"
        "9. Do not impersonate staff, creators, or other members.\n"
        "10. Staff decisions are final; repeated abuse may result in moderation action.\n\n"
        f"Additional note: {self.bot.settings.discord_rules_text}"
      ),
      color=EMBED_COLOR,
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

  @discord.ui.button(label="TOS/Privacy", style=discord.ButtonStyle.secondary, custom_id="merchantbot_info_tos_privacy")
  async def tos_privacy(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
    base = self.bot.settings.mcmerchant_base_url.rstrip("/")
    embed = discord.Embed(
      title="Terms and Privacy",
      description="Please review these policies before using MCMerchant.",
      color=EMBED_COLOR,
    )
    embed.add_field(name="Terms of Service", value=f"{base}/tos", inline=False)
    embed.add_field(name="Privacy Policy", value=f"{base}/privacy", inline=False)
    await interaction.response.send_message(
      embed=embed,
      ephemeral=True,
    )


def build_information_embed() -> discord.Embed:
  embed = discord.Embed(
    title="Welcome to MCMerchant",
    description=(
      "MCMerchant is the marketplace + licensing + updater platform for Minecraft plugin developers.\n\n"
      "Use the buttons below for key links, role setup, server rules, and legal pages."
    ),
    color=EMBED_COLOR,
  )
  embed.set_footer(text="MCMerchant Support")
  return embed

