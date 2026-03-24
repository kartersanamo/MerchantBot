from __future__ import annotations

import discord


class GettingStartedPanelView(discord.ui.View):
  def __init__(self) -> None:
    super().__init__(timeout=None)
    self.add_item(discord.ui.Button(label="Quickstart", url="https://www.mcmerchant.net/docs/loader#overview"))
    self.add_item(discord.ui.Button(label="Setup Docs", url="https://www.mcmerchant.net/docs"))
    self.add_item(discord.ui.Button(label="Seller Guide", url="https://www.mcmerchant.net/docs/for-sellers"))
    self.add_item(discord.ui.Button(label="Buyer Guide", url="https://www.mcmerchant.net/docs/for-buyers"))


def build_getting_started_embed() -> discord.Embed:
  return discord.Embed(
    title="Getting Started",
    description=(
      "Start here for first-time setup, quickstart docs, seller workflows, and platform walkthroughs."
    ),
    color=discord.Color.from_rgb(0, 224, 152),
  )

