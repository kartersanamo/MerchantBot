from __future__ import annotations

import discord


class LoaderApiPanelView(discord.ui.View):
  def __init__(self) -> None:
    super().__init__(timeout=None)
    self.add_item(discord.ui.Button(label="MCMerchantLoader", url="https://www.mcmerchant.net/docs/loader"))
    self.add_item(discord.ui.Button(label="API Endpoints", url="https://www.mcmerchant.net/docs/loader#api-request"))
    self.add_item(discord.ui.Button(label="mcmerchant.yml", url="https://www.mcmerchant.net/docs/loader#config"))
    self.add_item(discord.ui.Button(label="/pdex Help", url="https://www.mcmerchant.net/docs/loader#commands"))


def build_loader_api_embed() -> discord.Embed:
  return discord.Embed(
    title="Loader And API",
    description=(
      "Everything for integration: MCMerchantLoader, API endpoints, `mcmerchant.yml` configuration, and `/pdex` support."
    ),
    color=discord.Color.from_rgb(0, 224, 152),
  )

