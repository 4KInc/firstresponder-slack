"""AI-powered intelligence tools — learning, pattern recognition, and recommendations."""

from claude_agent_sdk import tool

from agent.context import agent_deps_var
from crisis import crisis_manager, CRISIS_TYPES


@tool(
    name="search_past_incidents",
    description="""\
Search past resolved incidents by keyword. Use this to find how similar situations \
were handled before, what worked, what didn't, and how long they took to resolve. \
Always check past incidents when a new crisis starts — learning from history saves lives.
""",
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search term (e.g., 'fire', 'database', 'ransomware', 'east wing')",
            },
        },
        "required": ["query"],
    },
)
async def search_past_incidents_tool(args):
    query = args["query"]
    results = crisis_manager.search_past_incidents(query)

    if not results:
        return {"content": [{"type": "text", "text": f"No past incidents found matching '{query}'."}]}

    lines = [f"Found {len(results)} past incident(s) matching '{query}':\n"]
    for inc in results:
        info = CRISIS_TYPES.get(inc["crisis_type"], CRISIS_TYPES["other"])
        lines.append(
            f"- *{inc['id']}* — {info['label']}: {inc['description']}\n"
            f"  Severity: {inc['severity'].upper()} | Duration: {inc['duration_minutes']}min | "
            f"Status: {inc['status'].upper()}"
        )

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


@tool(
    name="get_incident_intelligence",
    description="""\
Get intelligence and patterns from past incidents of a specific crisis type. \
Returns average resolution time, lessons learned, and recent similar incidents. \
Use this when starting a new crisis to inform the team what to expect based on history.
""",
    input_schema={
        "type": "object",
        "properties": {
            "crisis_type": {
                "type": "string",
                "description": "Type of crisis to get intelligence for",
                "enum": list(CRISIS_TYPES.keys()),
            },
        },
        "required": ["crisis_type"],
    },
)
async def get_incident_intelligence_tool(args):
    crisis_type = args["crisis_type"]
    context = crisis_manager.get_past_context(crisis_type)
    crisis_info = CRISIS_TYPES.get(crisis_type, CRISIS_TYPES["other"])

    if not context.get("has_data"):
        return {"content": [{"type": "text", "text": f"No past {crisis_info['label']} incidents to learn from. This is the first one."}]}

    lines = [
        f"Intelligence for {crisis_info['label']} incidents:\n",
        f"- Past incidents: {context['past_incident_count']}",
        f"- Average resolution time: {context['avg_resolution_minutes']} minutes",
    ]

    if context.get("lessons"):
        lines.append(f"\nLessons learned from past incidents:")
        for lesson in context["lessons"]:
            lines.append(f"- {lesson}")

    if context.get("recent_incidents"):
        lines.append(f"\nMost recent {crisis_info['label']} incidents:")
        for inc in context["recent_incidents"]:
            lines.append(f"- {inc['id']}: {inc['description']} ({inc['duration']}min)")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


@tool(
    name="add_lesson_learned",
    description="""\
Record a lesson learned from a crisis. Lessons are stored permanently and surfaced \
during future incidents of the same type. Use this during or after a crisis when \
the team identifies something that worked well, something that went wrong, or a \
process improvement. Good lessons are specific and actionable.

Examples of good lessons:
- "Sandbagging the server room entrance prevented water damage to critical systems"
- "The 5-minute delay in isolating the compromised server allowed lateral movement"
- "Having pre-designated floor wardens cut evacuation time by 40%"
""",
    input_schema={
        "type": "object",
        "properties": {
            "crisis_id": {
                "type": "string",
                "description": "The incident ID this lesson relates to.",
            },
            "lesson": {
                "type": "string",
                "description": "The lesson learned — be specific and actionable.",
            },
            "category": {
                "type": "string",
                "description": "Category of the lesson",
                "enum": ["communication", "coordination", "technical", "safety", "timing", "resources", "general"],
                "default": "general",
            },
        },
        "required": ["crisis_id", "lesson"],
    },
)
async def add_lesson_learned_tool(args):
    crisis_id = args["crisis_id"]
    lesson = args["lesson"]
    category = args.get("category", "general")

    crisis_manager.add_lesson_learned(crisis_id, lesson, category)

    return {
        "content": [
            {
                "type": "text",
                "text": (
                    f"Lesson recorded for {crisis_id} [{category}]:\n"
                    f"> {lesson}\n\n"
                    f"This will be surfaced in future {category} situations to help teams respond better."
                ),
            }
        ]
    }


