"""Cyber incident tools — cyberattack, data breach, outage.

These tools query network topology, data inventory, runbooks, on-call schedules,
and business continuity plans for infrastructure-aware incident response.
"""

import json

from claude_agent_sdk import tool

from crisis.knowledge import knowledge_base


@tool(
    name="get_data_at_risk",
    description="""\
Identify what sensitive data lives on a compromised system. Returns data classification, \
PII fields, record counts, regulatory frameworks (GDPR, HIPAA, PCI-DSS), and breach \
notification requirements. Use this IMMEDIATELY during data breaches to understand \
scope and trigger the right notification timelines.

Example: if 'donor-db' is breached, this tells you "50,000 donor records with names, \
emails, credit cards — PCI-DSS applies, 72-hour notification required."
""",
    input_schema={
        "type": "object",
        "properties": {
            "storage_system": {
                "type": "string",
                "description": "The compromised system name (e.g., 'donor-db', 'file-server', 'crm')",
            },
        },
        "required": ["storage_system"],
    },
)
async def get_data_at_risk_tool(args):
    data = knowledge_base.get_data_at_risk(args["storage_system"])

    if not data:
        return {"content": [{"type": "text", "text": f"No data inventory records for system '{args['storage_system']}'."}]}

    lines = [f"*Data at Risk on `{args['storage_system']}` ({len(data)} datasets):*\n"]
    for d in data:
        lines.append(f"*{d['name']}*")
        lines.append(f"- Classification: *{d['data_classification'].upper()}*")
        lines.append(f"- Storage: {d['storage_system']}")
        if d.get("record_count"):
            lines.append(f"- Records: {d['record_count']}")

        pii = json.loads(d.get("pii_fields", "[]"))
        if pii:
            lines.append(f"- PII fields: {', '.join(pii)}")

        regs = json.loads(d.get("regulatory_frameworks", "[]"))
        if regs:
            lines.append(f"- Regulatory: {', '.join(regs)}")

        if d.get("notification_requirements"):
            lines.append(f"- NOTIFICATION: {d['notification_requirements']}")

        if d.get("backup_location"):
            lines.append(f"- Backup: {d['backup_location']} (frequency: {d.get('backup_frequency', '?')})")

        if d.get("data_owner"):
            lines.append(f"- Owner: {d['data_owner']}")

        lines.append("")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


@tool(
    name="get_runbook",
    description="""\
Find step-by-step recovery procedures (runbooks) for a specific scenario or system. \
Runbooks contain tested procedures with estimated resolution times. Use this during \
outages and cyber incidents to follow proven recovery steps instead of improvising.

Search by scenario type (e.g., 'ransomware', 'database-failure') or by system \
name (e.g., 'stripe', 'auth-server', 'postgresql').
""",
    input_schema={
        "type": "object",
        "properties": {
            "scenario_type": {
                "type": "string",
                "description": "Type of scenario (e.g., 'ransomware', 'ddos', 'database-failure', 'outage')",
            },
            "system": {
                "type": "string",
                "description": "Specific system or service name (e.g., 'postgresql', 'stripe', 'nginx')",
            },
        },
    },
)
async def get_runbook_tool(args):
    runbooks = knowledge_base.get_runbook(
        scenario_type=args.get("scenario_type"),
        system=args.get("system"),
    )

    if not runbooks:
        return {"content": [{"type": "text", "text": "No runbooks found. Recovery procedures may not be documented."}]}

    lines = [f"*Runbooks Found ({len(runbooks)}):*\n"]
    for rb in runbooks:
        lines.append(f"*{rb['title']}*")
        lines.append(f"- Scenario: {rb['scenario_type']} | System: {rb.get('system_or_service', 'general')}")
        lines.append(f"- Severity: {rb.get('severity', '?').upper()}")
        if rb.get("estimated_minutes"):
            lines.append(f"- Estimated time: {rb['estimated_minutes']} minutes")
        if rb.get("last_tested"):
            lines.append(f"- Last tested: {rb['last_tested']}")
        if rb.get("owner"):
            lines.append(f"- Owner: {rb['owner']}")

        steps = json.loads(rb.get("steps", "[]"))
        if steps:
            lines.append(f"- Steps:")
            for i, step in enumerate(steps, 1):
                lines.append(f"  {i}. {step}")

        lines.append("")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


