from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PanelOption = Literal["Information", "Verify", "Tickets", "Getting Started", "Loader And Api"]


class Settings(BaseSettings):
  model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

  # Runtime
  discord_token: str = Field(alias="DISCORD_TOKEN")
  discord_guild_id: int = Field(alias="DISCORD_GUILD_ID")
  bot_log_level: str = Field(default="INFO", alias="BOT_LOG_LEVEL")
  database_path: str = Field(default="merchantbot.db", alias="DATABASE_PATH")

  # Webhook
  webhook_bind_host: str = Field(default="127.0.0.1", alias="WEBHOOK_BIND_HOST")
  webhook_bind_port: int = Field(default=8088, alias="WEBHOOK_BIND_PORT")
  webhook_shared_secret: str = Field(alias="WEBHOOK_SHARED_SECRET")

  # URLs/content
  mcmerchant_base_url: str = Field(default="https://www.mcmerchant.net", alias="MCMERCHANT_BASE_URL")
  mcmerchant_bot_api_key: str = Field(default="", alias="MCMERCHANT_BOT_API_KEY")
  sync_account_url: str = Field(
    default="https://www.mcmerchant.net/account/connections/discord/sync",
    alias="SYNC_ACCOUNT_URL",
  )
  unsync_account_url: str = Field(
    default="https://www.mcmerchant.net/account/connections/discord/unsync",
    alias="UNSYNC_ACCOUNT_URL",
  )
  discord_rules_text: str = Field(
    default="Follow Discord ToS, be respectful, and avoid spam.",
    alias="DISCORD_RULES_TEXT",
  )

  # Optional role lists
  self_assignable_role_ids: str = Field(default="", alias="SELF_ASSIGNABLE_ROLE_IDS")
  admin_role_ids: str = Field(default="", alias="ADMIN_ROLE_IDS")

  # Channel IDs
  information_channel_id: int = 1485372672136446062
  verify_channel_id: int = 1485373075946999949
  tickets_channel_id: int = 1485374796488245370
  getting_started_channel_id: int = 1485374171746795712
  loader_api_channel_id: int = 1485374216789557330
  logs_channel_id: int = 1485374660039413770
  welcome_channel_id: int = 1485372287627563048
  featured_channel_id: int = 1485373201172402477

  verified_role_id: int = 922225328225673257

  @property
  def database_file(self) -> Path:
    return Path(self.database_path)

  @property
  def parsed_self_assignable_role_ids(self) -> list[int]:
    return _parse_csv_ints(self.self_assignable_role_ids)

  @property
  def parsed_admin_role_ids(self) -> list[int]:
    return _parse_csv_ints(self.admin_role_ids)


def _parse_csv_ints(raw: str) -> list[int]:
  values: list[int] = []
  for item in raw.split(","):
    stripped = item.strip()
    if not stripped:
      continue
    try:
      values.append(int(stripped))
    except ValueError:
      continue
  return values

