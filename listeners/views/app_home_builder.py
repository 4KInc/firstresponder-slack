from crisis import crisis_manager, CRISIS_TYPES


def build_app_home_view(
    install_url: str | None = None, is_connected: bool = False
) -> dict:
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "FirstResponder - Crisis Coordination Agent",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "I help teams coordinate crisis and incident response directly in Slack. "
                    "From natural disasters to cyber attacks, I provide playbooks, track check-ins, "
                    "generate situation reports, and produce after-action reviews.\n\n"
                    "*Quick Start:*\n"
                    "- Type `/crisis start <type> <description>` to declare an incident\n"
                    "- DM me or @mention me in a channel for AI-assisted coordination\n"
                    "- React with :white_check_mark: during a crisis to check in as safe"
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Supported Crisis Types:*",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n".join(
                    f":{info['emoji']}: *{info['label']}* - `/crisis playbook {key}`"
                    for key, info in CRISIS_TYPES.items()
                ),
            },
        },
        {"type": "divider"},
    ]

    # Active crises section
    active = crisis_manager.get_active_crises()
    if active:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":rotating_light: *Active Crises ({len(active)})*",
            },
        })
        for c in active:
            info = CRISIS_TYPES.get(c.crisis_type, CRISIS_TYPES["other"])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f":{info['emoji']}: *{c.id}* - {info['label']}\n"
                        f"Severity: {c.severity.value.upper()} | "
                        f"Duration: {c.duration_minutes}min | "
                        f"Check-ins: {len(c.check_ins)}/{len(c.team_roster)}"
                    ),
                },
            })
    else:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":white_check_mark: *No active crises.* All clear.",
            },
        })

    blocks.append({"type": "divider"})

    # MCP connection status
    if is_connected:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\U0001f7e2 *Slack MCP Server is connected.* I can search messages and channels for incident context.",
            },
        })
    elif install_url:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"\U0001f534 *Slack MCP Server is disconnected.* <{install_url}|Connect now> to enable incident search.",
            },
        })
    else:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\U0001f534 *Slack MCP Server is disconnected.* Enable OAuth to allow incident search across channels.",
            },
        })

    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "_FirstResponder is not a replacement for calling 911 or emergency services. Always contact emergency services for life-threatening situations._",
            }
        ],
    })

    return {"type": "home", "blocks": blocks}
