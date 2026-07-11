"""Knowledge-aware tools — the agent queries organizational context during crises.

These tools give the agent access to building layouts, personnel info, resource locations,
network topology, and drill history. This is what makes FirstResponder context-aware
instead of generic.
"""

import json

from claude_agent_sdk import tool

from agent.context import agent_deps_var
from agent.tools._people import person_label
from crisis.knowledge import knowledge_base


@tool(
    name="get_evacuation_guidance",
    description="""\
Get context-aware evacuation guidance based on the threat location. Returns:
- Safe evacuation routes (avoiding the threat zone)
- Blocked routes (passing through the threat zone)
- Personnel with mobility limitations who need elevator/assistance
- Floor wardens responsible for sweeping their zones

Use this IMMEDIATELY when a physical crisis starts (fire, active threat, earthquake, flood). \
The threat_location should match a zone ID from the facility setup.
""",
    input_schema={
        "type": "object",
        "properties": {
            "threat_location": {
                "type": "string",
                "description": "Zone or area where the threat is located (e.g., 'east-wing', 'floor-2', 'server-room')",
            },
            "floor": {
                "type": "integer",
                "description": "Floor number to focus on (optional)",
            },
        },
    },
)
async def get_evacuation_guidance_tool(args):
    threat_location = args.get("threat_location", "")
    floor = args.get("floor")

    guidance = knowledge_base.get_evacuation_guidance(threat_location, floor)

    if not guidance["zones"] and not guidance["safe_routes"]:
        return {"content": [{"type": "text", "text": "No facility data loaded. Use /crisis setup to configure your building layout."}]}

    lines = ["*Evacuation Guidance*\n"]

    if threat_location:
        lines.append(f"Threat location: *{threat_location}*\n")

    if guidance["safe_routes"]:
        lines.append("*Safe Routes:*")
        for route in guidance["safe_routes"]:
            lines.append(f"- {route['name']}: {route['route_description']} -> Exit: {route['to_exit']}")
            if route.get("accessibility") != "standard":
                lines.append(f"  Accessibility: {route['accessibility']}")

    if guidance["blocked_routes"]:
        lines.append("\n*BLOCKED Routes (pass through threat zone):*")
        for route in guidance["blocked_routes"]:
            lines.append(f"- DO NOT USE: {route['name']} ({route['route_description']})")

    if guidance["mobility_limited_personnel"]:
        lines.append(f"\n*Personnel Requiring Assistance ({len(guidance['mobility_limited_personnel'])}):*")
        for p in guidance["mobility_limited_personnel"]:
            lines.append(f"- {p['name']} — Location: {p['default_location']}, Floor {p['floor']}")

    if guidance["floor_wardens"]:
        lines.append(f"\n*Floor Wardens:*")
        for w in guidance["floor_wardens"]:
            uid = person_label(w.get("slack_user_id"), w.get("name"))
            lines.append(f"- {uid} — {w['default_location']}, Floor {w['floor']}")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


@tool(
    name="find_emergency_resources",
    description="""\
Find nearby emergency resources — AEDs, fire extinguishers, first aid kits, \
emergency exits, trauma kits, etc. Use this during medical emergencies, fires, \
or any situation where physical resources are needed.
""",
    input_schema={
        "type": "object",
        "properties": {
            "resource_type": {
                "type": "string",
                "description": "Type of resource to find",
                "enum": ["aed", "fire_extinguisher", "first_aid_kit", "trauma_kit",
                         "emergency_exit", "fire_alarm", "emergency_phone", "shelter",
                         "eyewash_station", "spill_kit"],
            },
            "floor": {
                "type": "integer",
                "description": "Floor number to search on (optional)",
            },
        },
    },
)
async def find_emergency_resources_tool(args):
    resource_type = args.get("resource_type")
    floor = args.get("floor")

    resources = knowledge_base.get_nearby_resources(resource_type=resource_type, floor=floor)

    if not resources:
        msg = "No emergency resources found"
        if resource_type:
            msg += f" of type '{resource_type}'"
        if floor:
            msg += f" on floor {floor}"
        msg += ". Facility resource data may not be configured."
        return {"content": [{"type": "text", "text": msg}]}

    lines = [f"*Emergency Resources Found ({len(resources)}):*\n"]
    for r in resources:
        lines.append(f"- *{r['resource_type'].upper()}*: {r['location_description']} (Floor {r['floor']})")
        if r.get("notes"):
            lines.append(f"  Note: {r['notes']}")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