@tool(
    name="get_on_call",
    description="""\
Find who is currently on-call for a service or system. Returns primary and secondary \
contacts with phone numbers. Use this during outages and cyber incidents to page \
the right people immediately. Also shows escalation path to management.
""",
    input_schema={
        "type": "object",
        "properties": {
            "service": {
                "type": "string",
                "description": "Service or system to find on-call for (e.g., 'database', 'network', 'security', 'payments')",
            },
        },
    },
)
async def get_on_call_tool(args):
    schedules = knowledge_base.get_on_call(args.get("service"))

    if not schedules:
        return {"content": [{"type": "text", "text": "No on-call schedules configured."}]}

    lines = [f"*On-Call Contacts ({len(schedules)}):*\n"]
    for s in schedules:
        lines.append(f"*{s['team_name']}* — {s['service']}")

        primary_uid = f"<@{s['primary_slack_id']}>" if s.get("primary_slack_id") else s["primary_name"]
        lines.append(f"- Primary: {primary_uid}")
        if s.get("primary_phone"):
            lines.append(f"  Phone: {s['primary_phone']}")

        if s.get("secondary_name"):
            secondary_uid = f"<@{s['secondary_slack_id']}>" if s.get("secondary_slack_id") else s["secondary_name"]
            lines.append(f"- Secondary: {secondary_uid}")
            if s.get("secondary_phone"):
                lines.append(f"  Phone: {s['secondary_phone']}")

        if s.get("escalation_manager"):
            lines.append(f"- Escalation: {s['escalation_manager']}")
            if s.get("escalation_phone"):
                lines.append(f"  Phone: {s['escalation_phone']}")

        lines.append("")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


@tool(
    name="get_continuity_plan",
    description="""\
Get the business continuity plan for a scenario — what to do when normal operations \
are disrupted. Shows trigger conditions, required actions, whether remote work is \
possible, backup facilities, critical functions, and recovery time objectives. \
Use during extended outages, severe weather, or any event that threatens normal operations.
""",
    input_schema={
        "type": "object",
        "properties": {
            "scenario_type": {
                "type": "string",
                "description": "Scenario type (e.g., 'weather', 'outage', 'flood', 'earthquake', 'cyberattack')",
            },
        },
        "required": ["scenario_type"],
    },
)
async def get_continuity_plan_tool(args):
    plans = knowledge_base.get_continuity_plan(args["scenario_type"])

    if not plans:
        return {"content": [{"type": "text", "text": f"No continuity plan configured for '{args['scenario_type']}'."}]}

    lines = [f"*Business Continuity Plans ({len(plans)}):*\n"]
    for p in plans:
        lines.append(f"*{p['plan_name']}*")

        if p.get("trigger_conditions"):
            lines.append(f"- Trigger: {p['trigger_conditions']}")

        if p.get("recovery_time_objective_hours"):
            lines.append(f"- Recovery Time Objective: {p['recovery_time_objective_hours']} hours")

        lines.append(f"- Remote work capable: {'Yes' if p.get('remote_work_capable') else 'No'}")

        if p.get("backup_facility"):
            lines.append(f"- Backup facility: {p['backup_facility']}")

        critical = json.loads(p.get("critical_functions", "[]"))
        if critical:
            lines.append(f"- Critical functions to maintain:")
            for func in critical:
                lines.append(f"  - {func}")

        actions = json.loads(p.get("actions", "[]"))
        if actions:
            lines.append(f"- Required actions:")
            for i, action in enumerate(actions, 1):
                lines.append(f"  {i}. {action}")

        lines.append("")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}
