from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PluginEventPayload:
  plugin_id: str
  plugin_name: str
  plugin_slug: str
  developer_name: str
  version_name: str | None
  changelog: str | None
  price_label: str | None
  url: str

