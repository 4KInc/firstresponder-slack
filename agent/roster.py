"""Seed a crisis roster from the members of its Slack channel.

Personnel accountability ("who hasn't checked in?") only works if the crisis
knows who is *expected* to check in. We derive that expected set from the human
members of the channel where the crisis is declared, so ``missing_checkins``
(roster − checked-in) is populated from the moment the crisis starts.
"""

from slack_sdk.web.async_client import AsyncWebClient

from crisis import crisis_manager

# Cache the app's own bot user id per token so it isn't counted as "missing".
_bot_id_cache: dict[str | None, str | None] = {}


async def seed_roster_from_channel(
    client: AsyncWebClient, crisis_id: str, channel_id: str
) -> int:
    """Add the channel's human members to the crisis roster.

    Best-effort: any failure (missing scope, bot not in channel, a DM, etc.) is
    swallowed and returns 0 so declaring a crisis never breaks. Returns the
    number of members added to the roster.
    """
    try:
        token = getattr(client, "token", None)
        if token not in _bot_id_cache:
            auth = await client.auth_test()
            _bot_id_cache[token] = auth.get("user_id")
        bot_id = _bot_id_cache.get(token)

        members: list[str] = []
        cursor: str | None = None
        while True:
            resp = await client.conversations_members(
                channel=channel_id, limit=200, cursor=cursor
            )
            members.extend(resp.get("members", []))
            cursor = (resp.get("response_metadata") or {}).get("next_cursor")
            if not cursor:
                break

        humans = [m for m in members if m != bot_id]
        if humans:
            crisis_manager.add_to_roster(crisis_id, humans)
        return len(humans)
    except Exception:
        return 0
