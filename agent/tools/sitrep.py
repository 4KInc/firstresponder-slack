from claude_agent_sdk import tool

from agent.context import agent_deps_var
from crisis import crisis_manager


@tool(
    name="generate_sitrep",
    description="""\
Generate a Situation Report (SITREP) for an active crisis. The SITREP summarizes \
the current situation, personnel status, and actions taken. Use this periodically \
during a crisis to maintain situational awareness.
""",
    input_schema={
        "type": "object",
        "properties": {
            "crisis_id": {
                "type": "string",
                "description": "The incident ID. If not provided, uses the crisis in the current channel.",
            },
            "summary": {
                "type": "string",
                "description": "AI-generated summary of the current situation based on channel discussion.",
            },
            "actions_taken": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of actions taken since the last SITREP.",
            },
        },
        "required": ["summary", "actions_taken"],
    },
)
async def generate_sitrep_tool(args):
    deps = agent_deps_var.get()
    crisis_id = args.get("crisis_id")
    summary = args["summary"]
    actions_taken = args["actions_taken"]

    if not crisis_id:
        crisis = crisis_manager.get_crisis_by_channel(deps.channel_id)
        if crisis:
            crisis_id = crisis.id
        else:
            return {"content": [{"type": "text", "text": "No active crisis found in this channel."}]}

    sitrep = crisis_manager.add_sitrep(crisis_id, summary, actions_taken)
    if not sitrep:
        return {"content": [{"type": "text", "text": f"Could not generate SITREP - crisis {crisis_id} not found."}]}

    lines = [
        f"SITREP #{sitrep.number} - {sitrep.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"Incident: {crisis_id}",
        "",
        f"*Situation:*\n{sitrep.summary}",
        "",
        f"*Personnel Status:*",
        f"- Checked in: {len(sitrep.checked_in)}",
        f"- Missing: {len(sitrep.missing)}",
    ]

    if sitrep.missing:
        lines.append(f"- Unaccounted: " + ", ".join(f"<@{uid}>" for uid in sitrep.missing))

    lines.append("")
    lines.append("*Actions Taken:*")
    for action in sitrep.actions_taken:
        lines.append(f"- {action}")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}
