from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class CrisisStatus(str, Enum):
    ACTIVE = "active"
    MONITORING = "monitoring"
    RESOLVED = "resolved"


class CrisisSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


CRISIS_TYPES = {
    "earthquake": {
        "label": "Earthquake",
        "emoji": "earth_americas",
        "default_severity": CrisisSeverity.CRITICAL,
        "playbook": "earthquake",
    },
    "fire": {
        "label": "Fire",
        "emoji": "fire",
        "default_severity": CrisisSeverity.CRITICAL,
        "playbook": "fire",
    },
    "flood": {
        "label": "Flood",
        "emoji": "ocean",
        "default_severity": CrisisSeverity.HIGH,
        "playbook": "flood",
    },
    "active-threat": {
        "label": "Active Threat",
        "emoji": "rotating_light",
        "default_severity": CrisisSeverity.CRITICAL,
        "playbook": "active_threat",
    },
    "cyberattack": {
        "label": "Cyber Attack",
        "emoji": "skull_and_crossbones",
        "default_severity": CrisisSeverity.CRITICAL,
        "playbook": "cyberattack",
    },
    "data-breach": {
        "label": "Data Breach",
        "emoji": "lock",
        "default_severity": CrisisSeverity.HIGH,
        "playbook": "data_breach",
    },
    "outage": {
        "label": "Service Outage",
        "emoji": "electric_plug",
        "default_severity": CrisisSeverity.HIGH,
        "playbook": "outage",
    },
    "weather": {
        "label": "Severe Weather",
        "emoji": "thunder_cloud_and_rain",
        "default_severity": CrisisSeverity.MEDIUM,
        "playbook": "weather",
    },
    "medical": {
        "label": "Medical Emergency",
        "emoji": "ambulance",
        "default_severity": CrisisSeverity.CRITICAL,
        "playbook": "medical",
    },
    "other": {
        "label": "Other Incident",
        "emoji": "warning",
        "default_severity": CrisisSeverity.MEDIUM,
        "playbook": "generic",
    },
}


@dataclass
class CheckIn:
    user_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "safe"
    note: str = ""


@dataclass
class SitRep:
    number: int
    timestamp: datetime
    summary: str
    checked_in: list[str]
    missing: list[str]
    actions_taken: list[str]


@dataclass
class Crisis:
    id: str
    crisis_type: str
    description: str
    severity: CrisisSeverity
    status: CrisisStatus
    channel_id: str
    created_by: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: datetime | None = None
    incident_commander: str | None = None
    check_ins: dict[str, CheckIn] = field(default_factory=dict)
    sitreps: list[SitRep] = field(default_factory=list)
    timeline: list[dict] = field(default_factory=list)
    team_roster: list[str] = field(default_factory=list)

    def add_timeline_event(self, event_type: str, description: str, user_id: str = "system"):
        self.timeline.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "description": description,
            "user_id": user_id,
        })

    @property
    def missing_checkins(self) -> list[str]:
        return [uid for uid in self.team_roster if uid not in self.check_ins]

    @property
    def duration_minutes(self) -> int:
        end = self.resolved_at or datetime.now(timezone.utc)
        return int((end - self.created_at).total_seconds() / 60)
