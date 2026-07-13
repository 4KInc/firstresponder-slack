# FirstResponder

**Crisis & incident coordination agent for Slack. Turns your workspace into a coordination center in 60 seconds.**

When crisis strikes, FirstResponder activates with a single command. It posts response playbooks, tracks who is safe (staff and students, classroom by classroom), creates dedicated incident channels, generates situation reports by reading channel conversations, hands arriving police a crisp tactical brief, and produces after-action reports with historical comparison. It knows your building, your people, and your infrastructure because you upload them as CSVs, no code required. It learns from every incident and gets smarter over time.

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
- Agent totals everyone in the threat zone (staff and students) and tracks accountability room by room
- Agent checks for mobility-limited personnel who need assistance
- Agent locates nearest first aid responders and emergency resources
- When responders arrive, agent generates a one-card tactical brief for law enforcement
- Past incident intelligence surfaced: "You've had 2 similar incidents. Avg resolution: 34 min"

### Upload your data, no code required

The knowledge base is populated by dropping CSV files into a Slack channel. FirstResponder auto-detects each file's type from its columns (facility, zones, rooms, personnel, evacuation routes, hazmat, on-call, and 10 more), loads it into the knowledge base, and confirms what it ingested. Re-uploading a corrected file replaces that data instead of duplicating it. Ready-to-edit templates for every type live in [`templates/`](templates/).

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
                    |              |  35 Agent Tools  |
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
| - Classroom acct. | | - Historical comp. | | - Network topo.   |
| - SITREP gen.     | |                   | | - Data inventory   |
| - Police handoff  | |                   | | - Runbooks         |
| - After-action    | |                   | | - On-call sched.   |
| - Role assignment | |                   | | - Vendor contacts |
| - Incident chans. | |                   | | - Hazmat locations|
+-------------------+ +-------------------+ | - Utility controls|
                                             | - Assembly points |
              CSV upload -> auto-detect ---> | - Nearby hospitals|
              (crisis/ingest.py)             | - Drill history   |
                                             | - Continuity plans|
                                             +-------------------+
                                                      |
                                              Slack MCP Server
                                             (channel search via
                                              Real-Time Search API)
```

### Three Intelligence Layers

**Layer 1 - Crisis Coordination** handles the core incident lifecycle: declaring crises, posting playbooks, tracking check-ins via emoji reactions, running classroom-by-classroom student accountability, creating incident channels, assigning roles, generating SITREPs, briefing arriving law enforcement, and producing after-action reports.

**Layer 2 - Learning Engine** persists every incident to SQLite. After resolution, the team records lessons learned. When a new crisis starts, the agent automatically searches past incidents of the same type and surfaces what worked before. After-action reports compare resolution time against historical averages. The agent gets smarter with every incident.

**Layer 3 - Knowledge Base** stores the organization's specific context: building layouts with zones and rooms, personnel directory with locations and emergency contacts, evacuation routes that account for threat-zone blocking, emergency resources like AEDs and fire extinguishers, network topology with dependency mapping, data inventory with regulatory requirements, step-by-step runbooks, on-call schedules, and more. This is what transforms generic advice into "Mrs. Thompson is in Room 204, Floor 2, east wing. She has mobility limitations. Nearest AED is in hallway B."

### Technologies Used

| Technology | How It's Used |
|---|---|
| **Slack AI (Agent Builder)** | Assistant view, suggested prompts, streaming responses, feedback buttons |
| **MCP Server Integration** | Slack MCP Server for searching channel messages to generate SITREPs, finding past discussions, reading channel context |
| **Real-Time Search API** | Powers channel message search through the Slack MCP Server for situation report generation |
| **Claude Agent SDK** | AI agent framework with 35 registered tools, session management, streaming responses |
| **Bolt for Python** | Slack app framework handling events, slash commands, actions, and Socket Mode |
| **CSV ingest engine** | Auto-detects file type from column headers and loads org data into the knowledge base from a Slack file upload, no code required |

---

## Features

### Crisis Management
- **10 crisis types** with full response playbooks: earthquake, fire, flood, active threat, cyberattack, data breach, service outage, severe weather, medical emergency, and general incidents
- **`/crisis` slash command** with subcommands: `start`, `status`, `checkin`, `resolve`, `playbook`, `help`
- **Emoji check-ins** during crises: react with a checkmark to mark safe, SOS for help needed, ambulance if injured
- **Classroom-level student accountability**: teachers report headcounts per room; the agent tracks safe, unaccounted, and silent rooms across the building
- **Law enforcement handoff brief**: one scannable card for arriving police (threat, headcount, unaccounted, assisted-rescue needs, doors to avoid vs use, hazards, on-site medical, IC contact)
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
| **Active Threat** | Everyone in danger zone (staff + students), classroom-by-classroom accountability, safe routes away from threat, police ETA, person lookup by name or room, law enforcement handoff brief |
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

### 6. Configure Knowledge Base (Upload CSVs)

For context-aware responses, load your organizational data. The easiest way is to **upload CSV files directly into a Slack channel** with FirstResponder present. It auto-detects each file's type from its column headers, loads it into the knowledge base, and confirms what it ingested. Re-uploading a corrected file replaces that data instead of duplicating it.

Copy the templates in [`templates/`](templates/), fill in your own building, people, and routes, and drop them into Slack:

```
templates/
  facility.csv            zones.csv              rooms.csv
  personnel.csv           evacuation_routes.csv  emergency_resources.csv
  assembly_points.csv     hazmat_locations.csv   utility_controls.csv
  nearby_services.csv     drills.csv             vendor_contacts.csv
  network_assets.csv      data_inventory.csv     runbooks.csv
  on_call_schedules.csv   continuity_plans.csv