@tool(
    name="lookup_person",
    description="""\
Look up a person's details — location, emergency contacts, medical notes, training. \
Use this when someone hasn't checked in to find their likely location, or during \
a medical emergency to check for relevant medical conditions. Also useful for finding \
who is trained in first aid/CPR near a medical emergency.
""",
    input_schema={
        "type": "object",
        "properties": {
            "slack_user_id": {
                "type": "string",
                "description": "The Slack user ID to look up (e.g., U01ABCDEF)",
            },
        },
        "required": ["slack_user_id"],
    },
)
async def lookup_person_tool(args):
    slack_user_id = args["slack_user_id"]
    person = knowledge_base.get_personnel_by_slack_id(slack_user_id)

    if not person:
        return {"content": [{"type": "text", "text": f"No personnel record found for {person_label(slack_user_id)}. They may not be in the directory."}]}

    lines = [
        f"*Personnel Record: {person['name']}*\n",
        f"- Role: {person.get('role', 'N/A')}",
        f"- Department: {person.get('department', 'N/A')}",
        f"- Default Location: {person.get('default_location', 'N/A')} (Floor {person.get('floor', '?')})",
        f"- Phone: {person.get('phone', 'N/A')}",
    ]

    if person.get("emergency_contact_name"):
        lines.append(f"- Emergency Contact: {person['emergency_contact_name']} — {person.get('emergency_contact_phone', 'N/A')}")

    flags = []
    if person.get("mobility_limitations"):
        flags.append("MOBILITY LIMITED — needs elevator/assistance for evacuation")
    if person.get("trained_first_aid"):
        flags.append("First Aid trained")
    if person.get("trained_cpr"):
        flags.append("CPR trained")
    if person.get("is_floor_warden"):
        flags.append("Floor Warden")
    if person.get("evacuation_role"):
        flags.append(f"Evacuation role: {person['evacuation_role']}")

    if flags:
        lines.append(f"\n*Flags:*")
        for f in flags:
            lines.append(f"- {f}")

    if person.get("medical_notes"):
        lines.append(f"\n*Medical Notes:* {person['medical_notes']}")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


@tool(
    name="find_first_aid_responders",
    description="""\
Find all personnel trained in first aid and/or CPR with their locations. \
Use this during medical emergencies to dispatch the nearest trained person. \
Also identifies AED-trained personnel.
""",
    input_schema={
        "type": "object",
        "properties": {},
    },
)
async def find_first_aid_responders_tool(args):
    trained = knowledge_base.get_first_aid_trained()

    if not trained:
        return {"content": [{"type": "text", "text": "No first aid/CPR trained personnel in the directory. Consider adding training records."}]}

    lines = [f"*First Aid / CPR Trained Personnel ({len(trained)}):*\n"]
    for p in trained:
        certs = []
        if p.get("trained_first_aid"):
            certs.append("First Aid")
        if p.get("trained_cpr"):
            certs.append("CPR/AED")

        uid = person_label(p.get("slack_user_id"), p.get("name"))
        lines.append(f"- {uid} — {', '.join(certs)} — Location: {p.get('default_location', '?')}, Floor {p.get('floor', '?')}")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


@tool(
    name="get_blast_radius",
    description="""\
For cyber incidents: determine the blast radius of a compromised system. \
Shows all systems that depend on the affected asset, their criticality, and owners. \
Use this when a server, database, or service is compromised to understand \
what else might be affected and who to notify.
""",
    input_schema={
        "type": "object",
        "properties": {
            "asset_id": {
                "type": "string",
                "description": "The ID of the compromised asset (e.g., 'prod-db', 'auth-server')",
            },
        },
        "required": ["asset_id"],
    },
)
async def get_blast_radius_tool(args):
    asset_id = args["asset_id"]
    affected = knowledge_base.get_affected_systems(asset_id)

    if not affected:
        return {"content": [{"type": "text", "text": f"No downstream dependencies found for '{asset_id}'. Asset may not be in the inventory."}]}

    lines = [f"*Blast Radius for `{asset_id}` ({len(affected)} dependent systems):*\n"]
    for a in affected:
        lines.append(
            f"- *{a['name']}* (`{a['id']}`) — {a['asset_type']} | "
            f"Criticality: {a.get('criticality', 'unknown').upper()} | "
            f"Owner: {a.get('owner', 'unknown')}"
        )
        if a.get("ip_address"):
            lines.append(f"  IP: {a['ip_address']}")

    lines.append(f"\n*Action:* Isolate `{asset_id}` AND assess each dependent system for compromise.")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


