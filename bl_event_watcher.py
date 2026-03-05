import os
import re
import aiohttp
import discord

# ── Config ────────────────────────────────────────────────────────────────────
# Secrets are loaded from environment variables (set in Railway → Variables tab)
# NEVER hardcode tokens in code that goes on GitHub.
DISCORD_TOKEN   = os.environ.get("DISCORD_TOKEN", "")
WATCH_CHANNEL   = 1478094308186914899
WEBHOOK_URL     = os.environ.get("WEBHOOK_URL", "")

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN env variable is not set!")
if not WEBHOOK_URL:
    raise RuntimeError("WEBHOOK_URL env variable is not set!")

# ← paste the numeric ID of your @notify role here (right-click role → Copy ID)
NOTIFY_ROLE_ID = 1478904991296131225

# Event keywords → display names + embed colors
EVENT_TYPES = {
    "deathmatch": ("Deathmatch",  0xE74C3C),   # red
    "graveyard":  ("Graveyard",   0x9B59B6),   # purple
}

# Only match roblox.com links (profile pages OR private server links)
ROBLOX_URL_RE = re.compile(
    r"https?://(?:www\.)?roblox\.com/\S+",
    re.IGNORECASE,
)

# ── Discord client ─────────────────────────────────────────────────────────────
client = discord.Client()

async def send_event_webhook(event_name: str, color: int, link: str, raw: str):
    embed = {
        "title": f"🌍 World Event — {event_name}",
        "description": (
            f"**Type:** {event_name}\n"
            f"**Link:** {link}\n\n"
            f"*Original message:*\n> {raw[:300]}"
        ),
        "color": color,
        "footer": {"text": "Lucid.gg | Notifier"},
    }
    # Ping @notify role if ID is set, otherwise falls back to plain text
    ping = f"<@&{NOTIFY_ROLE_ID}>" if NOTIFY_ROLE_ID else "@notify"
    payload = {
        "content": ping,
        "embeds": [embed],
    }
    async with aiohttp.ClientSession() as session:
        resp = await session.post(WEBHOOK_URL, json=payload)
        print(f"[WEBHOOK] {event_name} → HTTP {resp.status}")

@client.event
async def on_ready():
    print(f"[READY] Logged in as {client.user} — watching channel {WATCH_CHANNEL}")

@client.event
async def on_message(message):
    # Only care about the target channel
    if message.channel.id != WATCH_CHANNEL:
        return

    low = message.content.lower()

    # Detect event type
    detected = None
    for keyword, (name, color) in EVENT_TYPES.items():
        if keyword in low:
            detected = (name, color)
            break

    if not detected:
        return

    event_name, color = detected

    # Must have a roblox.com link — ignore random messages with no link
    match = ROBLOX_URL_RE.search(message.content)
    if not match:
        print(f"[SKIP] {event_name} — no roblox link found | \"{message.content[:60]}\"")
        return
    link = match.group(0)

    print(f"[DETECTED] {event_name} | {link} | \"{message.content[:80]}\"")
    await send_event_webhook(event_name, color, link, message.content)

client.run(DISCORD_TOKEN)
