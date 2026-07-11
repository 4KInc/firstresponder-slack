from claude_agent_sdk import tool
from slack_sdk.errors import SlackApiError

from agent.context import agent_deps_var
from crisis import crisis_manager, CrisisSeverity, CRISIS_TYPES
from crisis.playbooks import format_playbook_message


@tool(
    name="start_crisis",
    description="""\
Declare a new crisis incident. This creates a crisis record, generates an incident ID, \
and returns the playbook for the crisis type. Use this when someone reports an emergency \
or incident that needs coordinated response.

Available crisis types: earthquake, fire, flood, active-threat, cyberattack, \
data-breach, outage, weather, medical, other
""",
    input_schema={
        "type": "object",
        "properties": {
            "crisis_type": {
                "type": "string",
                "description": "Type of crisis (earthquake, fire, flood, active-threat, cyberattack, data-breach, outage, weather, medical, other)",
                "enum": list(CRISIS_TYPES.keys()),
            },
            "description": {
                "type": "string",
                "description": "Brief description of the crisis situation",
            },
            "severity": {
                "type": "string",
                "description": "Override severity level (optional, defaults based on crisis type)",
                "enum": ["critical", "high", "medium", "low"],
            },
        },
        "required": ["crisis_type", "description"],
    },
)
async def start_crisis_tool(args):
    deps = agent_deps_var.get()
    crisis_type = args["crisis_type"]
    description = args["description"]
    severity = CrisisSeverity(args["severity"]) if "severity" in args else None

    crisis = crisis_manager.start_crisis(
        crisis_type=crisis_type,
        description=description,
        channel_id=deps.channel_id,
        created_by=deps.user_id,
        severity=severity,
    )

    # Seed the roster with the channel's members so "who's missing?" works.
    from agent.roster import seed_roster_from_channel
    await seed_roster_from_channel(deps.client, crisis.id, deps.channel_id)

    crisis_info = CRISIS_TYPES.get(crisis_type, CRISIS_TYPES["other"])
    playbook_text = format_playbook_message(crisis_type)

    return {
        "content": [
            {
                "type": "text",
                "text": (
                    f"Crisis declared successfully.\n"
                    f"Incident ID: {crisis.id}\n"
                    f"Type: {crisis_info['label']}\n"
                    f"Severity: {crisis.severity.value.upper()}\n"
                    f"Status: ACTIVE\n"
                    f"Channel: <#{crisis.channel_id}>\n\n"
                    f"Playbook:\n{playbook_text}\n\n"
                    f"Next steps: Create a dedicated incident channel, assign an Incident Commander, "
                    f"and ask team members to check in."
                ),
            }
        ]
    }


@tool(
    name="crisis_status",
    description="Get the current status of an active crisis, including check-ins, missing personnel, and timeline.",
    input_schema={
        "type": "object",
        "properties": {
            "crisis_id": {
                "type": "string",
                "description": "The incident ID (e.g., INC-20260628-143000-001). If not provided, uses the crisis associated with the current channel.",
            },
        },
    },
)
async def crisis_status_tool(args):
    deps = agent_deps_var.get()
    crisis_id = args.get("crisis_id")

    if crisis_id:
        crisis = crisis_manager.get_crisis(crisis_id)
    else:
        crisis = crisis_manager.get_crisis_by_channel(deps.channel_id)

    if not crisis:
        active = crisis_manager.get_active_crises()
        if active:
            summary = "\n".join(
                f"- *{c.id}*: {CRISIS_TYPES.get(c.crisis_type, CRISIS_TYPES['other'])['label']} "
                f"— {c.description} ({c.severity.value.upper()}, {c.duration_minutes}min)"
                for c in active
            )
            return {"content": [{"type": "text", "text": f"No crisis in this channel. Active crises:\n{summary}"}]}
        return {"content": [{"type": "text", "text": "No active crises found."}]}

    crisis_info = CRISIS_TYPES.get(crisis.crisis_type, CRISIS_TYPES["other"])
    checked_in = len(crisis.check_ins)
    roster_size = len(crisis.team_roster)
    missing = crisis.missing_checkins

    status_lines = [
        f"Incident: {crisis.id}",
        f"Type: {crisis_info['label']}",
        f"Severity: {crisis.severity.value.upper()}",
        f"Status: {crisis.status.value.upper()}",
        f"Duration: {crisis.duration_minutes} minutes",
        f"Incident Commander: {'<@' + crisis.incident_commander + '>' if crisis.incident_commander else 'Not assigned'}",
        f"Check-ins: {checked_in}/{roster_size}",
    ]

    if missing:
        status_lines.append(f"MISSING ({len(missing)}): " + ", ".join(f"<@{uid}>" for uid in missing))

    if crisis.sitreps:
        status_lines.append(f"SITREPs generated: {len(crisis.sitreps)}")

    return {"content": [{"type": "text", "text": "\n".join(status_lines)}]}


