from logging import Logger

from slack_bolt import Ack
from slack_bolt.context.async_context import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient

from crisis import crisis_manager, CRISIS_TYPES, CrisisSeverity
from crisis.playbooks import format_playbook_message


async def handle_crisis_command(
    ack: Ack,
    command: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    """Handle /crisis slash command.

    Usage:
        /crisis start <type> <description>
        /crisis status
        /crisis checkin [status]
        /crisis resolve
        /crisis playbook <type>
        /crisis help
    """
    await ack()

    try:
        text = command.get("text", "").strip()
        channel_id = command["channel_id"]
        user_id = command["user_id"]
        parts = text.split(maxsplit=2)

        if not parts or parts[0] == "help":
            await _send_help(client, channel_id, user_id)
            return

        subcommand = parts[0].lower()

        if subcommand == "start":
            await _handle_start(client, channel_id, user_id, parts)
        elif subcommand == "status":
            await _handle_status(client, channel_id, user_id)
        elif subcommand == "checkin":
            await _handle_checkin(client, channel_id, user_id, parts)
        elif subcommand == "resolve":
            await _handle_resolve(client, channel_id, user_id)
        elif subcommand == "playbook":
            await _handle_playbook(client, channel_id, user_id, parts)
        elif subcommand == "setup":
            await _handle_setup(client, channel_id, user_id)
        else:
            await client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f":warning: Unknown subcommand `{subcommand}`. Use `/crisis help` for usage.",
            )

    except Exception as e:
        logger.exception(f"Failed to handle /crisis command: {e}")
        await client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f":warning: Something went wrong: {e}",
        )


async def _send_help(client, channel_id, user_id):
    help_text = (
        "*FirstResponder — Crisis Coordination Commands*\n\n"
        "`/crisis start <type> <description>` — Declare a new crisis\n"
        "`/crisis status` — View active crisis status\n"
        "`/crisis checkin [safe|injured|evacuated|need-help]` — Check in\n"
        "`/crisis resolve` — Resolve the active crisis\n"
        "`/crisis playbook <type>` — View a response playbook\n"
        "`/crisis setup` — Configure your building and personnel\n"
        "`/crisis help` — Show this help message\n\n"
        f"*Crisis types:* {', '.join(CRISIS_TYPES.keys())}"
    )
    await client.chat_postEphemeral(channel=channel_id, user=user_id, text=help_text)


async def _handle_setup(client, channel_id, user_id):
    from crisis.knowledge import knowledge_base
    summary = knowledge_base.get_facility_summary()
    non_zero = {k: v for k, v in summary.items() if v > 0}

    if non_zero:
        status_text = "*Current Knowledge Base:*\n" + "\n".join(
            f"- {k.replace('_', ' ').title()}: {v}" for k, v in non_zero.items()
        )
    else:
        status_text = ":warning: *Knowledge base is empty.* FirstResponder will give generic guidance until you upload your building data."

    setup_text = (
        "*FirstResponder — Setup Your Building*\n\n"
        f"{status_text}\n\n"
        "---\n\n"
        "*How to configure:*\n"
        "1. Download CSV templates from the GitHub repo (`templates/` folder)\n"
        "2. Fill them out with your building's data\n"
        "3. DM me (FirstResponder) and drag-drop each CSV file (any order — I auto-detect the type)\n"
        "4. Re-upload anytime to update — I replace, not duplicate\n\n"
        "*Building & people (start here):*\n"
        "`facility.csv` · `zones.csv` · `rooms.csv` · `personnel.csv`\n\n"
        "*Safety & evacuation:*\n"
        "`emergency_resources.csv` (AEDs, extinguishers) · `evacuation_routes.csv` · `assembly_points.csv` · "
        "`utility_controls.csv` (gas/electric shutoffs) · `hazmat_locations.csv` · `nearby_services.csv` (hospitals, police, fire) · `drills.csv`\n\n"
        "*IT & operations (optional):*\n"
        "`network_assets.csv` · `data_inventory.csv` · `runbooks.csv` · `on_call_schedules.csv` · `continuity_plans.csv` · `vendor_contacts.csv`\n\n"
        "*The more data you upload, the smarter FirstResponder becomes during a crisis.*\n"
        "Without data: generic playbooks. With data: room-specific evacuation, named personnel, nearest AED locations."
    )
    await client.chat_postEphemeral(channel=channel_id, user=user_id, text=setup_text)


async def _handle_start(client, channel_id, user_id, parts):
    if len(parts) < 3:
        await client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f":warning: Usage: `/crisis start <type> <description>`\nTypes: {', '.join(CRISIS_TYPES.keys())}",
        )
        return

    crisis_type = parts[1].lower()
    description = parts[2]

    if crisis_type not in CRISIS_TYPES:
        await client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f":warning: Unknown crisis type `{crisis_type}`. Available: {', '.join(CRISIS_TYPES.keys())}",
        )
        return

    crisis = crisis_manager.start_crisis(
        crisis_type=crisis_type,
        description=description,
        channel_id=channel_id,
        created_by=user_id,
    )

    # Seed the roster with this channel's members so "who's missing?" works.
    from agent.roster import seed_roster_from_channel
    await seed_roster_from_channel(client, crisis.id, channel_id)

    crisis_info = CRISIS_TYPES[crisis_type]
    playbook_text = format_playbook_message(crisis_type)

    # Post publicly to the channel
    await client.chat_postMessage(
        channel=channel_id,
        text=(
            f":rotating_light: *CRISIS DECLARED — {crisis_info['label'].upper()}*\n\n"
            f"*Incident ID:* `{crisis.id}`\n"
            f"*Severity:* {crisis.severity.value.upper()}\n"
            f"*Description:* {description}\n"
            f"*Declared by:* <@{user_id}>\n\n"
            f"---\n\n"
            f"{playbook_text}\n\n"
            f"---\n\n"
            f":white_check_mark: *React with :white_check_mark: to this message to check in as safe*\n"
            f":sos: React with :sos: if you need help\n"
            f":ambulance: React with :ambulance: if injured\n\n"
            f"_Use `/crisis status` for current status or `/crisis checkin` to check in._"
        ),
    )


