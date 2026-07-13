"""Classroom-level accountability — how schools actually track students in a crisis.

Students are never stored as named individuals (privacy). Instead each TEACHER
reports their classroom's headcount ("Room 104: 23 of 25 safe, 2 missing"), and
the incident commander gets a per-classroom board: which rooms are all-safe,
which have missing students, and which haven't reported yet.
"""

from claude_agent_sdk import tool

from agent.context import agent_deps_var
from crisis import crisis_manager
from crisis.knowledge import knowledge_base


def _text(t):
    return {"content": [{"type": "text", "text": t}]}


def _active_crisis(deps, crisis_id=None):
    if crisis_id:
        return crisis_manager.get_crisis(crisis_id)
    crisis = crisis_manager.get_crisis_by_channel(deps.channel_id)
    if crisis:
        return crisis
    active = crisis_manager.get_active_crises()
    return active[0] if active else None


def _teacher(room: dict) -> str:
    notes = (room or {}).get("notes", "") or ""
    return notes.split(" - ")[-1].strip() if " - " in notes else notes


def _board(crisis, zone_id=None) -> dict:
    classrooms = knowledge_base.get_zone_occupancy(zone_id=zone_id)["rooms"]
    reports = crisis.classroom_reports
    reported = [c for c in classrooms if c["id"] in reports]
    unreported = [c for c in classrooms if c["id"] not in reports]
    return {
        "classrooms": classrooms,
        "reported": reported,
        "unreported": unreported,
        "safe": sum(reports[c["id"]].students_safe for c in reported),
        "missing": sum(reports[c["id"]].students_missing for c in reported),
        "unreported_students": sum(int(c.get("capacity") or 0) for c in unreported),
    }


@tool(
    name="report_classroom_status",
    description="""\
Record a TEACHER's accountability report for their classroom during a crisis — \
headcounts only, never student names. Use this whenever a teacher reports their \
class (e.g. "Room 104, 23 of 25 safe, 2 missing"). This is how schools account \
for students in a lockdown: the classroom is the unit, the teacher is the reporter.
""",
    input_schema={
        "type": "object",
        "properties": {
            "room_id": {"type": "string", "description": "The classroom/room id (e.g., 104)."},
            "students_safe": {"type": "integer", "description": "Number of students accounted for as safe."},
            "students_missing": {"type": "integer", "description": "Number unaccounted for (default 0)."},
            "note": {"type": "string", "description": "Optional note (e.g., where missing students were last seen)."},
            "crisis_id": {"type": "string", "description": "Incident ID (optional; uses the active crisis in this channel)."},
        },
        "required": ["room_id", "students_safe"],
    },
)
async def report_classroom_status_tool(args):
    deps = agent_deps_var.get()
    crisis = _active_crisis(deps, args.get("crisis_id"))
    if not crisis:
        return _text("No active crisis to report to. Start one with `/crisis start` first.")

    room_id = str(args["room_id"]).strip()
    safe = int(args.get("students_safe", 0))
    missing = int(args.get("students_missing", 0))
    note = (args.get("note") or "").strip()

    room = knowledge_base.get_room(room_id)
    report = crisis_manager.report_classroom(crisis.id, room_id, safe, missing, note, deps.user_id)
    if not report:
        return _text("Could not record the report — the crisis is not active.")

    room_name = room["name"] if room else f"Room {room_id}"
    teacher = _teacher(room)
    b = _board(crisis)
    line = f":school: *{room_name}*" + (f" ({teacher})" if teacher else "") + f": *{safe} safe*"
    if missing:
        line += f", :red_circle: *{missing} MISSING*"
    if note:
        line += f" — {note}"
    line += (
        f"\n\n_Accountability: {len(b['reported'])}/{len(b['classrooms'])} classrooms reported · "
        f"{b['safe']} students safe · {b['missing']} missing · "
        f"{len(b['unreported'])} rooms not yet reporting (~{b['unreported_students']} students)_"
    )
    return _text(line)


@tool(
    name="get_classroom_accountability",
    description="""\
Show the classroom accountability board for an active crisis: which classrooms \
reported all-safe, which have MISSING students, and which have NOT reported yet, \
with totals. Use when the IC asks "who's unaccounted?" or "what's our headcount?" \
Optionally scope to a zone (e.g., the threat area).
""",
    input_schema={
        "type": "object",
        "properties": {
            "zone_id": {"type": "string", "description": "Limit to a zone's classrooms (optional; default all)."},
            "crisis_id": {"type": "string", "description": "Incident ID (optional; uses the active crisis in this channel)."},
        },
    },
)
async def get_classroom_accountability_tool(args):
    deps = agent_deps_var.get()
    crisis = _active_crisis(deps, args.get("crisis_id"))
    if not crisis:
        return _text("No active crisis. Start one with `/crisis start` first.")

    b = _board(crisis, zone_id=args.get("zone_id"))
    if not b["classrooms"]:
        return _text("No classrooms found for this scope. Upload `rooms.csv` to enable classroom accountability.")

    reports = crisis.classroom_reports
    lines = [
        f"*:clipboard: CLASSROOM ACCOUNTABILITY — {len(b['reported'])}/{len(b['classrooms'])} rooms reported*\n"
    ]
    # sort: rooms with missing first, then unreported, then all-safe
    def _key(c):
        r = reports.get(c["id"])
        if r and r.students_missing:
            return (0, c["id"])
        if not r:
            return (1, c["id"])
        return (2, c["id"])

    for c in sorted(b["classrooms"], key=_key):
        room_name, teacher = c["name"], _teacher(c)
        label = f"{room_name}" + (f" ({teacher})" if teacher else "")
        r = reports.get(c["id"])
        if r and r.students_missing:
            lines.append(f":red_circle: *{label}: {r.students_safe}/{r.total} — {r.students_missing} MISSING*" + (f" — {r.note}" if r.note else ""))
        elif r:
            lines.append(f":white_check_mark: {label}: {r.students_safe}/{r.total} safe")
        else:
            lines.append(f":black_circle: {label}: *NO REPORT* (~{int(c.get('capacity') or 0)} students)")

    lines.append(
        f"\n*{b['safe']} students safe · {b['missing']} MISSING · "
        f"~{b['unreported_students']} unreported ({len(b['unreported'])} rooms)*"
    )
    if b["missing"] or b["unreported"]:
        lines.append("_Chase the red/⚫ rooms first — call the teacher's phone (`lookup_person`)._")
    return _text("\n".join(lines))
