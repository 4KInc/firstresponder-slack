"""Physical safety tools — fire, earthquake, flood, weather, active threat, medical.

These tools query facility-specific data: utility shutoffs, assembly points,
hazmat locations, nearby hospitals, and personnel in danger zones.
"""

import json

from claude_agent_sdk import tool

from crisis.knowledge import knowledge_base


@tool(
    name="get_utility_controls",
    description="""\
Find utility shutoff locations — gas valves, electrical panels, water mains, HVAC controls. \
Critical during fires (shut gas to prevent explosion), floods (shut electrical to prevent \
electrocution), gas leaks (shut gas main), and earthquakes (shut all utilities after shaking stops). \
Always tell responders if a shutoff requires a key and where the key is.
""",
    input_schema={
        "type": "object",
        "properties": {
            "utility_type": {
                "type": "string",
                "description": "Type of utility to find",
                "enum": ["gas", "electrical", "water", "hvac", "sprinkler", "fire_suppression"],
            },
            "zone_id": {
                "type": "string",
                "description": "Zone to search in (optional)",
            },
            "floor": {
                "type": "integer",
                "description": "Floor number (optional)",
            },
        },
    },
)
async def get_utility_controls_tool(args):
    controls = knowledge_base.get_utility_controls(
        utility_type=args.get("utility_type"),
        zone_id=args.get("zone_id"),
        floor=args.get("floor"),
    )

    if not controls:
        return {"content": [{"type": "text", "text": "No utility controls found. Facility data may not be configured."}]}

    lines = [f"*Utility Controls ({len(controls)}):*\n"]
    for c in controls:
        lines.append(f"- *{c['utility_type'].upper()}*: {c['location_description']} (Floor {c.get('floor', '?')})")
        if c.get("shutoff_instructions"):
            lines.append(f"  Instructions: {c['shutoff_instructions']}")
        if c.get("requires_key"):
            lines.append(f"  KEY REQUIRED — Key location: {c.get('key_location', 'unknown')}")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


@tool(
    name="get_assembly_points",
    description="""\
Get designated assembly/rally points for evacuation accountability. Shows primary \
and alternate points with capacity. Use this after ordering an evacuation to tell \
people WHERE to go and ensure headcounts happen at the right locations.
""",
    input_schema={
        "type": "object",
        "properties": {
            "facility_id": {
                "type": "string",
                "description": "Facility ID (optional, returns all if omitted)",
            },
        },
    },
)
async def get_assembly_points_tool(args):
    points = knowledge_base.get_assembly_points(args.get("facility_id"))

    if not points:
        return {"content": [{"type": "text", "text": "No assembly points configured."}]}

    lines = ["*Assembly / Rally Points:*\n"]
    for p in points:
        prefix = "PRIMARY" if p.get("is_primary") else "ALTERNATE"
        lines.append(f"- *[{prefix}] {p['name']}*: {p['location_description']}")
        if p.get("capacity"):
            lines.append(f"  Capacity: {p['capacity']} people")
        if p.get("accessibility") and p["accessibility"] != "standard":
            lines.append(f"  Accessibility: {p['accessibility']}")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


@tool(
    name="get_hazmat_info",
    description="""\
Find hazardous materials near a threat zone. Critical during fires (chemicals may \
explode or produce toxic fumes), earthquakes (containers may rupture), and floods \
(chemicals may contaminate water). Returns material name, hazard class, quantity, \
and containment instructions. ALWAYS check for hazmat when fire is near labs, \
maintenance areas, kitchens, or industrial zones.
""",
    input_schema={
        "type": "object",
        "properties": {
            "zone_id": {
                "type": "string",
                "description": "Zone where the threat/fire is located",
            },
            "floor": {
                "type": "integer",
                "description": "Floor number to check",
            },
        },
    },
)
async def get_hazmat_info_tool(args):
    materials = knowledge_base.get_hazmat_near_threat(
        zone_id=args.get("zone_id"),
        floor=args.get("floor"),
    )

    if not materials:
        return {"content": [{"type": "text", "text": "No hazardous materials registered in this area."}]}

    lines = [f"*HAZARDOUS MATERIALS IN AREA ({len(materials)}):*\n"]
    for m in materials:
        lines.append(f"- *{m['material_name']}* — Hazard class: {m['hazard_class']}")
        lines.append(f"  Location: {m['location_description']} (Floor {m.get('floor', '?')})")
        if m.get("quantity"):
            lines.append(f"  Quantity: {m['quantity']}")
        if m.get("containment_instructions"):
            lines.append(f"  Containment: {m['containment_instructions']}")
        if m.get("sds_location"):
            lines.append(f"  Safety Data Sheet: {m['sds_location']}")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


