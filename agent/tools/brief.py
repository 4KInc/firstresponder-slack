"""Law-enforcement / first-responder handoff brief - one crisp tactical status.

When police, fire, or EMS arrive on scene, the incident commander needs a single
scannable brief, not a scroll: the threat, how many people are in the building,
who is unaccounted, who needs assisted rescue, which entrances to avoid vs use,
hazards, medical on site, and who is in charge.
"""

from claude_agent_sdk import tool

from agent.context import agent_deps_var
from crisis import crisis_manager
from crisis.knowledge import knowledge_base
from crisis.models import CRISIS_TYPES


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


@tool(
    name="law_enforcement_brief",
    description="""\
Generate a CRISP tactical handoff brief for arriving law enforcement, fire, or \
EMS: the threat, headcount in the building, who is unaccounted, people needing \
assisted rescue, which entrances to AVOID vs use, hazards, medical on site, and \
the incident commander's contact. Use the moment responders arrive on scene, or \
when someone asks for a brief/status for police. Pass the threat zone if known.
""",
    input_schema={
        "type": "object",
        "properties": {
            "zone_id": {"type": "string", "description": "Threat location/zone (e.g., east-wing), if known."},
            "crisis_id": {"type": "string", "description": "Incident ID (optional; uses the active crisis in this channel)."},
        },
    },
)
async def law_enforcement_brief_tool(args):
    deps = agent_deps_var.get()
    crisis = _active_crisis(deps, args.get("crisis_id"))
    if not crisis:
        return _text("No active crisis to brief on. Start one with `/crisis start` first.")

    zone = args.get("zone_id")
    info = CRISIS_TYPES.get(crisis.crisis_type, CRISIS_TYPES["other"])

    staff = knowledge_base.get_personnel_in_zone(zone_id=zone)
    occ = knowledge_base.get_zone_occupancy(zone_id=zone)
    reports = crisis.classroom_reports

    lines = [
        f":police_car: *LAW ENFORCEMENT BRIEF - {crisis.id}* ({info['label'].upper()})",
        f"Elapsed: *{crisis.duration_minutes} min* | IC: " + (f"<@{crisis.incident_commander}>" if crisis.incident_commander else "*UNASSIGNED*"),
        f"\n*THREAT:* {crisis.description}" + (f" | Zone: *{zone}*" if zone else ""),
    ]

    total = len(staff) + occ["estimated_students"]
    lines.append(
        f"*IN BUILDING:* ~{total} in the danger zone - {len(staff)} staff, "
        f"~{occ['estimated_students']} students ({occ['classroom_count']} classrooms), in lockdown"
    )

    # Accountability
    safe_students = sum(r.students_safe for r in reports.values())
    missing = [(rid, r) for rid, r in reports.items() if r.students_missing]
    lines.append("\n*ACCOUNTABILITY:*")
    lines.append(f"- Reported safe: *{safe_students}* students across {len([r for r in reports.values() if not r.students_missing])} rooms")
    for rid, r in missing:
        room = knowledge_base.get_room(rid)
        rn = room["name"] if room else f"Room {rid}"
        lines.append(f"- :red_circle: *{r.students_missing} UNACCOUNTED - {rn}*" + (f" ({r.note})" if r.note else ""))
    unreported = occ["classroom_count"] - len(reports)
    if unreported > 0:
        lines.append(f"- {unreported} classrooms not yet reporting")

    # People who cannot self-evacuate
    mobility = [p for p in staff if p.get("mobility_limitations")]
    if mobility:
        lines.append("\n*NEED ASSISTED RESCUE:*")
        for p in mobility:
            note = p.get("medical_notes") or "mobility limited"
            lines.append(f"- {p['name']} - Rm {p.get('default_location', '?')} - {p.get('phone', '')} - {note}")

    # Approach: which doors to avoid vs use
    guidance = knowledge_base.get_evacuation_guidance(threat_location=zone or "")
    blocked = guidance.get("blocked_routes", [])
    safe = guidance.get("safe_routes", [])
    lines.append("\n*APPROACH:*")
    for exit_name in dict.fromkeys(r["to_exit"] for r in blocked):  # dedup, keep order
        lines.append(f"- :no_entry: AVOID {exit_name} - passes through the threat")
    if safe:
        exits = ", ".join(dict.fromkeys(r["to_exit"] for r in safe))  # dedup, keep order
        lines.append(f"- Civilians evacuating via: {exits[:200]}")

    # Hazards
    hazmat = knowledge_base.get_hazmat_near_threat(zone_id=zone)
    if hazmat:
        lines.append("\n*HAZARDS:*")
        for h in hazmat[:4]:
            lines.append(f"- {h['material_name']} ({h['hazard_class']}) - {h['location_description']}")

    # Medical on site
    medics = [p for p in staff if p.get("trained_first_aid") or p.get("trained_cpr")]
    if medics:
        lines.append("\n*MEDICAL ON SITE:* " + ", ".join(f"{m['name']} (Rm {m.get('default_location', '?')})" for m in medics[:6]))

    lines.append("\n_Call 911 / follow on-scene command. This brief supports responders, it does not replace them._")
    return _text("\n".join(lines))
