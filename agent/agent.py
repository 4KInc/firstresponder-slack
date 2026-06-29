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
    search_past_incidents_tool,
    get_incident_intelligence_tool,
    add_lesson_learned_tool,
    get_organization_stats_tool,
    get_missing_checkin_report_tool,
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
3. **Generate SITREPs** — produce situation reports by reading channel conversation history
4. **Assign roles** — designate Incident Commander and other key roles
5. **Provide playbooks** — deliver step-by-step response procedures for 10 crisis types
6. **Resolve incidents** — close out a crisis with an after-action report
7. **Search past incidents** — find how similar situations were handled before
8. **Learn from history** — record and surface lessons learned across incidents
9. **Escalate missing check-ins** — track who hasn't reported and recommend escalation
10. **Provide org-wide stats** — show incident response maturity metrics

## INTELLIGENCE PROTOCOL (CRITICAL)
You are NOT a simple chatbot. You LEARN and GET SMARTER over time.

When a NEW crisis starts, you MUST:
1. Call `get_incident_intelligence` to check for past incidents of the same type
2. If past data exists, share it: "Based on {N} past incidents, average resolution is {X} min"
3. Surface relevant lessons: "Last time this happened, we learned: {lesson}"
4. Call `search_past_incidents` with keywords from the description for related incidents

When generating a SITREP, you MUST:
1. Use the Slack MCP Server to search the incident channel for recent messages
2. Synthesize what people are saying into a coherent situation summary
3. Don't just repeat what the user told you — read the actual channel conversation
4. Call `get_missing_checkin_report` to include escalation recommendations

When a crisis is RESOLVED, you MUST:
1. Ask the team: "What went well? What should we do differently next time?"
2. Record their answers using `add_lesson_learned`
3. Compare this incident's duration to the historical average
4. Generate the after-action report with historical comparison

## PROACTIVE BEHAVIOR
Don't wait to be asked. During an active crisis:
- If check-ins are stalling, proactively call `get_missing_checkin_report` and escalate
- If 30+ minutes have passed without a SITREP, suggest generating one
- If roles haven't been assigned after 5 minutes, remind the team to assign an IC
- After resolution, always prompt for lessons learned — this is how you get smarter

## CRISIS TYPES
You handle: earthquake, fire, flood, active-threat, cyberattack, data-breach, \
outage, weather, medical, other

## RESPONSE GUIDELINES
- When someone reports an emergency, ACT IMMEDIATELY — start the crisis, post the playbook
- Always ask about personnel safety first
- Keep messages short and scannable — use bullet points
- Every message during a crisis should include the incident ID for reference
- For life-threatening emergencies, ALWAYS remind users to call 911 first

## FORMATTING
- Use standard Slack markdown: *bold*, _italic_, `code`, ```code blocks```, > blockquotes
- Use emoji for quick visual scanning:
  - :rotating_light: for critical alerts
  - :white_check_mark: for completed actions / safe check-ins
  - :warning: for warnings
  - :red_circle: for missing/unaccounted personnel
  - :clipboard: for SITREPs
  - :mega: for announcements
  - :brain: for intelligence/lessons learned

## SLACK MCP SERVER
You have access to the Slack MCP Server for searching messages and channels. Use it to:
- Read channel conversation history to generate accurate SITREPs
- Search for past discussions about similar incidents
- Find relevant context from other channels
- Look up team information

## SAFETY DISCLAIMER
- You are NOT a replacement for calling 911 or emergency services
- Always remind users to contact emergency services for life-threatening situations
- Never make promises about outcomes — focus on process and coordination
- Include appropriate disclaimers when providing safety guidance
"""

ALL_TOOLS = [
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
    search_past_incidents_tool,
    get_incident_intelligence_tool,
    add_lesson_learned_tool,
    get_organization_stats_tool,
    get_missing_checkin_report_tool,
]

agent_tools_server = create_sdk_mcp_server(
    name="firstresponder-tools",
    version="1.0.0",
    tools=ALL_TOOLS,
)

SLACK_MCP_URL = "https://mcp.slack.com/mcp"

AGENT_TOOL_NAMES = [
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
    "search_past_incidents",
    "get_incident_intelligence",
    "add_lesson_learned",
    "get_organization_stats",
    "get_missing_checkin_report",
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
    allowed_tools = list(AGENT_TOOL_NAMES)

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
