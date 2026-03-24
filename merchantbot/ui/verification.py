from __future__ import annotations

import discord

from merchantbot.bot import MerchantBot


class VerifyPanelView(discord.ui.View):
  def __init__(self, bot: MerchantBot) -> None:
    super().__init__(timeout=None)
    self.add_item(
      discord.ui.Button(
        label="Sync Account",
        style=discord.ButtonStyle.link,
        url=bot.settings.sync_account_url,
      )
    )
    self.add_item(
      discord.ui.Button(
        label="Unsync Account",
        style=discord.ButtonStyle.link,
        url=bot.settings.unsync_account_url,
      )
    )


def build_verify_embed() -> discord.Embed:
  embed = discord.Embed(
    title="Verify to unlock the server",
    description=(
      "You must verify your MCMerchant account to gain full access.\n\n"
      "1) Press **Sync Account**\n"
      "2) Complete the account link flow\n"
      "3) You will automatically receive the verified role"
    ),
    color=discord.Color.from_rgb(0, 224, 152),
  )
  return embed

