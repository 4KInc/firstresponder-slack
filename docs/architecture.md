# FirstResponder Architecture

## System Overview

```mermaid
flowchart TB
    subgraph SLACK["Slack Workspace"]
        USER["User"]
        SLASH["/crisis command"]
        MENTION["@FirstResponder"]
        EMOJI["Emoji Reactions"]
        HOME["App Home Tab"]
        CHANNEL["Incident Channel"]
    end

    subgraph APP["FirstResponder Agent"]
        subgraph LISTENERS["Listeners (Bolt for Python)"]
            SLASH_H["Slash Command Handler"]
            MSG_H["Message Handler"]
            MENTION_H["App Mention Handler"]
            REACT_H["Reaction Handler"]
            HOME_H["App Home Handler"]
        end

        subgraph AGENT["AI Agent (Claude Agent SDK)"]
            PROMPT["System Prompt\n(Scenario Protocols)"]
            SESSION["Session Manager"]
            STREAM["Response Streamer"]
        end

        subgraph TOOLS["32 Agent Tools"]
            subgraph T1["Crisis Management (10)"]
                START["start_crisis"]
                CHECKIN["check_in"]
                STATUS["crisis_status"]
                RESOLVE["resolve_crisis"]
                SITREP["generate_sitrep"]
                PLAYBOOK["get_playbook"]
                EMOJIT["add_emoji_reaction"]
                INC_CHAN["create_incident_channel"]
                IC["assign_incident_commander"]
                AAR["generate_after_action_report"]
            end

            subgraph T2["Intelligence (5)"]
                SEARCH["search_past_incidents"]
                INTEL["get_incident_intelligence"]
                LESSON["add_lesson_learned"]
                STATS["get_organization_stats"]
                MISSING["get_missing_checkin_report"]
            end

            subgraph T3["Knowledge - General (8)"]
                EVAC["get_evacuation_guidance"]
                RESOURCES["find_emergency_resources"]
                LOOKUP["lookup_person"]
                FIRSTAID["find_first_aid_responders"]
                BLAST["get_blast_radius"]
                VENDOR["get_vendor_contacts"]
                DRILL["get_drill_performance"]
                SUMMARY["get_knowledge_summary"]
            end

            subgraph T4["Physical Safety (5)"]
                UTILITY["get_utility_controls"]
                ASSEMBLY["get_assembly_points"]
                HAZMAT["get_hazmat_info"]
                HOSPITAL["get_nearest_emergency_services"]
                DANGER["get_people_in_danger_zone"]
            end

            subgraph T5["Cyber & Ops (4)"]
                DATA["get_data_at_risk"]
                RUNBOOK["get_runbook"]
                ONCALL["get_on_call"]
                CONTINUITY["get_continuity_plan"]
            end
        end
    end

    subgraph STORAGE["Persistent Storage (SQLite)"]
        subgraph L2["Layer 2: Learning Engine"]
            INC_DB[("Incidents")]
            CHECK_DB[("Check-ins")]
            TIME_DB[("Timeline Events")]
            SIT_DB[("SITREPs")]
            LESSON_DB[("Lessons Learned")]
        end

        subgraph L3["Layer 3: Knowledge Base"]
            FAC_DB[("Facilities\nZones, Rooms")]
            PERS_DB[("Personnel\nDirectory")]
            EVAC_DB[("Evacuation\nRoutes")]
            RES_DB[("Emergency\nResources")]
            NET_DB[("Network\nTopology")]
            DATA_DB[("Data\nInventory")]
            RUN_DB[("Runbooks")]
            OC_DB[("On-Call\nSchedules")]
            UTIL_DB[("Utility\nControls")]
            HAZ_DB[("Hazmat\nLocations")]
            SVC_DB[("Nearby\nServices")]
            ASM_DB[("Assembly\nPoints")]
            VEN_DB[("Vendor\nContacts")]
            DRL_DB[("Drill\nHistory")]
            CON_DB[("Continuity\nPlans")]
        end
    end

    subgraph EXTERNAL["External Services"]
        SLACK_MCP["Slack MCP Server\n(mcp.slack.com)"]
        ANTHROPIC["Anthropic API\n(Claude)"]
    end

    USER --> SLASH & MENTION & EMOJI & HOME
    SLASH --> SLASH_H
    MENTION --> MENTION_H
    EMOJI --> REACT_H
    HOME --> HOME_H

    SLASH_H --> AGENT
    MSG_H --> AGENT
    MENTION_H --> AGENT
    REACT_H --> CHECKIN

    AGENT --> TOOLS
    AGENT --> SLACK_MCP
    AGENT --> ANTHROPIC
    AGENT --> STREAM --> CHANNEL

    T1 --> L2
    T2 --> L2
    T3 --> L3
    T4 --> L3
    T5 --> L3

    style SLACK fill:#4A154B,color:#fff
    style AGENT fill:#D97706,color:#fff
    style L2 fill:#1D4ED8,color:#fff
    style L3 fill:#059669,color:#fff
    style EXTERNAL fill:#6B7280,color:#fff
```

