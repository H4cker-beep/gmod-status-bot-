#!/usr/bin/env python3
"""
GMod Server Status -> Discord Webhook

Queries a Garry's Mod (Source Engine) server using the A2S protocol
and posts a live "Online"/"Offline" embed to a Discord channel via webhook.

Usage:
    python3 gmod_status.py

Requirements:
    pip install python-a2s requests --break-system-packages

Configure the constants below, then run the script manually,
or schedule it (see the bottom of this file for a cron example).
"""

import os
import sys
import time
import requests

try:
    import a2s
except ImportError:
    print("Missing dependency. Install with:")
    print("  pip install python-a2s requests --break-system-packages")
    sys.exit(1)

# ── CONFIGURE THESE ──────────────────────────────────────────────
# On Railway, set these as Variables in your project settings instead
# of editing them here. Locally, you can still just edit the values below.
SERVER_IP = os.environ.get("SERVER_IP", "65.21.150.116")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "27015"))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "PASTE_YOUR_DISCORD_WEBHOOK_URL_HERE")
BOT_NAME = os.environ.get("BOT_NAME", "GMod Server Status")
BOT_AVATAR = os.environ.get("BOT_AVATAR", "")   # URL to an avatar image
CHECK_INTERVAL_SECONDS = int(os.environ.get("CHECK_INTERVAL_SECONDS", "300"))  # 5 min default
# ─────────────────────────────────────────────────────────────────

ADDRESS = (SERVER_IP, SERVER_PORT)

# File used to remember which message to edit, so we update the
# same embed instead of posting a new one every time this runs.
# NOTE: Railway's free tier does not guarantee this file survives a
# redeploy/restart — if it's missing, the script just posts a fresh
# message and starts tracking from there again. Not a big deal.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MESSAGE_ID_FILE = os.path.join(SCRIPT_DIR, "last_message_id.txt")


def get_server_info():
    """Query the server. Returns an a2s.SourceInfo object, or None if offline."""
    try:
        info = a2s.info(ADDRESS, timeout=3)
        return info
    except Exception:
        return None


def build_embed(info):
    if info is None:
        # Server is offline / unreachable
        offline_embed = {
            "title": "🔴 Server Offline",
            "description": "The server could not be reached.",
            "color": 0xE24B4A,  # red
            "fields": [
                {"name": "IP Address", "value": f"`{SERVER_IP}:{SERVER_PORT}`", "inline": True},
            ],
            "footer": {"text": "Last checked"},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        if BOT_AVATAR:
            offline_embed["thumbnail"] = {"url": BOT_AVATAR}
        return {
            "username": BOT_NAME,
            "avatar_url": BOT_AVATAR or None,
            "embeds": [offline_embed]
        }

    # Server is online — pull live details
    name = info.server_name or "Garry's Mod Server"
    map_name = info.map_name or "unknown"
    players = info.player_count
    max_players = info.max_players

    embed = {
        "title": "🟢 Server Online",
        "description": f"**{name}**",
        "color": 0x639922,  # green
        "fields": [
            {"name": "Connect IP", "value": f"`{SERVER_IP}:{SERVER_PORT}`", "inline": True},
            {"name": "Players", "value": f"{players} / {max_players}", "inline": True},
            {"name": "Map", "value": map_name, "inline": True},
            {"name": "Direct Connect", "value": f"steam://connect/{SERVER_IP}:{SERVER_PORT}"},
        ],
        "footer": {"text": "Last checked"},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }

    if BOT_AVATAR:
        embed["thumbnail"] = {"url": BOT_AVATAR}

    return {
        "username": BOT_NAME,
        "avatar_url": BOT_AVATAR or None,
        "embeds": [embed]
    }


def load_message_id():
    if os.path.exists(MESSAGE_ID_FILE):
        with open(MESSAGE_ID_FILE, "r") as f:
            content = f.read().strip()
            return content or None
    return None


def save_message_id(message_id):
    with open(MESSAGE_ID_FILE, "w") as f:
        f.write(str(message_id))


def post_to_discord(payload):
    if "PASTE_YOUR" in WEBHOOK_URL:
        print("⚠️  You need to set WEBHOOK_URL in the script before running it.")
        sys.exit(1)

    message_id = load_message_id()

    if message_id:
        # Try to edit the existing message
        edit_url = f"{WEBHOOK_URL}/messages/{message_id}"
        resp = requests.patch(edit_url, json=payload, timeout=10)
        if resp.status_code in (200, 204):
            print("Edited existing Discord message.")
            return
        elif resp.status_code == 404:
            # The old message was deleted manually — fall through and post a new one
            print("Previous message not found, posting a new one.")
        else:
            print(f"Edit failed ({resp.status_code}: {resp.text}), posting a new message instead.")

    # No saved message yet, or editing failed — post a new one (wait=true returns the message JSON)
    resp = requests.post(f"{WEBHOOK_URL}?wait=true", json=payload, timeout=10)
    if resp.status_code in (200, 201):
        new_id = resp.json().get("id")
        if new_id:
            save_message_id(new_id)
        print("Posted new Discord message.")
    else:
        print(f"Discord returned {resp.status_code}: {resp.text}")


def main():
    print(f"Starting GMod status watcher for {SERVER_IP}:{SERVER_PORT}")
    print(f"Checking every {CHECK_INTERVAL_SECONDS} seconds...")
    while True:
        try:
            info = get_server_info()
            payload = build_embed(info)
            post_to_discord(payload)
        except Exception as e:
            # Never let one bad check crash the whole worker
            print(f"Unexpected error during check: {e}")
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