@tool(
    name="get_organization_stats",
    description="""\
Get aggregate incident response statistics for the organization. Shows total incidents, \
average resolution time, check-in rates, breakdown by type, and total lessons learned. \
Use this to give the team a picture of their incident response maturity.
""",
    input_schema={
        "type": "object",
        "properties": {},
    },
)
async def get_organization_stats_tool(args):
    stats = crisis_manager.get_stats()

    if stats["total_incidents"] == 0:
        return {"content": [{"type": "text", "text": "No incidents recorded yet. Stats will appear after the first crisis."}]}

    lines = [
        "Organization Incident Response Stats:\n",
        f"- Total incidents: {stats['total_incidents']}",
        f"- Resolved: {stats['resolved']}",
        f"- Active: {stats['active']}",
        f"- Average resolution time: {stats['avg_duration_minutes']} minutes",
        f"- Average check-in rate: {stats['avg_checkin_rate']}%",
        f"- Lessons learned: {stats['total_lessons']}",
    ]

    if stats["by_type"]:
        lines.append("\nBreakdown by type:")
        for ctype, count in stats["by_type"].items():
            info = CRISIS_TYPES.get(ctype, CRISIS_TYPES["other"])
            lines.append(f"- {info['label']}: {count}")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


@tool(
    name="get_missing_checkin_report",
    description="""\
Generate an escalation report for personnel who haven't checked in during an active crisis. \
Includes how long each person has been missing and recommends escalation actions. \
Use this proactively — don't wait for someone to ask about missing people.
""",
    input_schema={
        "type": "object",
        "properties": {
            "crisis_id": {
                "type": "string",
                "description": "The incident ID. If not provided, uses the crisis in the current channel.",
            },
        },
    },
)
async def get_missing_checkin_report_tool(args):
    deps = agent_deps_var.get()
    crisis_id = args.get("crisis_id")

    if not crisis_id:
        crisis = crisis_manager.get_crisis_by_channel(deps.channel_id)
        if crisis:
            crisis_id = crisis.id
        else:
            return {"content": [{"type": "text", "text": "No active crisis in this channel."}]}

    crisis = crisis_manager.get_crisis(crisis_id)
    if not crisis:
        return {"content": [{"type": "text", "text": f"Crisis {crisis_id} not found."}]}

    missing = crisis.missing_checkins
    duration = crisis.duration_minutes

    if not missing:
        return {"content": [{"type": "text", "text": f"All {len(crisis.team_roster)} personnel accounted for."}]}

    lines = [
        f"MISSING PERSONNEL REPORT — {crisis.id}",
        f"Crisis duration: {duration} minutes",
        f"Missing: {len(missing)}/{len(crisis.team_roster)}\n",
    ]

    # Escalation levels based on time
    if duration < 5:
        level = "INITIAL — send reminder"
    elif duration < 15:
        level = "ELEVATED — direct message each missing person"
    elif duration < 30:
        level = "HIGH — attempt phone contact, notify their manager"
    else:
        level = "CRITICAL — assume in danger, notify emergency services"

    lines.append(f"Escalation level: *{level}*\n")
    lines.append("Missing personnel:")
    for uid in missing:
        lines.append(f"- <@{uid}> — no check-in for {duration} minutes")

    lines.append(f"\nRecommended action: {level.split(' — ')[1]}")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}
