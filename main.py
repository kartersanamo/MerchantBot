from __future__ import annotations

import asyncio

from dotenv import load_dotenv

from merchantbot.bot import MerchantBot
from merchantbot.config import Settings
from merchantbot.logging import configure_python_logging


async def main() -> None:
  load_dotenv()
  settings = Settings()
  configure_python_logging(settings.bot_log_level)
  bot = MerchantBot(settings)
  async with bot:
    await bot.start(settings.discord_token)


if __name__ == "__main__":
  asyncio.run(main())

