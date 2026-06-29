# FirstResponder

**Crisis & incident coordination agent for Slack. Turns your workspace into a coordination center in 60 seconds.**

When crisis strikes, FirstResponder activates with a single command. It posts response playbooks, tracks who is safe, creates dedicated incident channels, generates situation reports by reading channel conversations, and produces after-action reports with historical comparison. It knows your building layout, your people, your infrastructure. It learns from every incident and gets smarter over time.

**Track:** Slack Agent for Good
**Hackathon:** [Slack Agent Builder Challenge](https://slackhack.devpost.com/)
**License:** Apache 2.0

---

## The Problem

PagerDuty costs $21/user/month. Opsgenie costs $9/user. A school with 50 staff pays $12K/year for incident management. A nonprofit running on grants cannot justify that cost.

When an active shooter enters a school, a ransomware attack hits a nonprofit, or a fire breaks out at a community center, the people who need crisis coordination tools the most are the ones who can't afford them.

These organizations fall back on panic in group chats, phone trees that fail, and paper rosters that no one can find during an emergency. Personnel accountability takes 30+ minutes when it should take 3.

## The Solution

FirstResponder gives every Slack workspace a crisis coordination system for free. One command, full incident management, with an AI agent that knows your building, your people, and your infrastructure.

```
/crisis start active-threat Gunshots heard near east entrance
```

Within seconds:
- Incident declared with unique ID and severity classification
- Response playbook posted (Run/Hide/Fight protocol with 5 immediate actions)
- Personnel accountability system activated (react with a checkmark to mark safe)
- Agent queries building layout: safe evacuation routes, blocked routes, people in the danger zone
- Agent checks for mobility-limited personnel who need assistance
- Agent locates nearest first aid responders and emergency resources
- Past incident intelligence surfaced: "You've had 2 similar incidents. Avg resolution: 34 min"

---

## Architecture

```
                          Slack Workspace
                               |
                    +-----------+-----------+
                    |                       |
              /crisis command         @FirstResponder
              (slash command)           (AI agent)
                    |                       |
                    v                       v
            +-------+-------+    +---------+---------+
            | Slash Handler |    | Claude Agent SDK   |
            | (listeners/)  |    | (agent/agent.py)   |
            +-------+-------+    +---------+---------+
                    |                       |
                    |              +--------+--------+
                    |              |  32 Agent Tools  |
                    |              +--------+--------+
                    |                       |
          +---------+-----------+-----------+---------+
          |                     |                     |
+---------v---------+ +---------v---------+ +---------v---------+
| Layer 1: Crisis   | | Layer 2: Learning | | Layer 3: Knowledge|
| Coordination      | | Engine            | | Base              |
|                   | |                   | |                   |
| crisis/manager.py | | crisis/store.py   | | crisis/knowledge  |
| crisis/models.py  | | (SQLite)          | | .py (SQLite)      |
| crisis/playbooks  | |                   | |                   |
| .py               | | - Incident history| | - Facility layout |
|                   | | - Lessons learned | | - Personnel dir.  |
| - 10 crisis types | | - Pattern recog.  | | - Evacuation rtes |
| - Check-in track. | | - Org-wide stats  | | - Emergency rsrc. |
| - SITREP gen.     | | - Historical comp. | | - Network topo.   |
| - After-action    | |                   | | - Data inventory   |
| - Role assignment | |                   | | - Runbooks         |
| - Incident chans. | |                   | | - On-call sched.   |
+-------------------+ +-------------------+ | - Vendor contacts |
                                             | - Hazmat locations|
                                             | - Utility controls|
                                             | - Assembly points |
                                             | - Nearby hospitals|
                                             | - Drill history   |
                                             | - Continuity plans|
                                             +-------------------+
                                                      |
                                              Slack MCP Server
                                             (channel search via
                                              Real-Time Search API)
```

### Three Intelligence Layers

**Layer 1 - Crisis Coordination** handles the core incident lifecycle: declaring crises, posting playbooks, tracking check-ins via emoji reactions, creating incident channels, assigning roles, generating SITREPs, and producing after-action reports.

**Layer 2 - Learning Engine** persists every incident to SQLite. After resolution, the team records lessons learned. When a new crisis starts, the agent automatically searches past incidents of the same type and surfaces what worked before. After-action reports compare resolution time against historical averages. The agent gets smarter with every incident.

**Layer 3 - Knowledge Base** stores the organization's specific context: building layouts with zones and rooms, personnel directory with locations and emergency contacts, evacuation routes that account for threat-zone blocking, emergency resources like AEDs and fire extinguishers, network topology with dependency mapping, data inventory with regulatory requirements, step-by-step runbooks, on-call schedules, and more. This is what transforms generic advice into "Mrs. Thompson is in Room 204, Floor 2, east wing. She has mobility limitations. Nearest AED is in hallway B."

### Technologies Used

| Technology | How It's Used |
|---|---|
| **Slack AI (Agent Builder)** | Assistant view, suggested prompts, streaming responses, feedback buttons |
| **MCP Server Integration** | Slack MCP Server for searching channel messages to generate SITREPs, finding past discussions, reading channel context |
| **Real-Time Search API** | Powers channel message search through the Slack MCP Server for situation report generation |
| **Claude Agent SDK** | AI agent framework with 32 registered tools, session management, streaming responses |
| **Bolt for Python** | Slack app framework handling events, slash commands, actions, and Socket Mode |

---

## Features

### Crisis Management
- **10 crisis types** with full response playbooks: earthquake, fire, flood, active threat, cyberattack, data breach, service outage, severe weather, medical emergency, and general incidents
- **`/crisis` slash command** with subcommands: `start`, `status`, `checkin`, `resolve`, `playbook`, `help`
- **Emoji check-ins** during crises: react with a checkmark to mark safe, SOS for help needed, ambulance if injured
- **Dedicated incident channels** auto-created with topic set to crisis type, severity, and incident ID
- **Incident Commander assignment** with timeline tracking
- **Situation reports (SITREPs)** generated by the AI reading channel conversation via Slack MCP
- **After-action reports** with complete timeline, personnel accountability, and historical comparison

### Learning Engine
- **Persistent incident history** in SQLite (survives restarts)
- **Lessons learned** recorded per incident, automatically surfaced in future incidents of the same type
- **Pattern recognition**: "Based on 3 past fire incidents, average resolution is 45 minutes"
- **Historical comparison** in after-action reports: "This incident was resolved 12 minutes faster than average"
- **Organization-wide stats**: total incidents, average resolution time, check-in rates by type
- **Past incident search** by keyword across all resolved incidents
- **Time-based escalation** for missing check-ins: initial reminder, DM, phone contact, emergency services

### Knowledge Base (Context-Aware Response)
- **Building layouts**: facilities, zones, rooms, floors with capacity
- **Personnel directory**: default locations, phone numbers, emergency contacts, medical notes
- **Evacuation routes**: primary and alternate routes with threat-zone blocking logic
- **Emergency resources**: AED locations, fire extinguishers, first aid kits, trauma kits
- **Utility controls**: gas, electrical, water, HVAC shutoff locations with key requirements
- **Assembly points**: primary and alternate rally points with capacity and accessibility
- **Hazmat locations**: chemicals, hazard class, containment instructions, safety data sheets
- **Nearby emergency services**: hospitals with trauma levels, fire and police stations with ETA
- **Network topology**: asset inventory with dependency mapping for blast radius analysis
- **Data inventory**: classification, PII fields, record counts, regulatory frameworks, notification timelines
- **Runbooks**: tested step-by-step recovery procedures with estimated resolution times
- **On-call schedules**: primary, secondary, and escalation contacts per service
- **Vendor contacts**: emergency contacts, SLA hours, escalation procedures
- **Drill history**: evacuation times, accountability times, issues noted, slowest zones
- **Business continuity plans**: remote work capability, backup facilities, recovery time objectives

### Per-Scenario Intelligence

The agent triggers different knowledge queries depending on the crisis type:

| Scenario | Auto-Queried Context |
|---|---|
| **Fire** | Gas shutoff, hazmat near fire, safe/blocked evacuation routes, assembly points, people in danger zone, fire dept ETA, drill benchmark |
| **Earthquake** | All utility shutoffs, hazmat everywhere (rupture risk), mobility-limited personnel, hospital ETA, continuity plan |
| **Active Threat** | People in danger zone, safe routes away from threat, police ETA, missing person lookup, assembly point away from threat |
| **Flood** | Electrical shutoff (electrocution risk), hazmat contamination, ground floor personnel, continuity plan |
| **Medical** | Nearest CPR/AED trained person, AED location, patient medical records, nearest hospital with trauma level |
| **Cyberattack** | Blast radius of compromised system, attack-type runbook, security on-call, data at risk, vendor escalation |
| **Data Breach** | Data inventory (PII + records + regulatory), notification timelines, legal on-call, breach notification runbook |
| **Outage** | Service dependency tree, on-call engineer, system-specific runbook, vendor SLA, continuity plan |
| **Weather** | Continuity plan, interior shelter points, utility prep, personnel in vulnerable locations |

---

## Setup Instructions

### Prerequisites

- Python 3.12+
- A Slack workspace (free [Developer Sandbox](https://api.slack.com/developer-program))
- [Slack CLI](https://api.slack.com/automation/cli/install) v4.0+
- An [Anthropic API key](https://console.anthropic.com/) for the Claude Agent SDK

### 1. Clone and Install

```bash
git clone https://github.com/4KInc/firstresponder-slack.git
cd firstresponder-slack
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Configure Environment

```bash
cp .env.sample .env
# Edit .env and set your ANTHROPIC_API_KEY
```

### 3. Authenticate Slack CLI

```bash
slack login
```

Follow the prompts to authenticate against your Slack workspace. Paste the `/slackauthticket` command in any Slack channel, approve the permissions, and enter the challenge code.

### 4. Create the App

The app is configured via `manifest.json`. The Slack CLI uses this to create the app in your workspace:

```bash
slack run
```

This starts the app locally with hot reload. The CLI creates the app from the manifest, provisions Socket Mode credentials, and starts listening for events.

### 5. Run Without Slack CLI (Optional)

If running outside the CLI (e.g., in production):

```bash
# Set tokens in .env:
# SLACK_APP_TOKEN=xapp-...
# SLACK_BOT_TOKEN=xoxb-...
python3 app.py
```

### 6. Configure Knowledge Base (Optional)

For context-aware responses, load your organizational data. The knowledge base uses SQLite and can be populated via Python:

```python
from crisis.knowledge import knowledge_base

# Add your facility
knowledge_base.add_facility("hq", "Main Office", "123 Main St", floors=3, capacity=200)

# Add zones
knowledge_base.add_zone("east-wing", "hq", "East Wing", floor=1,
    primary_exit="Door 3", alternate_exit="Door 7")

# Add personnel
knowledge_base.add_person("p001", "Sarah Johnson", slack_user_id="U01ABC",
    role="IT Director", default_location="east-wing", floor=2, phone="555-0101",
    emergency_contact_name="John Johnson", emergency_contact_phone="555-0102",
    trained_first_aid=True)

# Add emergency resources
knowledge_base.add_emergency_resource("hq", "aed", "Hallway B outside Room 112", floor=1)

# Add evacuation routes
knowledge_base.add_evacuation_route("hq", "East Stairwell", "Door 3",
    "East stairwell to ground floor, exit via Door 3",
    from_zone="east-wing", blocked_by_zones=["east-entrance"])
```

### 7. Run Tests

```bash
python -m pytest tests/ -v
```

---

## Usage

### Slash Commands

```
/crisis start <type> <description>    Start a new crisis
/crisis status                        View active crisis status
/crisis checkin [safe|injured|evacuated|need-help]    Check in
/crisis resolve                       Resolve the active crisis
/crisis playbook <type>               View a response playbook
/crisis help                          Show available commands
```

### AI Agent (DM or @mention)

```
@FirstResponder We have a fire on the 3rd floor near the chemistry lab
@FirstResponder Show me the status of all active incidents
@FirstResponder Who hasn't checked in yet?
@FirstResponder Generate a SITREP for the current incident
@FirstResponder What did we learn from past fire incidents?
@FirstResponder Show me our organization's incident response stats
```

### Emoji Check-Ins

During an active crisis, react to any message in the incident channel:
- React with a checkmark: checked in as **safe**
- React with SOS: checked in as **need-help**
- React with ambulance: checked in as **injured**
- React with door: checked in as **evacuated**

---

## Project Structure

```
firstresponder-slack/
+-- app.py                          # Entry point (Bolt for Python + Socket Mode)
+-- manifest.json                   # Slack app configuration
+-- agent/
|   +-- agent.py                    # Claude Agent SDK integration + system prompt
|   +-- deps.py                     # Agent dependencies (Slack client, context)
|   +-- context.py                  # Context variables for tool access
|   +-- tools/
|       +-- crisis.py               # Crisis lifecycle tools (start, resolve, channel)
|       +-- checkin.py              # Personnel check-in tool
|       +-- sitrep.py               # Situation report generation
|       +-- playbooks.py            # Response playbook retrieval
|       +-- emoji_reaction.py       # Contextual emoji reactions
|       +-- intelligence.py         # Learning engine tools (search, lessons, stats)
|       +-- knowledge.py            # General knowledge base tools (8 tools)
|       +-- physical_safety.py      # Physical crisis tools (5 tools)
|       +-- cyber_tools.py          # Cyber/operations tools (4 tools)
+-- crisis/
|   +-- models.py                   # Data models (Crisis, CheckIn, SitRep, etc.)
|   +-- manager.py                  # Crisis state manager with persistence
|   +-- playbooks.py               # 10 response playbooks with roles + resources
|   +-- store.py                    # SQLite incident store (Layer 2)
|   +-- knowledge.py               # SQLite knowledge base (Layer 3)
+-- listeners/
|   +-- events/                     # Slack event handlers
|   |   +-- message.py              # DM message handling
|   |   +-- app_mentioned.py        # @mention handling
|   |   +-- assistant_thread_started.py  # Suggested prompts
|   |   +-- reaction_added.py       # Emoji check-in tracking
|   |   +-- slash_crisis.py         # /crisis command handler
|   |   +-- app_home_opened.py      # App Home tab
|   +-- actions/                    # Button actions (feedback)
|   +-- views/                      # Block Kit view builders
+-- thread_context/
|   +-- store.py                    # Session management for agent conversations
+-- tests/                          # 19 tests (crisis manager, playbooks, intelligence)
+-- data/                           # SQLite databases (auto-created)
```

---

## Impact

### Who This Serves

| Organization Type | Why They Need This |
|---|---|
| **K-12 Schools** | Active shooter drills, fire evacuations, severe weather shelter-in-place, medical emergencies. Most schools use paper rosters and walkie-talkies for accountability. |
| **Nonprofits** | Operate on grants with no budget for security tools. Face the same cyber threats (ransomware, phishing, data breaches) as enterprises. |
| **Small Businesses** | Service outages, workplace incidents, natural disasters. Cannot afford a SOC or incident management platform. |
| **Houses of Worship** | Medical emergencies, active threats, severe weather. Volunteer-run with no IT staff. |
| **Community Organizations** | Disaster response coordination, volunteer safety tracking, event safety management. |
| **Open Source Projects** | Security vulnerability response, infrastructure outage coordination. |

### By the Numbers

- Enterprise incident management: **$21/user/month** (PagerDuty) to **$45/user/month** (ServiceNow)
- A 50-person school: **$12,600/year** for basic incident management
- FirstResponder: **$0**
- Time to go from "emergency reported" to "full coordination active": **< 60 seconds**

---

## Technical Highlights

- **32 AI agent tools** across 7 modules, each with typed schemas and contextual descriptions
- **10 crisis playbooks** with immediate actions, role assignments, and resource requirements
- **SQLite dual-database architecture**: incident store (learning) + knowledge base (context)
- **Threat-zone-aware evacuation routing**: routes automatically filtered based on where the threat is
- **Dependency-graph blast radius analysis**: trace impact through network topology
- **Time-based escalation engine**: missing check-in urgency increases from reminder to 911
- **Learning loop**: lessons from Incident N automatically surface during Incident N+1
- **Zero external dependencies beyond Slack**: no AWS, no cloud databases, no infrastructure to manage
- **19 automated tests** covering crisis management, playbook integrity, and intelligence layer

---

## Built With

- [Bolt for Python](https://slack.dev/bolt-python/) (Slack app framework)
- [Claude Agent SDK](https://docs.anthropic.com/en/docs/agents) (AI agent orchestration)
- [Slack MCP Server](https://docs.slack.dev/ai/slack-mcp-server/) (channel search + context)
- [SQLite](https://sqlite.org/) (persistence + knowledge base)
- Python 3.12+

---

*FirstResponder is not a replacement for calling 911 or emergency services. Always contact emergency services for life-threatening situations. This tool coordinates organizational response alongside professional emergency responders.*
