from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from aiohttp import web

from merchantbot.bot import MerchantBot
from merchantbot.webhooks.security import verify_hmac_signature

log = logging.getLogger("merchantbot.webhooks")


async def start_webhook_server(bot: MerchantBot) -> None:
  app = web.Application()
  app["bot"] = bot
  app.router.add_post("/webhooks/mcmerchant", handle_webhook)
  runner = web.AppRunner(app)
  await runner.setup()
  site = web.TCPSite(runner, host=bot.settings.webhook_bind_host, port=bot.settings.webhook_bind_port)
  await site.start()
  log.info("Webhook server listening on %s:%s", bot.settings.webhook_bind_host, bot.settings.webhook_bind_port)
  try:
    while True:
      await asyncio.sleep(60)
  except asyncio.CancelledError:
    await runner.cleanup()
    raise


async def handle_webhook(request: web.Request) -> web.Response:
  bot: MerchantBot = request.app["bot"]
  raw_body = await request.read()
  timestamp = request.headers.get("X-MCMerchant-Timestamp", "")
  signature = request.headers.get("X-MCMerchant-Signature", "")
  event_id = request.headers.get("X-MCMerchant-Event-Id", "")

  if not verify_hmac_signature(
    raw_body=raw_body,
    timestamp=timestamp,
    signature=signature,
    secret=bot.settings.webhook_shared_secret,
  ):
    await bot.event_logger.send(
      title="Webhook Rejected",
      description="Invalid signature/timestamp for incoming webhook.",
      severity="warn",
    )
    return web.json_response({"error": "invalid_signature"}, status=401)

  try:
    payload = json.loads(raw_body.decode("utf-8"))
  except json.JSONDecodeError:
    return web.json_response({"error": "invalid_json"}, status=400)

  event_type = payload.get("type")
  if not isinstance(event_type, str):
    return web.json_response({"error": "missing_event_type"}, status=400)

  if not event_id:
    return web.json_response({"error": "missing_event_id"}, status=400)

  inserted = await bot.storage.record_webhook_event(event_id, event_type)
  if not inserted:
    return web.json_response({"ok": True, "duplicate": True})

  try:
    await dispatch_event(bot, event_type, payload.get("data") or {})
  except Exception as exc:  # noqa: BLE001
    log.exception("Failed to process webhook %s", event_type)
    await bot.event_logger.exception(
      title="Webhook Processing Error",
      error=exc,
      extra={"event_type": event_type, "event_id": event_id},
    )
    return web.json_response({"error": "processing_failed"}, status=500)

  await bot.event_logger.send(
    title="Webhook Processed",
    description=f"Processed `{event_type}` successfully.",
    severity="success",
    fields=[("event_id", event_id)],
  )
  return web.json_response({"ok": True})


async def dispatch_event(bot: MerchantBot, event_type: str, data: dict[str, Any]) -> None:
  if event_type == "verify.synced":
    await _handle_verify_synced(bot, data)
    return
  if event_type == "verify.unsynced":
    await _handle_verify_unsynced(bot, data)
    return
  if event_type in {"plugin.created", "plugin.version_published"}:
    await _handle_plugin_event(bot, event_type, data)
    return
  await bot.event_logger.send(
    title="Unknown Webhook Event",
    description=f"Received unsupported event type `{event_type}`.",
    severity="warn",
  )


async def _handle_verify_synced(bot: MerchantBot, data: dict[str, Any]) -> None:
  from merchantbot.cogs.verification import apply_verified_state

  await apply_verified_state(
    bot=bot,
    discord_user_id=int(data["discord_user_id"]),
    username=str(data["username"]),
  )


async def _handle_verify_unsynced(bot: MerchantBot, data: dict[str, Any]) -> None:
  from merchantbot.cogs.verification import remove_verified_state

  await remove_verified_state(
    bot=bot,
    discord_user_id=int(data["discord_user_id"]),
  )


async def _handle_plugin_event(bot: MerchantBot, event_type: str, data: dict[str, Any]) -> None:
  from merchantbot.cogs.featured import send_plugin_announcement

  await send_plugin_announcement(bot=bot, event_type=event_type, payload=data)

