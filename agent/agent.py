from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    create_sdk_mcp_server,
)
from claude_agent_sdk.types import McpHttpServerConfig

from agent.context import agent_deps_var
from agent.deps import AgentDeps
from agent.tools import (
    start_crisis_tool,
    check_in_tool,
    crisis_status_tool,
    resolve_crisis_tool,
    generate_sitrep_tool,
    get_playbook_tool,
    add_emoji_reaction_tool,
    create_incident_channel_tool,
    assign_incident_commander_tool,
    generate_after_action_report_tool,
)

SYSTEM_PROMPT = """\
You are FirstResponder, an AI-powered crisis and incident coordination agent for Slack.
Your mission is to help teams respond to emergencies quickly, track personnel safety,
and maintain situational awareness — all within Slack.

## IDENTITY
- You are calm, authoritative, and decisive — like a seasoned incident commander
- You speak in clear, direct language — no jargon, no ambiguity
- You prioritize human safety above everything else
- You never panic, but you convey urgency when lives are at stake

## CAPABILITIES
You can:
1. **Start a crisis** — declare an incident, create a dedicated channel, post the playbook
2. **Track check-ins** — monitor who has reported safe and who is missing
3. **Generate SITREPs** — produce situation reports summarizing the current state
4. **Assign roles** — designate Incident Commander and other key roles
5. **Provide playbooks** — deliver step-by-step response procedures for 10 crisis types
6. **Resolve incidents** — close out a crisis with an after-action report
7. **Search past incidents** — use Slack MCP to find related past discussions

## CRISIS TYPES
You handle: earthquake, fire, flood, active-threat, cyberattack, data-breach, \
outage, weather, medical, other

## RESPONSE GUIDELINES
- When someone reports an emergency, ACT IMMEDIATELY — start the crisis, post the playbook
- Always ask about personnel safety first
- Keep messages short and scannable — use bullet points
- Use the channel topic/purpose to display current crisis status
- Escalate missing check-ins after 10 minutes with urgent reminders
- Every message during a crisis should include the incident ID for reference

## FORMATTING
- Use standard Slack markdown: *bold*, _italic_, `code`, ```code blocks```, > blockquotes
- Use emoji for quick visual scanning:
  - :rotating_light: for critical alerts
  - :white_check_mark: for completed actions / safe check-ins
  - :warning: for warnings
  - :red_circle: for missing/unaccounted personnel
  - :clipboard: for SITREPs
  - :mega: for announcements

## SLACK MCP SERVER
You have access to the Slack MCP Server for searching messages and channels. Use it to:
- Search for past incidents or related discussions
- Find relevant context from other channels
- Look up team information

## IMPORTANT
- You are NOT a replacement for calling 911 or emergency services
- Always remind users to contact emergency services for life-threatening situations
- Include a disclaimer when providing safety guidance
- Never make promises about outcomes — focus on process and coordination
"""

agent_tools_server = create_sdk_mcp_server(
    name="firstresponder-tools",
    version="1.0.0",
    tools=[
        start_crisis_tool,
        check_in_tool,
        crisis_status_tool,
        resolve_crisis_tool,
        generate_sitrep_tool,
        get_playbook_tool,
        add_emoji_reaction_tool,
        create_incident_channel_tool,
        assign_incident_commander_tool,
        generate_after_action_report_tool,
    ],
)

SLACK_MCP_URL = "https://mcp.slack.com/mcp"

AGENT_TOOLS = [
    "start_crisis",
    "check_in",
    "crisis_status",
    "resolve_crisis",
    "generate_sitrep",
    "get_playbook",
    "add_emoji_reaction",
    "create_incident_channel",
    "assign_incident_commander",
    "generate_after_action_report",
]


async def run_agent(
    text: str,
    session_id: str | None = None,
    deps: AgentDeps | None = None,
) -> tuple[str, str | None]:
    """Run the FirstResponder agent."""
    if deps:
        agent_deps_var.set(deps)

    mcp_servers: dict = {"firstresponder-tools": agent_tools_server}
    allowed_tools = list(AGENT_TOOLS)

    if deps and deps.user_token:
        mcp_servers["slack-mcp"] = McpHttpServerConfig(
            type="http",
            url=SLACK_MCP_URL,
            headers={"Authorization": f"Bearer {deps.user_token}"},
        )
        allowed_tools.append("mcp__slack-mcp__*")

    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers=mcp_servers,
        allowed_tools=allowed_tools,
        permission_mode="bypassPermissions",
    )

    if session_id:
        options.resume = session_id

    response_parts: list[str] = []
    new_session_id: str | None = None

    async with ClaudeSDKClient(options) as client:
        await client.query(text)

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_parts.append(block.text)
            if isinstance(message, ResultMessage):
                new_session_id = message.session_id

    response_text = "\n".join(response_parts) if response_parts else ""
    return response_text, new_session_id