```

Prefer code? The same data can be loaded programmatically:

```python
from crisis.knowledge import knowledge_base

knowledge_base.add_facility("hq", "Main Office", "123 Main St", floors=3, capacity=200)
knowledge_base.add_person("p001", "Sarah Johnson", slack_user_id="U01ABC",
    role="IT Director", default_location="east-wing", floor=2, phone="555-0101",
    trained_first_aid=True)
```

### 7. Run Tests

```bash
python -m pytest tests/ -v
```

### 8. Deploy Always-On (Optional)

Because FirstResponder runs over Socket Mode (not Slack's serverless platform), it is deployed as a long-running process. A [`Dockerfile`](Dockerfile) is included (Python 3.12 + Node + the `claude` CLI, running as a non-root user). Build it and run it anywhere that keeps a container alive 24/7, for example a small always-on VM:

```bash
docker build -t firstresponder .
docker run -d --env-file .env firstresponder
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
+-- Dockerfile                      # Always-on container (Python 3.12 + Node + claude CLI)
+-- agent/
|   +-- agent.py                    # Claude Agent SDK integration + system prompt
|   +-- deps.py                     # Agent dependencies (Slack client, context)
|   +-- context.py                  # Context variables for tool access
|   +-- tools/                      # 35 registered agent tools
|       +-- crisis.py               # Crisis lifecycle tools (start, resolve, channel)
|       +-- checkin.py              # Personnel check-in tool
|       +-- classroom.py            # Classroom-level student accountability (2 tools)
|       +-- brief.py                # Law enforcement handoff brief
|       +-- sitrep.py               # Situation report generation
|       +-- playbooks.py            # Response playbook retrieval
|       +-- emoji_reaction.py       # Contextual emoji reactions
|       +-- intelligence.py         # Learning engine tools (search, lessons, stats)
|       +-- knowledge.py            # General knowledge base tools (8 tools)
|       +-- physical_safety.py      # Physical crisis tools (5 tools)
|       +-- cyber_tools.py          # Cyber/operations tools (4 tools)
+-- crisis/
|   +-- models.py                   # Data models (Crisis, CheckIn, SitRep, ClassroomReport)
|   +-- manager.py                  # Crisis state manager with persistence + rehydration
|   +-- playbooks.py               # 10 response playbooks with roles + resources
|   +-- ingest.py                   # CSV ingest engine (auto-detects 17 file types)
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
+-- templates/                      # CSV templates for every knowledge-base type
+-- tests/                          # 28 tests (crisis manager, playbooks, intelligence, ingest)
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

- **35 AI agent tools** across 11 modules, each with typed schemas and contextual descriptions
- **CSV ingest engine**: auto-detects 17 file types from column headers, idempotent re-upload, populated straight from a Slack file upload
- **Classroom-level accountability**: tracks students room by room, not just a building-wide headcount
- **10 crisis playbooks** with immediate actions, role assignments, and resource requirements
- **SQLite dual-database architecture**: incident store (learning) + knowledge base (context)
- **Threat-zone-aware evacuation routing**: routes automatically filtered based on where the threat is
- **Dependency-graph blast radius analysis**: trace impact through network topology
- **Time-based escalation engine**: missing check-in urgency increases from reminder to 911
- **Learning loop**: lessons from Incident N automatically surface during Incident N+1
- **No cloud-service dependencies**: SQLite for storage, Socket Mode for transport, self-hostable in a single container
- **28 automated tests** covering crisis management, playbook integrity, the intelligence layer, and CSV ingest

---

## Built With

- [Bolt for Python](https://slack.dev/bolt-python/) (Slack app framework)
- [Claude Agent SDK](https://docs.anthropic.com/en/docs/agents) (AI agent orchestration)
- [Slack MCP Server](https://docs.slack.dev/ai/slack-mcp-server/) (channel search + context)
- [SQLite](https://sqlite.org/) (persistence + knowledge base)
- [Docker](https://www.docker.com/) (always-on self-hosted deployment)
- Python 3.12+

---

*FirstResponder is not a replacement for calling 911 or emergency services. Always contact emergency services for life-threatening situations. This tool coordinates organizational response alongside professional emergency responders.*
