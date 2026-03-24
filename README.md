# MerchantBot

Discord support bot for the MCMerchant Discord server, built with `discord.py`.

## Features

- `/send-message` panel publisher:
  - Information panel (`1485372672136446062`)
  - Verify panel (`1016687918796001280`)
  - Tickets panel (`1485374796488245370`)
  - Getting Started panel (`1485374171746795712`)
  - Loader And Api panel (`1485374216789557330`)
- `/feature <plugin_url>` posts featured plugin embeds (`1485373201172402477`)
- `/verify-license <license>` returns license validity/details (ephemeral)
- `/plugin-info <name>` posts plugin details publicly
- Verification sync/unsync support from signed webhooks
- Plugin/version announcement webhooks
- Ticket system with:
  - Category select panel + ticket intake modal
  - Auto-created ticket channels
  - Claim/close/reopen/delete controls
  - Transcript export and user ticket history button
- Event logging to `1485374660039413770`
- Welcome + leave messaging to `1485372287627563048`

## Setup

1. Install Python 3.11+.
2. Copy `.env.example` to `.env` and fill required values.
3. Install dependencies:

```bash
cd MerchantBot
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

4. Run:

```bash
python main.py
```

## Webhook Contract (HMAC)

- Endpoint: `POST /webhooks/mcmerchant`
- Required headers:
  - `X-MCMerchant-Timestamp`: unix seconds
  - `X-MCMerchant-Signature`: `sha256=<hex>` (or just hex)
  - `X-MCMerchant-Event-Id`: unique event id
- Signature body:
  - `HMAC_SHA256(secret, f"{timestamp}.{raw_json_body}")`

### Event payload examples

```json
{
  "type": "verify.synced",
  "data": {
    "discord_user_id": 1234567890,
    "username": "ExampleUser"
  }
}
```

```json
{
  "type": "plugin.version_published",
  "data": {
    "plugin_id": "abc",
    "plugin_name": "Bedwars Clone",
    "plugin_slug": "bedwars-clone",
    "developer_name": "kartersanamo",
    "version_name": "v1.0.1",
    "changelog": "Fixes and improvements",
    "price_label": "Free",
    "url": "https://mcmerchant.net/plugin/bedwars-clone"
  }
}
```

## Notes

- Ticket categories and modal questions are configured in `merchantbot/data/ticket_categories.json`.
- Add self-assignable roles in `.env` via `SELF_ASSIGNABLE_ROLE_IDS`.
- Restrict admin commands via `ADMIN_ROLE_IDS` (comma-separated role IDs).
- For `/verify-license`, set matching secrets:
  - Bot env: `MCMERCHANT_BOT_API_KEY`
  - Website env: `MERCHANTBOT_LICENSE_LOOKUP_KEY`

