"""Persistent incident store using SQLite.

Stores all incidents, check-ins, SITREPs, timeline events, and lessons learned.
The agent can query past incidents to learn from them and make recommendations.
"""

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from crisis.models import (
    CheckIn,
    Crisis,
    CrisisSeverity,
    CrisisStatus,
    CRISIS_TYPES,
    SitRep,
)

DB_PATH = Path(__file__).parent.parent / "data" / "firstresponder.db"


class IncidentStore:
    """SQLite-backed persistent incident store with learning capabilities."""

    def __init__(self, db_path: Path = DB_PATH):
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()

    @property
    def _conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(str(self._db_path))
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
        return self._local.conn

    def _init_db(self):
        conn = self._conn
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                crisis_type TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL,
                channel_id TEXT,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                resolved_at TEXT,
                incident_commander TEXT,
                duration_minutes INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT NOT NULL REFERENCES incidents(id),
                user_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'safe',
                note TEXT DEFAULT '',
                timestamp TEXT NOT NULL,
                UNIQUE(incident_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS timeline_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT NOT NULL REFERENCES incidents(id),
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                user_id TEXT DEFAULT 'system',
                timestamp TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sitreps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT NOT NULL REFERENCES incidents(id),
                number INTEGER NOT NULL,
                summary TEXT NOT NULL,
                checked_in_count INTEGER DEFAULT 0,
                missing_count INTEGER DEFAULT 0,
                actions_taken TEXT DEFAULT '[]',
                timestamp TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS lessons_learned (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT NOT NULL REFERENCES incidents(id),
                lesson TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS roster (
                incident_id TEXT NOT NULL REFERENCES incidents(id),
                user_id TEXT NOT NULL,
                PRIMARY KEY(incident_id, user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_incidents_type ON incidents(crisis_type);
            CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
            CREATE INDEX IF NOT EXISTS idx_lessons_category ON lessons_learned(category);
            CREATE INDEX IF NOT EXISTS idx_timeline_incident ON timeline_events(incident_id);
        """)
        conn.commit()

    def save_incident(self, crisis: Crisis):
        conn = self._conn
        conn.execute(
            """INSERT OR REPLACE INTO incidents
               (id, crisis_type, description, severity, status, channel_id,
                created_by, created_at, resolved_at, incident_commander, duration_minutes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                crisis.id,
                crisis.crisis_type,
                crisis.description,
                crisis.severity.value,
                crisis.status.value,
                crisis.channel_id,
                crisis.created_by,
                crisis.created_at.isoformat(),
                crisis.resolved_at.isoformat() if crisis.resolved_at else None,
                crisis.incident_commander,
                crisis.duration_minutes,
            ),
        )
        conn.commit()

    def save_checkin(self, incident_id: str, checkin: CheckIn):
        conn = self._conn
        conn.execute(
            """INSERT OR REPLACE INTO checkins
               (incident_id, user_id, status, note, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (incident_id, checkin.user_id, checkin.status, checkin.note, checkin.timestamp.isoformat()),
        )
        conn.commit()

    def save_timeline_event(self, incident_id: str, event: dict):
        conn = self._conn
        conn.execute(
            """INSERT INTO timeline_events
               (incident_id, event_type, description, user_id, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (incident_id, event["type"], event["description"], event["user_id"], event["timestamp"]),
        )
        conn.commit()

    def save_sitrep(self, incident_id: str, sitrep: SitRep):
        conn = self._conn
        conn.execute(
            """INSERT INTO sitreps
               (incident_id, number, summary, checked_in_count, missing_count, actions_taken, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                incident_id,
                sitrep.number,
                sitrep.summary,
                len(sitrep.checked_in),
                len(sitrep.missing),
                json.dumps(sitrep.actions_taken),
                sitrep.timestamp.isoformat(),
            ),
        )
        conn.commit()

    def save_roster(self, incident_id: str, user_ids: list[str]):
        conn = self._conn
        for uid in user_ids:
            conn.execute(
                "INSERT OR IGNORE INTO roster (incident_id, user_id) VALUES (?, ?)",
                (incident_id, uid),
            )
        conn.commit()

    def add_lesson_learned(self, incident_id: str, lesson: str, category: str = "general"):
        conn = self._conn
        conn.execute(
            """INSERT INTO lessons_learned (incident_id, lesson, category, created_at)
               VALUES (?, ?, ?, ?)""",
            (incident_id, lesson, category, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()

    # --- Query methods for the AI agent ---

    def get_past_incidents_by_type(self, crisis_type: str, limit: int = 10) -> list[dict]:
        cursor = self._conn.execute(
            """SELECT id, crisis_type, description, severity, status,
                      duration_minutes, created_at, resolved_at
               FROM incidents
               WHERE crisis_type = ? AND status = 'resolved'
               ORDER BY created_at DESC LIMIT ?""",
            (crisis_type, limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_lessons_for_type(self, crisis_type: str) -> list[dict]:
        cursor = self._conn.execute(
            """SELECT l.lesson, l.category, i.crisis_type, i.description
               FROM lessons_learned l
               JOIN incidents i ON l.incident_id = i.id
               WHERE i.crisis_type = ?
               ORDER BY l.created_at DESC""",
            (crisis_type,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_all_lessons(self, limit: int = 50) -> list[dict]:
        cursor = self._conn.execute(
            """SELECT l.lesson, l.category, i.crisis_type, i.description, i.id as incident_id
               FROM lessons_learned l
               JOIN incidents i ON l.incident_id = i.id
               ORDER BY l.created_at DESC LIMIT ?""",
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_incident_stats(self) -> dict:
        conn = self._conn
        total = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        resolved = conn.execute("SELECT COUNT(*) FROM incidents WHERE status = 'resolved'").fetchone()[0]
        active = conn.execute("SELECT COUNT(*) FROM incidents WHERE status = 'active'").fetchone()[0]

        avg_duration = conn.execute(
            "SELECT AVG(duration_minutes) FROM incidents WHERE status = 'resolved'"
        ).fetchone()[0]

        by_type = {}
        cursor = conn.execute(
            "SELECT crisis_type, COUNT(*) as count FROM incidents GROUP BY crisis_type"
        )
        for row in cursor:
            by_type[row["crisis_type"]] = row["count"]

        avg_checkin_rate = conn.execute(
            """SELECT AVG(CAST(checkin_count AS FLOAT) / NULLIF(roster_count, 0))
               FROM (
                   SELECT i.id,
                          (SELECT COUNT(*) FROM checkins c WHERE c.incident_id = i.id) as checkin_count,
                          (SELECT COUNT(*) FROM roster r WHERE r.incident_id = i.id) as roster_count
                   FROM incidents i WHERE i.status = 'resolved'
               )"""
        ).fetchone()[0]

        return {
            "total_incidents": total,
            "resolved": resolved,
            "active": active,
            "avg_duration_minutes": round(avg_duration or 0, 1),
            "avg_checkin_rate": round((avg_checkin_rate or 0) * 100, 1),
            "by_type": by_type,
            "total_lessons": conn.execute("SELECT COUNT(*) FROM lessons_learned").fetchone()[0],
        }

    def search_incidents(self, query: str, limit: int = 10) -> list[dict]:
        cursor = self._conn.execute(
            """SELECT id, crisis_type, description, severity, status,
                      duration_minutes, created_at
               FROM incidents
               WHERE description LIKE ? OR crisis_type LIKE ?
               ORDER BY created_at DESC LIMIT ?""",
            (f"%{query}%", f"%{query}%", limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_response_patterns(self, crisis_type: str) -> dict:
        """Analyze past incidents to find what worked and what didn't."""
        incidents = self.get_past_incidents_by_type(crisis_type, limit=20)
        lessons = self.get_lessons_for_type(crisis_type)

        if not incidents:
            return {"has_data": False, "message": f"No past {crisis_type} incidents to learn from."}

        durations = [i["duration_minutes"] for i in incidents if i["duration_minutes"]]
        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "has_data": True,
            "past_incident_count": len(incidents),
            "avg_resolution_minutes": round(avg_duration, 1),
            "lessons": [l["lesson"] for l in lessons],
            "recent_incidents": [
                {"id": i["id"], "description": i["description"], "duration": i["duration_minutes"]}
                for i in incidents[:3]
            ],
        }


# Singleton
incident_store = IncidentStore()