@tool(
    name="resolve_crisis",
    description="Resolve and close out an active crisis. Generates an after-action report summary.",
    input_schema={
        "type": "object",
        "properties": {
            "crisis_id": {
                "type": "string",
                "description": "The incident ID to resolve. If not provided, resolves the crisis in the current channel.",
            },
        },
    },
)
async def resolve_crisis_tool(args):
    deps = agent_deps_var.get()
    crisis_id = args.get("crisis_id")

    if crisis_id:
        crisis = crisis_manager.resolve_crisis(crisis_id, deps.user_id)
    else:
        active = crisis_manager.get_crisis_by_channel(deps.channel_id)
        if active:
            crisis = crisis_manager.resolve_crisis(active.id, deps.user_id)
        else:
            return {"content": [{"type": "text", "text": "No active crisis found to resolve."}]}

    if not crisis:
        return {"content": [{"type": "text", "text": "Crisis not found."}]}

    return {
        "content": [
            {
                "type": "text",
                "text": (
                    f"Crisis {crisis.id} has been RESOLVED.\n"
                    f"Duration: {crisis.duration_minutes} minutes\n"
                    f"Check-ins: {len(crisis.check_ins)}/{len(crisis.team_roster)}\n"
                    f"SITREPs generated: {len(crisis.sitreps)}\n"
                    f"Timeline events: {len(crisis.timeline)}\n\n"
                    f"Use generate_after_action_report to create the full report."
                ),
            }
        ]
    }


@tool(
    name="create_incident_channel",
    description="""\
Create a dedicated Slack channel for a crisis incident. The channel name is auto-generated \
from the crisis type and date. Use this right after starting a crisis to give the team \
a dedicated coordination space.
""",
    input_schema={
        "type": "object",
        "properties": {
            "crisis_id": {
                "type": "string",
                "description": "The incident ID to create a channel for.",
            },
        },
        "required": ["crisis_id"],
    },
)
async def create_incident_channel_tool(args):
    deps = agent_deps_var.get()
    crisis_id = args["crisis_id"]
    crisis = crisis_manager.get_crisis(crisis_id)

    if not crisis:
        return {"content": [{"type": "text", "text": f"Crisis {crisis_id} not found."}]}

    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    channel_name = f"incident-{crisis.crisis_type}-{ts}"
    # Slack channel names: lowercase, no spaces, max 80 chars
    channel_name = channel_name.lower().replace(" ", "-")[:80]

    try:
        result = await deps.client.conversations_create(
            name=channel_name,
            is_private=False,
        )
        new_channel_id = result["channel"]["id"]

        # Update the crisis with the new channel AND keep the channel->crisis map
        # in sync so check-ins/status/SITREPs work from the new incident channel.
        crisis_manager.reassign_channel(crisis.id, new_channel_id)
        crisis.add_timeline_event("channel_created", f"Incident channel <#{new_channel_id}> created", deps.user_id)

        crisis_info = CRISIS_TYPES.get(crisis.crisis_type, CRISIS_TYPES["other"])

        # Set channel topic
        await deps.client.conversations_setTopic(
            channel=new_channel_id,
            topic=f":rotating_light: {crisis_info['label']} — {crisis.severity.value.upper()} | {crisis.id} | Status: ACTIVE",
        )

        # Set channel purpose
        await deps.client.conversations_setPurpose(
            channel=new_channel_id,
            purpose=crisis.description,
        )

        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"Incident channel created: <#{new_channel_id}>\n"
                        f"Channel: #{channel_name}\n"
                        f"Linked to: {crisis.id}\n\n"
                        f"Team members should join this channel for coordination. "
                        f"Post the playbook and ask for check-ins."
                    ),
                }
            ]
        }

    except SlackApiError as e:
        return {"content": [{"type": "text", "text": f"Failed to create channel: {e.response['error']}"}]}


@tool(
    name="assign_incident_commander",
    description="Assign a user as the Incident Commander for a crisis. The IC has overall coordination authority.",
    input_schema={
        "type": "object",
        "properties": {
            "crisis_id": {
                "type": "string",
                "description": "The incident ID.",
            },
            "user_id": {
                "type": "string",
                "description": "The Slack user ID to assign as IC (e.g., U01ABCDEF).",
            },
        },
        "required": ["crisis_id", "user_id"],
    },
)
async def assign_incident_commander_tool(args):
    crisis_id = args["crisis_id"]
    user_id = args["user_id"]

    success = crisis_manager.set_incident_commander(crisis_id, user_id)
    if not success:
        return {"content": [{"type": "text", "text": f"Crisis {crisis_id} not found."}]}

    return {
        "content": [
            {
                "type": "text",
                "text": f"<@{user_id}> has been assigned as Incident Commander for {crisis_id}.",
            }
        ]
    }


@tool(
    name="generate_after_action_report",
    description="Generate a comprehensive after-action report for a crisis, including timeline, check-ins, SITREPs, and lessons learned.",
    input_schema={
        "type": "object",
        "properties": {
            "crisis_id": {
                "type": "string",
                "description": "The incident ID to generate the report for.",
            },
        },
        "required": ["crisis_id"],
    },
)
async def generate_after_action_report_tool(args):
    crisis_id = args["crisis_id"]
    report = crisis_manager.generate_after_action_report(crisis_id)

    if not report:
        return {"content": [{"type": "text", "text": f"Crisis {crisis_id} not found."}]}

    return {"content": [{"type": "text", "text": report}]}
