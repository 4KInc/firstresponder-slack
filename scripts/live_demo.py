"""Drive a REAL end-to-end FirstResponder demo in a live Slack workspace.

This is not a mock. Every step is a real Slack Web API call that produces a
real event the RUNNING app processes over Socket Mode, against the real
knowledge base (Jefferson Elementary) already loaded in data/firstresponder.db.

Prerequisite: the app must already be running in another terminal:
    .venv/bin/python app.py

Environment (from .env):
    SLACK_BOT_TOKEN     required   (xoxb-…)
    SLACK_USER_TOKEN    recommended (xoxp-…) — lets this script post & react AS
                        a human, which is what triggers the @mention agent flow
                        and the emoji check-in handler. Without it the script
                        can only post as the bot (bot messages don't trigger
                        those handlers), so you'd drive those steps by hand.
    DEMO_CHANNEL        optional   (Cxxxx) — reuse an existing channel id

Usage:
    .venv/bin/python -m scripts.live_demo
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

load_dotenv()

BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
USER_TOKEN = os.environ.get("SLACK_USER_TOKEN")
DEMO_CHANNEL = os.environ.get("DEMO_CHANNEL")
CHANNEL_NAME = os.environ.get("DEMO_CHANNEL_NAME", "fr-live-demo")


def log(msg):
    print(f"  {msg}", flush=True)


async def ensure_channel(bot: AsyncWebClient, user: AsyncWebClient | None) -> str:
    if DEMO_CHANNEL:
        log(f"using existing channel {DEMO_CHANNEL}")
        try:
            await bot.conversations_join(channel=DEMO_CHANNEL)
        except SlackApiError:
            pass
        return DEMO_CHANNEL

    # Prefer creating as the user so they're a member (and can be the "reporter").
    creator = user or bot
    try:
        r = await creator.conversations_create(name=CHANNEL_NAME, is_private=False)
        chan = r["channel"]["id"]
        log(f"created #{CHANNEL_NAME} → {chan}")
    except SlackApiError as e:
        if e.response["error"] in ("name_taken", "restricted_action"):
            # find it
            cursor = None
            chan = None
            while True:
                resp = await bot.conversations_list(limit=200, cursor=cursor, types="public_channel")
                for c in resp["channels"]:
                    if c["name"] == CHANNEL_NAME:
                        chan = c["id"]
                        break
                cursor = resp.get("response_metadata", {}).get("next_cursor")
                if chan or not cursor:
                    break
            if not chan:
                raise
            log(f"reusing existing #{CHANNEL_NAME} → {chan}")
        else:
            raise

    # Make sure the bot is a member so it can post/read.
    try:
        await bot.conversations_join(channel=chan)
    except SlackApiError:
        pass
    return chan


async def wait(seconds, why):
    log(f"… waiting {seconds}s for the app to {why}")
    await asyncio.sleep(seconds)


async def main():
    if not BOT_TOKEN:
        sys.exit("SLACK_BOT_TOKEN missing — fill in .env first.")

    bot = AsyncWebClient(token=BOT_TOKEN)
    user = AsyncWebClient(token=USER_TOKEN) if USER_TOKEN else None

    print("\n=== FirstResponder LIVE demo (real Slack, real data) ===\n")

    a = await bot.auth_test()
    log(f"bot   : @{a['user']}  ({a['user_id']})  team={a['team']}")
    bot_id = a["user_id"]
    if user:
        ua = await user.auth_test()
        log(f"human : @{ua['user']}  ({ua['user_id']})")
    else:
        log("no SLACK_USER_TOKEN — will post as the bot; @mention/emoji steps need a human")

    chan = await ensure_channel(bot, user)
    team = a["team_id"]
    log(f"open the channel: https://app.slack.com/client/{team}/{chan}\n")

    poster = user or bot
    reporter_is_human = user is not None

    # --- 1. Report the fire by @mentioning the agent (real agent run) ---
    print("STEP 1 — report a fire to @FirstResponder (real agent + knowledge base)")
    if reporter_is_human:
        await poster.chat_postMessage(
            channel=chan,
            text=(f"<@{bot_id}> we have a fire near the 2nd-floor science lab in the "
                  f"east wing — smoke spreading. Start the crisis, who's in danger and "
                  f"what are the safe evacuation routes?"),
        )
        await wait(25, "start the crisis, seed the roster, and answer with building-specific guidance")
    else:
        log("SKIP (needs human): in Slack, type —")
        log("   @FirstResponder we have a fire near the 2nd-floor science lab, who is in danger?")
        await wait(2, "continue")

    # --- 2. Emoji check-ins (real reaction_added events) ---
    print("\nSTEP 2 — personnel check in with emoji reactions (real check-in events)")
    # find the most recent bot alert message to react to
    hist = await bot.conversations_history(channel=chan, limit=15)
    target_ts = None
    for m in hist["messages"]:
        if m.get("user") == bot_id or m.get("bot_id"):
            target_ts = m["ts"]
            break
    if target_ts and user:
        await user.reactions_add(channel=chan, timestamp=target_ts, name="white_check_mark")
        log("human reacted ✅ safe → should post a check-in confirmation + missing list")
        await wait(6, "record the check-in and update accountability")
    elif target_ts:
        log("SKIP (needs human): react ✅ / 🆘 on the FirstResponder alert message")
        await wait(2, "continue")
    else:
        log("no bot message found to react to yet")

    # --- 3. Ask for status + a SITREP (real agent + RTS if user token present) ---
    print("\nSTEP 3 — ask for a SITREP + who is still missing (real agent)")
    if reporter_is_human:
        await poster.chat_postMessage(
            channel=chan,
            text=f"<@{bot_id}> generate a SITREP and tell me who still hasn't checked in.",
        )
        await wait(25, "read the channel (RTS/MCP) and produce a SITREP")
    else:
        log("SKIP (needs human): @FirstResponder generate a SITREP and who's missing?")
        await wait(2, "continue")

    print("\n=== driver finished — check the channel and the app logs ===")
    log(f"https://app.slack.com/client/{team}/{chan}")


if __name__ == "__main__":
    asyncio.run(main())