async def _handle_status(client, channel_id, user_id):
    crisis = crisis_manager.get_crisis_by_channel(channel_id)

    # Fall back to any active crisis if none in this channel
    if not crisis:
        active = crisis_manager.get_active_crises()
        if not active:
            await client.chat_postEphemeral(
                channel=channel_id, user=user_id, text=":white_check_mark: No active crises."
            )
            return
        if len(active) == 1:
            crisis = active[0]
        else:
            # Multiple active crises — list them all
            lines = [":clipboard: *Active Crises:*\n"]
            for c in active:
                info = CRISIS_TYPES.get(c.crisis_type, CRISIS_TYPES["other"])
                lines.append(
                    f":{info['emoji']}: *{c.id}* — {info['label']} | "
                    f"{c.severity.value.upper()} | {c.duration_minutes}min | "
                    f"Check-ins: {len(c.check_ins)}/{len(c.team_roster)}"
                )
            await client.chat_postEphemeral(channel=channel_id, user=user_id, text="\n".join(lines))
            return

    info = CRISIS_TYPES.get(crisis.crisis_type, CRISIS_TYPES["other"])
    missing = crisis.missing_checkins

    status_text = (
        f":{info['emoji']}: *{crisis.id} — {info['label']}*\n\n"
        f"*Severity:* {crisis.severity.value.upper()}\n"
        f"*Status:* {crisis.status.value.upper()}\n"
        f"*Duration:* {crisis.duration_minutes} minutes\n"
        f"*IC:* {'<@' + crisis.incident_commander + '>' if crisis.incident_commander else 'Not assigned'}\n"
        f"*Check-ins:* {len(crisis.check_ins)}/{len(crisis.team_roster)}\n"
    )

    if missing:
        status_text += f"\n:red_circle: *Missing:* " + ", ".join(f"<@{uid}>" for uid in missing)

    await client.chat_postEphemeral(channel=channel_id, user=user_id, text=status_text)


async def _handle_checkin(client, channel_id, user_id, parts):
    status = parts[1] if len(parts) > 1 else "safe"
    valid_statuses = ["safe", "injured", "evacuated", "need-help"]
    if status not in valid_statuses:
        await client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f":warning: Invalid status. Use: {', '.join(valid_statuses)}",
        )
        return

    crisis = crisis_manager.get_crisis_by_channel(channel_id)
    if not crisis:
        active = crisis_manager.get_active_crises()
        if active:
            crisis = active[0]
        else:
            await client.chat_postEphemeral(
                channel=channel_id, user=user_id, text=":warning: No active crisis to check in to."
            )
            return

    crisis_manager.add_to_roster(crisis.id, [user_id])
    checkin = crisis_manager.check_in(crisis.id, user_id, status)

    if checkin:
        status_emoji = {"safe": ":white_check_mark:", "injured": ":ambulance:", "evacuated": ":door:", "need-help": ":sos:"}
        await client.chat_postMessage(
            channel=crisis.channel_id,
            text=f"{status_emoji.get(status, ':white_check_mark:')} <@{user_id}> checked in as *{status}* ({len(crisis.check_ins)}/{len(crisis.team_roster)})",
        )


async def _handle_resolve(client, channel_id, user_id):
    crisis = crisis_manager.get_crisis_by_channel(channel_id)
    if not crisis:
        # Fall back to any active crisis (may have been started in a DM or other channel)
        active = crisis_manager.get_active_crises()
        if active:
            crisis = active[0]
        else:
            await client.chat_postEphemeral(
                channel=channel_id, user=user_id, text=":warning: No active crises to resolve."
            )
            return

    resolved = crisis_manager.resolve_crisis(crisis.id, user_id)
    if not resolved:
        await client.chat_postEphemeral(
            channel=channel_id, user=user_id,
            text=":warning: That crisis was already resolved.",
        )
        return
    report = crisis_manager.generate_after_action_report(crisis.id) or "_(report unavailable)_"

    await client.chat_postMessage(
        channel=resolved.channel_id,
        text=(
            f":heavy_check_mark: *Crisis {resolved.id} RESOLVED*\n\n"
            f"*Duration:* {resolved.duration_minutes} minutes\n"
            f"*Check-ins:* {len(resolved.check_ins)}/{len(resolved.team_roster)}\n"
            f"*SITREPs:* {len(resolved.sitreps)}\n\n"
            f"---\n\n"
            f"{report}"
        ),
    )


async def _handle_playbook(client, channel_id, user_id, parts):
    if len(parts) < 2:
        await client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f":warning: Usage: `/crisis playbook <type>`\nTypes: {', '.join(CRISIS_TYPES.keys())}",
        )
        return

    crisis_type = parts[1].lower()
    if crisis_type not in CRISIS_TYPES:
        await client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f":warning: Unknown type `{crisis_type}`. Available: {', '.join(CRISIS_TYPES.keys())}",
        )
        return

    playbook_text = format_playbook_message(crisis_type)
    await client.chat_postEphemeral(channel=channel_id, user=user_id, text=playbook_text)
