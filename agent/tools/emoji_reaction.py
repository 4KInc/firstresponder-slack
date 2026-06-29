from claude_agent_sdk import tool
from slack_sdk.errors import SlackApiError

from agent.context import agent_deps_var


@tool(
    name="add_emoji_reaction",
    description="""\
Add an emoji reaction to the user's message. Use contextually appropriate emoji:
- Crisis alerts: rotating_light, warning, sos, fire
- Check-ins: white_check_mark, thumbsup
- Reports: clipboard, memo, bar_chart
- Resolution: tada, heavy_check_mark, star
""",
    input_schema={
        "type": "object",
        "properties": {
            "emoji_name": {
                "type": "string",
                "description": "The Slack emoji name without colons (e.g., 'rotating_light', 'white_check_mark').",
            },
        },
        "required": ["emoji_name"],
    },
)
async def add_emoji_reaction_tool(args):
    deps = agent_deps_var.get()
    emoji_name = args["emoji_name"]

    try:
        await deps.client.reactions_add(
            channel=deps.channel_id,
            timestamp=deps.message_ts,
            name=emoji_name,
        )
        return {"content": [{"type": "text", "text": f"Reacted with :{emoji_name}:"}]}
    except SlackApiError as e:
        return {"content": [{"type": "text", "text": f"Could not add reaction: {e.response['error']}"}]}
