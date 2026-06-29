from claude_agent_sdk import tool

from crisis.models import CRISIS_TYPES
from crisis.playbooks import format_playbook_message


@tool(
    name="get_playbook",
    description="""\
Retrieve the response playbook for a specific crisis type. Playbooks include \
immediate actions, roles needed, and resources required. Use this when someone \
asks for guidance on how to handle a specific type of crisis.
""",
    input_schema={
        "type": "object",
        "properties": {
            "crisis_type": {
                "type": "string",
                "description": "Type of crisis to get the playbook for",
                "enum": list(CRISIS_TYPES.keys()),
            },
        },
        "required": ["crisis_type"],
    },
)
async def get_playbook_tool(args):
    crisis_type = args["crisis_type"]
    playbook_text = format_playbook_message(crisis_type)
    return {"content": [{"type": "text", "text": playbook_text}]}