@tool(
    name="get_vendor_contacts",
    description="""\
Look up vendor emergency contacts for a specific service. Use this during outages \
or incidents that involve third-party services (AWS, Stripe, hosting providers, etc.). \
Returns contact info, escalation procedures, and SLA details.
""",
    input_schema={
        "type": "object",
        "properties": {
            "service": {
                "type": "string",
                "description": "The service or vendor to look up (e.g., 'AWS', 'Stripe', 'hosting', 'database')",
            },
        },
        "required": ["service"],
    },
)
async def get_vendor_contacts_tool(args):
    service = args["service"]
    vendors = knowledge_base.get_vendor_for_service(service)

    if not vendors:
        return {"content": [{"type": "text", "text": f"No vendor contacts found for '{service}'."}]}

    lines = [f"*Vendor Contacts for '{service}':*\n"]
    for v in vendors:
        lines.append(f"*{v['vendor_name']}* — {v['service']}")
        if v.get("contact_name"):
            lines.append(f"- Contact: {v['contact_name']}")
        if v.get("contact_phone"):
            lines.append(f"- Phone: {v['contact_phone']}")
        if v.get("contact_email"):
            lines.append(f"- Email: {v['contact_email']}")
        if v.get("sla_hours"):
            lines.append(f"- SLA: {v['sla_hours']} hours")
        if v.get("escalation_procedure"):
            lines.append(f"- Escalation: {v['escalation_procedure']}")
        lines.append("")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


@tool(
    name="get_drill_performance",
    description="""\
Get past drill performance data to benchmark current crisis response. \
Shows evacuation times, accountability times, and issues from past drills. \
Use this to set expectations: "Last fire drill took 4:32 — we should beat that."
""",
    input_schema={
        "type": "object",
        "properties": {
            "drill_type": {
                "type": "string",
                "description": "Type of drill to look up (e.g., 'fire', 'active-threat', 'earthquake'). Omit for all types.",
            },
        },
    },
)
async def get_drill_performance_tool(args):
    drill_type = args.get("drill_type")
    drills = knowledge_base.get_drill_performance(drill_type)

    if not drills:
        msg = "No drill history recorded"
        if drill_type:
            msg += f" for '{drill_type}'"
        return {"content": [{"type": "text", "text": msg + "."}]}

    lines = ["*Past Drill Performance:*\n"]
    for d in drills:
        evac_time = f"{d['total_evacuation_seconds'] // 60}:{d['total_evacuation_seconds'] % 60:02d}"
        lines.append(
            f"- *{d['drill_type'].title()}* ({d['date']}) — "
            f"Evacuation: {evac_time} | Participants: {d.get('participants', '?')}"
        )
        if d.get("slowest_zone"):
            lines.append(f"  Slowest zone: {d['slowest_zone']}")
        if d.get("issues_noted"):
            lines.append(f"  Issues: {d['issues_noted']}")

    # Calculate averages
    times = [d["total_evacuation_seconds"] for d in drills]
    avg = sum(times) / len(times)
    lines.append(f"\n*Average evacuation time:* {avg // 60:.0f}:{avg % 60:02.0f}")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


@tool(
    name="get_knowledge_summary",
    description="""\
Get a summary of all organizational knowledge loaded into FirstResponder. \
Shows how much context the system has about your facilities, people, resources, \
and infrastructure. Use this to check if the system is properly configured.
""",
    input_schema={
        "type": "object",
        "properties": {},
    },
)
async def get_knowledge_summary_tool(args):
    summary = knowledge_base.get_facility_summary()

    if all(v == 0 for v in summary.values()):
        return {"content": [{"type": "text", "text": (
            "No organizational knowledge loaded yet.\n\n"
            "To make FirstResponder context-aware, configure:\n"
            "- Building layout (facilities, zones, rooms)\n"
            "- Personnel directory (locations, emergency contacts, training)\n"
            "- Emergency resources (AEDs, fire extinguishers, first aid kits)\n"
            "- Network assets (for cyber incident blast radius)\n"
            "- Vendor contacts (for outage escalation)\n"
            "- Evacuation routes (with accessibility info)\n\n"
            "The more context I have, the better I can coordinate your response."
        )}]}

    lines = [
        "*Organizational Knowledge Base:*\n",
        f"- Facilities: {summary['facilities']}",
        f"- Zones: {summary['zones']}",
        f"- Rooms: {summary['rooms']}",
        f"- Personnel: {summary['personnel']}",
        f"  - First Aid trained: {summary['first_aid_trained']}",
        f"  - CPR trained: {summary['cpr_trained']}",
        f"  - Mobility limited: {summary['mobility_limited']}",
        f"  - Floor Wardens: {summary['floor_wardens']}",
        f"- Emergency Resources: {summary['emergency_resources']}",
        f"- Network Assets: {summary['network_assets']}",
        f"- Vendor Contacts: {summary['vendor_contacts']}",
        f"- Evacuation Routes: {summary['evacuation_routes']}",
        f"- Drills Recorded: {summary['drills_recorded']}",
    ]

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}