@tool(
    name="get_nearest_emergency_services",
    description="""\
Find nearest hospitals, fire stations, police stations with ETA. Use during any \
crisis to coordinate with external emergency services. For medical emergencies, \
shows trauma center levels and helipad availability. Always provide this info \
when calling 911 so dispatch can route to the right facility.
""",
    input_schema={
        "type": "object",
        "properties": {
            "service_type": {
                "type": "string",
                "description": "Type of service to find",
                "enum": ["hospital", "fire_station", "police_station", "trauma_center", "urgent_care", "poison_control"],
            },
        },
    },
)
async def get_nearest_emergency_services_tool(args):
    services = knowledge_base.get_nearby_emergency_services(args.get("service_type"))

    if not services:
        return {"content": [{"type": "text", "text": "No nearby emergency services configured."}]}

    lines = [f"*Nearest Emergency Services ({len(services)}):*\n"]
    for s in services:
        lines.append(f"- *{s['name']}* ({s['service_type']})")
        if s.get("address"):
            lines.append(f"  Address: {s['address']}")
        if s.get("phone"):
            lines.append(f"  Phone: {s['phone']}")
        if s.get("distance_miles"):
            lines.append(f"  Distance: {s['distance_miles']} miles")
        if s.get("eta_minutes"):
            lines.append(f"  ETA: ~{s['eta_minutes']} minutes")
        if s.get("trauma_level"):
            lines.append(f"  Trauma Level: {s['trauma_level']}")
        if s.get("helipad"):
            lines.append(f"  Helipad: Yes")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


@tool(
    name="get_people_in_danger_zone",
    description="""\
Find all personnel whose default location is in or near a threat zone. \
Use this immediately when a physical threat is reported to identify who \
might be in danger. Returns names, locations, phone numbers, and any \
special needs (mobility limitations, medical conditions).
""",
    input_schema={
        "type": "object",
        "properties": {
            "zone_id": {
                "type": "string",
                "description": "Zone where the threat is",
            },
            "floor": {
                "type": "integer",
                "description": "Floor where the threat is",
            },
        },
    },
)
async def get_people_in_danger_zone_tool(args):
    people = knowledge_base.get_personnel_in_zone(
        zone_id=args.get("zone_id"),
        floor=args.get("floor"),
    )

    if not people:
        return {"content": [{"type": "text", "text": "No personnel records for this zone/floor."}]}

    lines = [f"*Personnel in Danger Zone ({len(people)}):*\n"]

    # Sort: mobility limited first (highest priority)
    people.sort(key=lambda p: (-p.get("mobility_limitations", 0), p.get("name", "")))

    for p in people:
        uid = f"<@{p['slack_user_id']}>" if p.get("slack_user_id") else p["name"]
        lines.append(f"- {uid} — {p.get('role', 'N/A')} — Location: {p.get('default_location', '?')}")
        if p.get("phone"):
            lines.append(f"  Phone: {p['phone']}")

        flags = []
        if p.get("mobility_limitations"):
            flags.append("MOBILITY LIMITED")
        if p.get("medical_notes"):
            flags.append(f"Medical: {p['medical_notes']}")
        if p.get("trained_first_aid"):
            flags.append("First Aid trained")
        if p.get("trained_cpr"):
            flags.append("CPR trained")
        if flags:
            lines.append(f"  Flags: {' | '.join(flags)}")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}
