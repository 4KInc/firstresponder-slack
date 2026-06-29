import threading
from datetime import datetime, timezone

from crisis.models import (
    CheckIn,
    Crisis,
    CrisisSeverity,
    CrisisStatus,
    CRISIS_TYPES,
    SitRep,
)
from crisis.store import incident_store


class CrisisManager:
    """Thread-safe crisis state manager with persistent storage and learning."""

    def __init__(self):
        self._crises: dict[str, Crisis] = {}  # id -> Crisis (active in memory)
        self._channel_map: dict[str, str] = {}  # channel_id -> crisis_id
        self._lock = threading.Lock()
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        return f"INC-{ts}-{self._counter:03d}"

    def start_crisis(
        self,
        crisis_type: str,
        description: str,
        channel_id: str,
        created_by: str,
        severity: CrisisSeverity | None = None,
    ) -> Crisis:
        crisis_info = CRISIS_TYPES.get(crisis_type, CRISIS_TYPES["other"])

        with self._lock:
            crisis_id = self._next_id()
            crisis = Crisis(
                id=crisis_id,
                crisis_type=crisis_type,
                description=description,
                severity=severity or crisis_info["default_severity"],
                status=CrisisStatus.ACTIVE,
                channel_id=channel_id,
                created_by=created_by,
            )
            crisis.add_timeline_event(
                "crisis_started",
                f"Crisis declared: {crisis_info['label']} — {description}",
                created_by,
            )
            self._crises[crisis_id] = crisis
            self._channel_map[channel_id] = crisis_id

        # Persist to SQLite
        incident_store.save_incident(crisis)
        incident_store.save_timeline_event(crisis_id, crisis.timeline[-1])

        return crisis

    def get_crisis(self, crisis_id: str) -> Crisis | None:
        with self._lock:
            return self._crises.get(crisis_id)

    def get_crisis_by_channel(self, channel_id: str) -> Crisis | None:
        with self._lock:
            crisis_id = self._channel_map.get(channel_id)
            if crisis_id:
                return self._crises.get(crisis_id)
            return None

    def get_active_crises(self) -> list[Crisis]:
        with self._lock:
            return [c for c in self._crises.values() if c.status == CrisisStatus.ACTIVE]

    def check_in(self, crisis_id: str, user_id: str, status: str = "safe", note: str = "") -> CheckIn | None:
        with self._lock:
            crisis = self._crises.get(crisis_id)
            if not crisis or crisis.status == CrisisStatus.RESOLVED:
                return None
            checkin = CheckIn(user_id=user_id, status=status, note=note)
            crisis.check_ins[user_id] = checkin
            crisis.add_timeline_event("check_in", f"<@{user_id}> checked in: {status}", user_id)

        # Persist
        incident_store.save_checkin(crisis_id, checkin)
        incident_store.save_timeline_event(crisis_id, crisis.timeline[-1])

        return checkin

    def set_incident_commander(self, crisis_id: str, user_id: str) -> bool:
        with self._lock:
            crisis = self._crises.get(crisis_id)
            if not crisis:
                return False
            crisis.incident_commander = user_id
            crisis.add_timeline_event("role_assigned", f"<@{user_id}> assigned as Incident Commander", user_id)

        incident_store.save_incident(crisis)
        incident_store.save_timeline_event(crisis_id, crisis.timeline[-1])
        return True

    def add_to_roster(self, crisis_id: str, user_ids: list[str]) -> bool:
        with self._lock:
            crisis = self._crises.get(crisis_id)
            if not crisis:
                return False
            for uid in user_ids:
                if uid not in crisis.team_roster:
                    crisis.team_roster.append(uid)

        incident_store.save_roster(crisis_id, user_ids)
        return True

    def resolve_crisis(self, crisis_id: str, resolved_by: str) -> Crisis | None:
        with self._lock:
            crisis = self._crises.get(crisis_id)
            if not crisis:
                return None
            crisis.status = CrisisStatus.RESOLVED
            crisis.resolved_at = datetime.now(timezone.utc)
            crisis.add_timeline_event("crisis_resolved", "Crisis resolved", resolved_by)
            if crisis.channel_id in self._channel_map:
                del self._channel_map[crisis.channel_id]

        # Persist final state
        incident_store.save_incident(crisis)
        incident_store.save_timeline_event(crisis_id, crisis.timeline[-1])

        return crisis

    def add_sitrep(self, crisis_id: str, summary: str, actions_taken: list[str]) -> SitRep | None:
        with self._lock:
            crisis = self._crises.get(crisis_id)
            if not crisis:
                return None
            sitrep = SitRep(
                number=len(crisis.sitreps) + 1,
                timestamp=datetime.now(timezone.utc),
                summary=summary,
                checked_in=list(crisis.check_ins.keys()),
                missing=crisis.missing_checkins,
                actions_taken=actions_taken,
            )
            crisis.sitreps.append(sitrep)
            crisis.add_timeline_event("sitrep", f"SITREP #{sitrep.number} generated")

        # Persist
        incident_store.save_sitrep(crisis_id, sitrep)
        incident_store.save_timeline_event(crisis_id, crisis.timeline[-1])

        return sitrep

    def add_lesson_learned(self, crisis_id: str, lesson: str, category: str = "general"):
        """Store a lesson learned from a resolved incident."""
        incident_store.add_lesson_learned(crisis_id, lesson, category)

    def get_past_context(self, crisis_type: str) -> dict:
        """Get intelligence from past incidents of the same type."""
        return incident_store.get_response_patterns(crisis_type)

    def get_all_lessons(self) -> list[dict]:
        """Get all lessons learned across all incidents."""
        return incident_store.get_all_lessons()

    def get_stats(self) -> dict:
        """Get aggregate statistics across all incidents."""
        return incident_store.get_incident_stats()

    def search_past_incidents(self, query: str) -> list[dict]:
        """Search past incidents by keyword."""
        return incident_store.search_incidents(query)

    def generate_after_action_report(self, crisis_id: str) -> str | None:
        with self._lock:
            crisis = self._crises.get(crisis_id)
            if not crisis:
                return None

        crisis_info = CRISIS_TYPES.get(crisis.crisis_type, CRISIS_TYPES["other"])

        # Get intelligence from past incidents
        past_context = self.get_past_context(crisis.crisis_type)

        lines = [
            f"# After-Action Report: {crisis.id}",
            f"**Type:** {crisis_info['label']}",
            f"**Severity:** {crisis.severity.value.upper()}",
            f"**Status:** {crisis.status.value.upper()}",
            f"**Duration:** {crisis.duration_minutes} minutes",
            f"**Started:** {crisis.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        ]

        if crisis.resolved_at:
            lines.append(f"**Resolved:** {crisis.resolved_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        if crisis.incident_commander:
            lines.append(f"**Incident Commander:** <@{crisis.incident_commander}>")

        lines.append(f"\n**Description:** {crisis.description}")

        # Compare to past performance
        if past_context.get("has_data"):
            avg = past_context["avg_resolution_minutes"]
            count = past_context["past_incident_count"]
            lines.append(f"\n## Comparison to Past Incidents")
            lines.append(f"- Past {crisis_info['label']} incidents: {count}")
            lines.append(f"- Average resolution time: {avg} minutes")
            if crisis.duration_minutes < avg:
                lines.append(f"- *This incident was resolved {round(avg - crisis.duration_minutes)} minutes faster than average*")
            else:
                lines.append(f"- *This incident took {round(crisis.duration_minutes - avg)} minutes longer than average*")

        lines.append(f"\n## Personnel Accountability")
        lines.append(f"- **Roster size:** {len(crisis.team_roster)}")
        lines.append(f"- **Checked in:** {len(crisis.check_ins)}")
        lines.append(f"- **Missing:** {len(crisis.missing_checkins)}")

        if crisis.check_ins:
            lines.append("\n**Check-ins:**")
            for uid, ci in crisis.check_ins.items():
                lines.append(f"- <@{uid}>: {ci.status} ({ci.timestamp.strftime('%H:%M:%S UTC')})")

        if crisis.missing_checkins:
            lines.append("\n**Not checked in:**")
            for uid in crisis.missing_checkins:
                lines.append(f"- <@{uid}>")

        lines.append(f"\n## Timeline ({len(crisis.timeline)} events)")
        for event in crisis.timeline:
            lines.append(f"- `{event['timestamp']}` [{event['type']}] {event['description']}")

        if crisis.sitreps:
            lines.append(f"\n## Situation Reports ({len(crisis.sitreps)})")
            for sr in crisis.sitreps:
                lines.append(f"\n### SITREP #{sr.number} — {sr.timestamp.strftime('%H:%M:%S UTC')}")
                lines.append(sr.summary)

        # Past lessons learned for this crisis type
        if past_context.get("has_data") and past_context.get("lessons"):
            lines.append(f"\n## Lessons from Past {crisis_info['label']} Incidents")
            for lesson in past_context["lessons"][:5]:
                lines.append(f"- {lesson}")

        return "\n".join(lines)


# Singleton instance
crisis_manager = CrisisManager()
