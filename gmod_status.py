#!/usr/bin/env python3
"""
LuminousRP Server Status -> Discord Webhook

Queries the LuminousRP Garry's Mod server using A2S
and updates a Discord webhook message every 30 seconds.

Requirements:
    pip install python-a2s requests --break-system-packages
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


# ── LUMINOUSRP CONFIG ───────────────────────────────────────────

SERVER_IP = os.environ.get(
    "SERVER_IP",
    "66.248.194.23"
)

SERVER_PORT = int(os.environ.get(
    "SERVER_PORT",
    "27015"
))

WEBHOOK_URL = os.environ.get(
    "WEBHOOK_URL",
    ""
)

BOT_NAME = os.environ.get(
    "BOT_NAME",
    "LuminousRP Status"
)

BOT_AVATAR = os.environ.get(
    "BOT_AVATAR",
    ""
)

# Update every 30 seconds
CHECK_INTERVAL_SECONDS = int(os.environ.get(
    "CHECK_INTERVAL_SECONDS",
    "30"
))

# ────────────────────────────────────────────────────────────────


ADDRESS = (SERVER_IP, SERVER_PORT)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

MESSAGE_ID_FILE = os.path.join(
    SCRIPT_DIR,
    "last_message_id.txt"
)


def get_server_info():
    """
    Query LuminousRP using the A2S protocol.
    Returns server information or None if offline.
    """

    try:
        info = a2s.info(
            ADDRESS,
            timeout=5
        )

        return info

    except Exception as e:
        print(f"Server query failed: {e}")
        return None


def build_embed(info):

    # ───────── SERVER OFFLINE ─────────

    if info is None:

        offline_embed = {
            "title": "🔴 LuminousRP.net",
            "description": "**Server Offline**",
            "color": 0xE24B4A,

            "fields": [
                {
                    "name": "🌐 Connect IP",
                    "value": f"`{SERVER_IP}:{SERVER_PORT}`",
                    "inline": True
                },
                {
                    "name": "🎮 Game",
                    "value": "Garry's Mod",
                    "inline": True
                }
            ],

            "footer": {
                "text": "LuminousRP • Last update"
            },

            "timestamp": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ",
                time.gmtime()
            )
        }

        if BOT_AVATAR:
            offline_embed["thumbnail"] = {
                "url": BOT_AVATAR
            }

        return {
            "username": BOT_NAME,
            "avatar_url": BOT_AVATAR or None,
            "embeds": [offline_embed]
        }


    # ───────── SERVER ONLINE ─────────

    name = info.server_name or "LuminousRP.net"

    map_name = info.map_name or "Unknown"

    players = info.player_count

    max_players = info.max_players


    online_embed = {
        "title": "🟢 LuminousRP.net",

        "description": (
            f"**{name}**\n"
            "Semi-Serious CityRP"
        ),

        "color": 0x639922,

        "fields": [

            {
                "name": "👥 Players",
                "value": f"`{players}/{max_players}`",
                "inline": True
            },

            {
                "name": "🗺️ Map",
                "value": f"`{map_name}`",
                "inline": True
            },

            {
                "name": "🎮 Game",
                "value": "Garry's Mod",
                "inline": True
            },

            {
                "name": "🌐 IP",
                "value": f"`{SERVER_IP}:{SERVER_PORT}`",
                "inline": False
            },

            {
                "name": "🔗 Direct Connect",
                "value": (
                    f"`steam://connect/"
                    f"{SERVER_IP}:{SERVER_PORT}`"
                ),
                "inline": False
            }
        ],

        "footer": {
            "text": "LuminousRP • Updates every 30 seconds"
        },

        "timestamp": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ",
            time.gmtime()
        )
    }


    if BOT_AVATAR:

        online_embed["thumbnail"] = {
            "url": BOT_AVATAR
        }


    return {
        "username": BOT_NAME,
        "avatar_url": BOT_AVATAR or None,
        "embeds": [online_embed]
    }


def load_message_id():

    if os.path.exists(MESSAGE_ID_FILE):

        with open(
            MESSAGE_ID_FILE,
            "r"
        ) as f:

            content = f.read().strip()

            return content or None

    return None


def save_message_id(message_id):

    with open(
        MESSAGE_ID_FILE,
        "w"
    ) as f:

        f.write(str(message_id))


def post_to_discord(payload):

    if "PASTE_YOUR" in WEBHOOK_URL:

        print(
            "⚠️ You need to set WEBHOOK_URL "
            "before running the script."
        )

        sys.exit(1)


    message_id = load_message_id()


    # ───────── EDIT EXISTING MESSAGE ─────────

    if message_id:

        edit_url = (
            f"{WEBHOOK_URL}"
            f"/messages/{message_id}"
        )

        try:

            resp = requests.patch(
                edit_url,
                json=payload,
                timeout=10
            )

            if resp.status_code in (200, 204):

                print(
                    "✅ Edited existing Discord message."
                )

                return

            elif resp.status_code == 404:

                print(
                    "Previous message not found."
                )

                print(
                    "Posting a new message..."
                )

            else:

                print(
                    f"Edit failed "
                    f"({resp.status_code})"
                )

                print(
                    "Posting a new message..."
                )

        except requests.RequestException as e:

            print(
                f"Edit request failed: {e}"
            )


    # ───────── CREATE NEW MESSAGE ─────────

    try:

        resp = requests.post(
            f"{WEBHOOK_URL}?wait=true",
            json=payload,
            timeout=10
        )

        if resp.status_code in (200, 201):

            new_id = resp.json().get("id")

            if new_id:

                save_message_id(new_id)

            print(
                "✅ Posted new Discord message."
            )

        else:

            print(
                f"Discord returned "
                f"{resp.status_code}:"
            )

            print(resp.text)

    except requests.RequestException as e:

        print(
            f"Discord request failed: {e}"
        )


def main():

    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    print(
        "   LuminousRP Status Monitor"
    )

    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    print(
        f"Server: "
        f"{SERVER_IP}:{SERVER_PORT}"
    )

    print(
        f"Update interval: "
        f"{CHECK_INTERVAL_SECONDS} seconds"
    )

    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


    while True:

        try:

            info = get_server_info()

            payload = build_embed(info)

            post_to_discord(payload)

        except Exception as e:

            print(
                f"Unexpected error: {e}"
            )


        time.sleep(
            CHECK_INTERVAL_SECONDS
        )


if __name__ == "__main__":

    main()
