PLAYBOOKS = {
    "earthquake": {
        "title": "Earthquake Response Playbook",
        "immediate_actions": [
            "Drop, Cover, Hold On - do not evacuate during shaking",
            "Once shaking stops: check for injuries, assess structural damage",
            "Evacuate if building damage is visible - use stairs, not elevators",
            "Move to designated assembly point",
            "Account for all personnel - check in with your team lead",
        ],
        "roles": [
            {"role": "Incident Commander", "responsibilities": "Overall coordination, communication with emergency services"},
            {"role": "Safety Officer", "responsibilities": "Building damage assessment, evacuation decisions"},
            {"role": "Communications Lead", "responsibilities": "Internal updates, external notifications, family contact"},
            {"role": "Medical Lead", "responsibilities": "First aid triage, coordinate with EMS"},
        ],
        "resources_needed": [
            "First aid kits",
            "Emergency radios",
            "Flashlights and batteries",
            "Water and emergency supplies",
            "Building evacuation maps",
        ],
    },
    "fire": {
        "title": "Fire Response Playbook",
        "immediate_actions": [
            "Activate fire alarm if not already triggered",
            "Call 911 / local fire department immediately",
            "Evacuate via nearest safe exit - do NOT use elevators",
            "Close doors behind you to slow fire spread",
            "Assemble at designated rally point for headcount",
        ],
        "roles": [
            {"role": "Incident Commander", "responsibilities": "Coordinate evacuation, liaise with fire department"},
            {"role": "Floor Wardens", "responsibilities": "Sweep assigned areas, confirm all clear"},
            {"role": "Communications Lead", "responsibilities": "Notify all staff, update stakeholders"},
            {"role": "Assembly Point Lead", "responsibilities": "Conduct headcount, report missing persons"},
        ],
        "resources_needed": [
            "Fire extinguishers (know locations)",
            "Evacuation route maps",
            "Emergency contact list",
            "First aid supplies",
            "Megaphone or communication device",
        ],
    },
    "flood": {
        "title": "Flood Response Playbook",
        "immediate_actions": [
            "Monitor weather alerts and water levels",
            "Move to higher ground if water is rising",
            "Disconnect electrical equipment in flood-risk areas",
            "Secure important documents and equipment",
            "Do NOT walk or drive through flood waters",
        ],
        "roles": [
            {"role": "Incident Commander", "responsibilities": "Monitor conditions, evacuation decisions"},
            {"role": "Facilities Lead", "responsibilities": "Sandbags, equipment protection, utility shutoff"},
            {"role": "Communications Lead", "responsibilities": "Weather monitoring, staff notifications"},
            {"role": "Logistics Lead", "responsibilities": "Transportation, temporary relocation coordination"},
        ],
        "resources_needed": [
            "Sandbags and barriers",
            "Water pumps",
            "Waterproof containers for documents",
            "Emergency power supply",
            "Evacuation transportation",
        ],
    },
    "active_threat": {
        "title": "Active Threat Response Playbook",
        "immediate_actions": [
            "RUN: Evacuate if safe path exists - leave belongings behind",
            "HIDE: If evacuation impossible, find secure room, lock/barricade door",
            "FIGHT: Last resort only - act with aggression, improvise weapons",
            "Call 911 when safe to do so - provide location and description",
            "Do NOT pull fire alarm - it causes people to gather in open areas",
        ],
        "roles": [
            {"role": "Incident Commander", "responsibilities": "Coordinate with law enforcement, account for personnel"},
            {"role": "Communications Lead", "responsibilities": "Send lockdown alerts, maintain communication with police"},
            {"role": "Medical Lead", "responsibilities": "Triage injuries once scene is secured"},
            {"role": "Recovery Lead", "responsibilities": "Post-incident support, counseling resources"},
        ],
        "resources_needed": [
            "Lockdown notification system",
            "Room barricade capability",
            "First aid / trauma kits",
            "Law enforcement direct contact numbers",
            "Crisis counseling resources",
        ],
    },
    "cyberattack": {
        "title": "Cyber Attack Response Playbook",
        "immediate_actions": [
            "Identify affected systems and scope of compromise",
            "Isolate compromised systems from the network immediately",
            "Preserve forensic evidence - do NOT reboot affected machines",
            "Activate incident response team communication channel",
            "Notify legal, compliance, and executive leadership",
        ],
        "roles": [
            {"role": "Incident Commander", "responsibilities": "Overall response coordination, stakeholder communication"},
            {"role": "Technical Lead", "responsibilities": "Containment, forensic analysis, system recovery"},
            {"role": "Communications Lead", "responsibilities": "Internal/external notifications, regulatory reporting"},
            {"role": "Legal/Compliance Lead", "responsibilities": "Regulatory obligations, evidence preservation, breach notification"},
        ],
        "resources_needed": [
            "Incident response toolkit (forensic tools, clean media)",
            "Network diagrams and asset inventory",
            "Backup systems and recovery procedures",
            "Legal counsel contact information",
            "Regulatory notification templates",
        ],
    },
    "data_breach": {
        "title": "Data Breach Response Playbook",
        "immediate_actions": [
            "Confirm the breach - identify what data was exposed",
            "Contain the breach - revoke access, patch vulnerability",
            "Document everything - timestamps, affected records, actions taken",
            "Notify legal counsel and compliance team",
            "Begin regulatory breach notification timeline (72h GDPR, varies by jurisdiction)",
        ],
        "roles": [
            {"role": "Incident Commander", "responsibilities": "Response coordination, executive briefings"},
            {"role": "Security Lead", "responsibilities": "Containment, investigation, remediation"},
            {"role": "Legal/Privacy Lead", "responsibilities": "Breach notification, regulatory compliance"},
            {"role": "Communications Lead", "responsibilities": "Customer notification, media response, FAQ preparation"},
        ],
        "resources_needed": [
            "Data classification inventory",
            "Breach notification templates (by jurisdiction)",
            "Forensic investigation tools",
            "External legal counsel (privacy/cyber)",
            "Customer communication channels",
        ],
    },
    "outage": {
        "title": "Service Outage Response Playbook",
        "immediate_actions": [
            "Confirm outage scope - which services, which users affected",
            "Check monitoring dashboards for root cause indicators",
            "Engage on-call engineers for affected systems",
            "Post status page update within 15 minutes",
            "Establish communication cadence (every 30 min until resolved)",
        ],
        "roles": [
            {"role": "Incident Commander", "responsibilities": "Coordination, stakeholder updates, escalation decisions"},
            {"role": "Technical Lead", "responsibilities": "Root cause analysis, remediation, failover"},
            {"role": "Communications Lead", "responsibilities": "Status page updates, customer notifications"},
            {"role": "Support Lead", "responsibilities": "Customer impact assessment, support queue management"},
        ],
        "resources_needed": [
            "Monitoring and alerting dashboards",
            "Runbooks for common failure modes",
            "Escalation contact list",
            "Status page access",
            "Post-incident review template",
        ],
    },
    "weather": {
        "title": "Severe Weather Response Playbook",
        "immediate_actions": [
            "Monitor official weather alerts (NWS, local emergency management)",
            "Activate early dismissal or shelter-in-place protocol as warranted",
            "Secure outdoor equipment and close windows",
            "Identify interior safe rooms away from windows",
            "Account for all personnel in building",
        ],
        "roles": [
            {"role": "Incident Commander", "responsibilities": "Weather monitoring, shelter/evacuation decisions"},
            {"role": "Facilities Lead", "responsibilities": "Building preparation, utility management"},
            {"role": "Communications Lead", "responsibilities": "Staff alerts, closure decisions, re-opening communication"},
            {"role": "Transportation Lead", "responsibilities": "Safe commute assessment, remote work activation"},
        ],
        "resources_needed": [
            "NOAA weather radio",
            "Emergency supplies (water, food, flashlights)",
            "Interior safe room designations",
            "Remote work capability",
            "Emergency contact tree",
        ],
    },
    "medical": {
        "title": "Medical Emergency Response Playbook",
        "immediate_actions": [
            "Call 911 immediately - provide exact location and nature of emergency",
            "Administer first aid if trained - CPR, AED, bleeding control",
            "Clear the area around the patient",
            "Send someone to meet and guide EMS to the patient",
            "Do NOT move the patient unless in immediate danger",
        ],
        "roles": [
            {"role": "Incident Commander", "responsibilities": "Coordinate response, communicate with EMS"},
            {"role": "First Responder", "responsibilities": "Administer first aid, stabilize patient"},
            {"role": "Guide", "responsibilities": "Meet EMS at entrance, direct to patient location"},
            {"role": "Communications Lead", "responsibilities": "Notify relevant parties, manage information flow"},
        ],
        "resources_needed": [
            "First aid kit (with AED location known)",
            "Emergency medical information for staff",
            "AED (Automated External Defibrillator)",
            "Emergency contact information",
            "Incident documentation forms",
        ],
    },
    "generic": {
        "title": "General Incident Response Playbook",
        "immediate_actions": [
            "Assess the situation - determine scope and severity",
            "Ensure immediate safety of all personnel",
            "Notify relevant leadership and stakeholders",
            "Document the incident - what happened, when, who is affected",
            "Establish communication cadence for updates",
        ],
        "roles": [
            {"role": "Incident Commander", "responsibilities": "Overall coordination, decision authority"},
            {"role": "Operations Lead", "responsibilities": "Execute response actions, manage resources"},
            {"role": "Communications Lead", "responsibilities": "Internal/external updates, stakeholder management"},
            {"role": "Documentation Lead", "responsibilities": "Record timeline, actions, decisions for after-action review"},
        ],
        "resources_needed": [
            "Incident documentation template",
            "Emergency contact list",
            "Communication tools (backup channels)",
            "Relevant SOPs and procedures",
            "Post-incident review template",
        ],
    },
}


def get_playbook(playbook_key: str) -> dict:
    return PLAYBOOKS.get(playbook_key, PLAYBOOKS["generic"])


def format_playbook_message(crisis_type_key: str) -> str:
    from crisis.models import CRISIS_TYPES

    crisis_info = CRISIS_TYPES.get(crisis_type_key, CRISIS_TYPES["other"])
    playbook = get_playbook(crisis_info["playbook"])

    lines = [f"*{playbook['title']}*\n"]

    lines.append("*Immediate Actions:*")
    for i, action in enumerate(playbook["immediate_actions"], 1):
        lines.append(f">{i}. {action}")

    lines.append("\n*Roles Needed:*")
    for role in playbook["roles"]:
        lines.append(f">*{role['role']}* - {role['responsibilities']}")

    lines.append("\n*Resources:*")
    for resource in playbook["resources_needed"]:
        lines.append(f">- {resource}")

    return "\n".join(lines)
