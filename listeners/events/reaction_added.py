from logging import Logger

from slack_bolt.context.async_context import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient

from crisis import crisis_manager

# Emoji reactions that count as check-ins
CHECKIN_EMOJIS = {
    "white_check_mark": "safe",
    "heavy_check_mark": "safe",
    "+1": "safe",
    "thumbsup": "safe",
    "ok_hand": "safe",
    "ambulance": "injured",
    "hospital": "injured",
    "door": "evacuated",
    "runner": "evacuated",
    "sos": "need-help",
    "hand": "need-help",
}


async def handle_reaction_added(
    client: AsyncWebClient,
    context: AsyncBoltContext,
    event: dict,
    logger: Logger,
):
    """Handle emoji reactions as check-ins during active crises."""
    try:
        reaction = event.get("reaction", "")
        user_id = event.get("user", "")
        channel_id = event.get("item", {}).get("channel", "")

        if reaction not in CHECKIN_EMOJIS:
            return

        # Check if there's an active crisis in this channel, or fall back to any active crisis
        crisis = crisis_manager.get_crisis_by_channel(channel_id)
        if not crisis:
            active = crisis_manager.get_active_crises()
            if active:
                crisis = active[0]
            else:
                return

        status = CHECKIN_EMOJIS[reaction]

        # Add to roster and check in
        crisis_manager.add_to_roster(crisis.id, [user_id])
        checkin = crisis_manager.check_in(crisis.id, user_id, status)

        if checkin:
            checked_in = len(crisis.check_ins)
            roster = len(crisis.team_roster)
            missing = crisis.missing_checkins

            # Post a check-in confirmation in the channel
            status_emoji = {
                "safe": ":white_check_mark:",
                "injured": ":ambulance:",
                "evacuated": ":door:",
                "need-help": ":sos:",
            }

            msg = f"{status_emoji.get(status, ':white_check_mark:')} <@{user_id}> checked in as *{status}* ({checked_in}/{roster})"

            if checked_in == roster and roster > 0:
                msg += "\n:tada: *All personnel accounted for!*"
            elif missing:
                msg += f"\n:red_circle: Still missing: " + ", ".join(f"<@{uid}>" for uid in missing[:5])
                if len(missing) > 5:
                    msg += f" and {len(missing) - 5} more"

            # Post to the crisis's own channel, not necessarily where the
            # reaction was added (they differ when we fell back to an active
            # crisis in another channel).
            await client.chat_postMessage(channel=crisis.channel_id, text=msg)

    except Exception as e:
        logger.exception(f"Failed to handle reaction: {e}")