## Data Flow: Crisis Lifecycle

```mermaid
sequenceDiagram
    participant U as User
    participant S as Slack
    participant A as Agent
    participant L2 as Learning Engine
    participant L3 as Knowledge Base
    participant MCP as Slack MCP

    Note over U,MCP: Phase 1: Crisis Declaration
    U->>S: /crisis start fire 3rd floor lab
    S->>A: Slash command event
    A->>L2: Check past fire incidents
    L2-->>A: "3 past fires, avg 45 min"
    A->>L3: get_evacuation_guidance(zone="3rd-floor")
    L3-->>A: Safe routes, blocked routes, mobility-limited staff
    A->>L3: get_hazmat_info(floor=3)
    L3-->>A: Chemistry lab chemicals list
    A->>L3: get_utility_controls(type="gas")
    L3-->>A: Gas shutoff location + instructions
    A->>L2: Save incident to DB
    A->>S: Post playbook + check-in prompt + intelligence

    Note over U,MCP: Phase 2: Personnel Accountability
    U->>S: React with checkmark emoji
    S->>A: reaction_added event
    A->>L2: Save check-in
    A-->>S: "Sarah checked in safe (12/45)"

    Note over U,MCP: Phase 3: Situation Report
    U->>S: @FirstResponder generate SITREP
    S->>A: Message event
    A->>MCP: Search channel messages
    MCP-->>A: Recent channel conversation
    A->>L2: Get check-in status
    A->>A: Synthesize SITREP from conversation + data
    A->>L2: Save SITREP
    A-->>S: SITREP #1 posted

    Note over U,MCP: Phase 4: Resolution + Learning
    U->>S: /crisis resolve
    S->>A: Slash command event
    A->>L2: Mark resolved, calc duration
    A->>L2: Get historical comparison
    A-->>S: After-action report + "What did we learn?"
    U->>S: "We should have shut gas immediately"
    A->>L2: Save lesson learned
    A-->>S: "Lesson recorded. Will surface in next fire incident."
```

## Three-Layer Intelligence Model

```mermaid
graph TB
    subgraph L1["Layer 1: Crisis Coordination"]
        direction LR
        C1["10 Crisis Types"]
        C2["Playbooks"]
        C3["Check-ins"]
        C4["SITREPs"]
        C5["Incident Channels"]
        C6["Role Assignment"]
        C7["After-Action Reports"]
    end

    subgraph L2["Layer 2: Learning Engine"]
        direction LR
        I1["Incident History"]
        I2["Lessons Learned"]
        I3["Pattern Recognition"]
        I4["Historical Comparison"]
        I5["Escalation Engine"]
        I6["Org-Wide Stats"]
    end

    subgraph L3["Layer 3: Knowledge Base"]
        direction LR
        subgraph PHYS["Physical"]
            P1["Floor Plans"]
            P2["Evacuation Routes"]
            P3["Personnel Locations"]
            P4["Emergency Resources"]
            P5["Utility Controls"]
            P6["Hazmat Locations"]
            P7["Assembly Points"]
            P8["Nearby Hospitals"]
        end
        subgraph CYBER["Cyber"]
            C8["Network Topology"]
            C9["Data Inventory"]
            C10["Runbooks"]
            C11["On-Call Schedules"]
        end
        subgraph OPS["Operations"]
            O1["Vendor Contacts"]
            O2["Continuity Plans"]
            O3["Drill History"]
        end
    end

    L1 --> L2
    L2 --> L3

    style L1 fill:#DC2626,color:#fff
    style L2 fill:#2563EB,color:#fff
    style L3 fill:#059669,color:#fff
```

## Scenario Intelligence Matrix

Each crisis type triggers a specific set of knowledge queries:

```
                    Physical Safety         Cyber/Data           Operations
                    ---------------         ----------           ----------
                    Evac  Util  Haz   Asm   Blast Data  Run  OC  Vendor Cont
                    Route Ctrl  Mat   Pts   Rad   Inv   Book     Cntct  Plan
    Fire            [x]   [x]   [x]   [x]
    Earthquake      [x]   [x]   [x]   [x]                       [x]  [x]
    Active Threat   [x]               [x]
    Flood           [x]   [x]   [x]         	                       [x]
    Medical
    Cyberattack                             [x]   [x]   [x]  [x] [x]
    Data Breach                             [x]   [x]   [x]  [x]
    Outage                                  [x]         [x]  [x] [x]  [x]
    Weather         [x]               [x]                        [x]  [x]

    + Every scenario uses: Personnel Lookup, Emergency Resources,
      Past Incident Search, Drill Benchmarks, Missing Person Escalation
```
