from claude_agent_sdk import tool

from agent.context import agent_deps_var
from crisis import crisis_manager


@tool(
    name="check_in",
    description="""\
Record a team member's check-in during a crisis. Check-ins track personnel safety \
and accountability. Users can check in as 'safe', 'injured', 'evacuated', or 'need-help'.
""",
    input_schema={
        "type": "object",
        "properties": {
            "crisis_id": {
                "type": "string",
                "description": "The incident ID. If not provided, uses the crisis in the current channel.",
            },
            "user_id": {
                "type": "string",
                "description": "The user ID checking in. If not provided, uses the current user.",
            },
            "status": {
                "type": "string",
                "description": "Check-in status",
                "enum": ["safe", "injured", "evacuated", "need-help"],
                "default": "safe",
            },
            "note": {
                "type": "string",
                "description": "Optional note with additional context (e.g., location, situation).",
            },
        },
    },
)
async def check_in_tool(args):
    deps = agent_deps_var.get()
    crisis_id = args.get("crisis_id")
    user_id = args.get("user_id", deps.user_id)
    status = args.get("status", "safe")
    note = args.get("note", "")

    if not crisis_id:
        crisis = crisis_manager.get_crisis_by_channel(deps.channel_id)
        if crisis:
            crisis_id = crisis.id
        else:
            return {"content": [{"type": "text", "text": "No active crisis found in this channel."}]}

    # Add user to roster if not already there
    crisis_manager.add_to_roster(crisis_id, [user_id])

    checkin = crisis_manager.check_in(crisis_id, user_id, status, note)
    if not checkin:
        return {"content": [{"type": "text", "text": f"Could not check in — crisis {crisis_id} not found or already resolved."}]}

    crisis = crisis_manager.get_crisis(crisis_id)
    checked_in_count = len(crisis.check_ins)
    roster_count = len(crisis.team_roster)
    missing = crisis.missing_checkins

    status_emoji = {
        "safe": ":white_check_mark:",
        "injured": ":ambulance:",
        "evacuated": ":door:",
        "need-help": ":sos:",
    }

    response = (
        f"{status_emoji.get(status, ':white_check_mark:')} <@{user_id}> checked in as *{status}*"
    )
    if note:
        response += f" — {note}"
    response += f"\n\nCheck-in progress: {checked_in_count}/{roster_count}"

    if missing:
        response += f"\nStill missing: " + ", ".join(f"<@{uid}>" for uid in missing)

    if checked_in_count == roster_count and roster_count > 0:
        response += "\n\n:tada: *All personnel accounted for!*"

    return {"content": [{"type": "text", "text": response}]}
