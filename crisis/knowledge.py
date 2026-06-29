"""Organizational Knowledge Base — the context engine that makes FirstResponder intelligent.

Organizations upload their specific data (floor plans, personnel, resources, network topology)
and the agent uses this context during crises to give location-aware, people-aware,
infrastructure-aware guidance instead of generic playbook advice.
"""

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "firstresponder.db"


class KnowledgeBase:
    """Organizational knowledge store for context-aware crisis response."""

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
        return self._local.conn

    def _init_db(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS facilities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                address TEXT,
                floors INTEGER DEFAULT 1,
                total_capacity INTEGER,
                data JSON DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS zones (
                id TEXT PRIMARY KEY,
                facility_id TEXT NOT NULL REFERENCES facilities(id),
                name TEXT NOT NULL,
                floor INTEGER DEFAULT 1,
                zone_type TEXT DEFAULT 'general',
                primary_exit TEXT,
                alternate_exit TEXT,
                shelter_location TEXT,
                capacity INTEGER,
                notes TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS rooms (
                id TEXT PRIMARY KEY,
                zone_id TEXT REFERENCES zones(id),
                facility_id TEXT NOT NULL REFERENCES facilities(id),
                name TEXT NOT NULL,
                floor INTEGER DEFAULT 1,
                room_type TEXT DEFAULT 'general',
                capacity INTEGER,
                assigned_personnel TEXT DEFAULT '[]',
                notes TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS personnel (
                id TEXT PRIMARY KEY,
                slack_user_id TEXT,
                name TEXT NOT NULL,
                role TEXT,
                department TEXT,
                default_location TEXT,
                floor INTEGER,
                phone TEXT,
                emergency_contact_name TEXT,
                emergency_contact_phone TEXT,
                medical_notes TEXT DEFAULT '',
                mobility_limitations INTEGER DEFAULT 0,
                trained_first_aid INTEGER DEFAULT 0,
                trained_cpr INTEGER DEFAULT 0,
                is_floor_warden INTEGER DEFAULT 0,
                evacuation_role TEXT
            );

            CREATE TABLE IF NOT EXISTS emergency_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_id TEXT NOT NULL REFERENCES facilities(id),
                resource_type TEXT NOT NULL,
                location_description TEXT NOT NULL,
                floor INTEGER,
                zone_id TEXT REFERENCES zones(id),
                notes TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS network_assets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                ip_address TEXT,
                location TEXT,
                criticality TEXT DEFAULT 'medium',
                dependencies TEXT DEFAULT '[]',
                owner TEXT,
                notes TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS vendor_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_name TEXT NOT NULL,
                service TEXT NOT NULL,
                contact_name TEXT,
                contact_phone TEXT,
                contact_email TEXT,
                escalation_procedure TEXT DEFAULT '',
                sla_hours INTEGER,
                notes TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS evacuation_routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_id TEXT NOT NULL REFERENCES facilities(id),
                name TEXT NOT NULL,
                from_zone TEXT,
                to_exit TEXT NOT NULL,
                route_description TEXT NOT NULL,
                accessibility TEXT DEFAULT 'standard',
                blocked_by_zones TEXT DEFAULT '[]',
                notes TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS drill_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_id TEXT REFERENCES facilities(id),
                drill_type TEXT NOT NULL,
                date TEXT NOT NULL,
                total_evacuation_seconds INTEGER,
                full_accountability_seconds INTEGER,
                participants INTEGER,
                slowest_zone TEXT,
                issues_noted TEXT DEFAULT '',
                notes TEXT DEFAULT ''
            );

            -- === PHYSICAL SAFETY LAYER ===

            CREATE TABLE IF NOT EXISTS utility_controls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_id TEXT NOT NULL REFERENCES facilities(id),
                utility_type TEXT NOT NULL,
                location_description TEXT NOT NULL,
                floor INTEGER,
                zone_id TEXT REFERENCES zones(id),
                shutoff_instructions TEXT DEFAULT '',
                requires_key INTEGER DEFAULT 0,
                key_location TEXT DEFAULT '',
                notes TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS assembly_points (
                id TEXT PRIMARY KEY,
                facility_id TEXT NOT NULL REFERENCES facilities(id),
                name TEXT NOT NULL,
                location_description TEXT NOT NULL,
                capacity INTEGER DEFAULT 0,
                is_primary INTEGER DEFAULT 1,
                alternate_point_id TEXT,
                accessibility TEXT DEFAULT 'standard',
                notes TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS hazmat_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_id TEXT NOT NULL REFERENCES facilities(id),
                material_name TEXT NOT NULL,
                hazard_class TEXT NOT NULL,
                location_description TEXT NOT NULL,
                floor INTEGER,
                zone_id TEXT REFERENCES zones(id),
                quantity TEXT DEFAULT '',
                sds_location TEXT DEFAULT '',
                containment_instructions TEXT DEFAULT '',
                notes TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS nearby_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_type TEXT NOT NULL,
                name TEXT NOT NULL,
                address TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                distance_miles REAL,
                eta_minutes INTEGER,
                trauma_level TEXT DEFAULT '',
                helipad INTEGER DEFAULT 0,
                notes TEXT DEFAULT ''
            );

            -- === CYBER / DATA LAYER ===

            CREATE TABLE IF NOT EXISTS data_inventory (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                data_classification TEXT NOT NULL,
                storage_system TEXT NOT NULL,
                record_count TEXT DEFAULT '',
                pii_fields TEXT DEFAULT '[]',
                regulatory_frameworks TEXT DEFAULT '[]',
                backup_location TEXT DEFAULT '',
                backup_frequency TEXT DEFAULT '',
                retention_policy TEXT DEFAULT '',
                data_owner TEXT DEFAULT '',
                notification_requirements TEXT DEFAULT '',
                notes TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS runbooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                scenario_type TEXT NOT NULL,
                system_or_service TEXT DEFAULT '',
                severity TEXT DEFAULT 'medium',
                steps TEXT NOT NULL DEFAULT '[]',
                estimated_minutes INTEGER DEFAULT 0,
                last_tested TEXT DEFAULT '',
                owner TEXT DEFAULT '',
                notes TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS on_call_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name TEXT NOT NULL,
                service TEXT NOT NULL,
                primary_name TEXT NOT NULL,
                primary_slack_id TEXT DEFAULT '',
                primary_phone TEXT DEFAULT '',
                secondary_name TEXT DEFAULT '',
                secondary_slack_id TEXT DEFAULT '',
                secondary_phone TEXT DEFAULT '',
                escalation_manager TEXT DEFAULT '',
                escalation_phone TEXT DEFAULT '',
                schedule_notes TEXT DEFAULT ''
            );

            -- === WEATHER / CONTINUITY LAYER ===

            CREATE TABLE IF NOT EXISTS continuity_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_type TEXT NOT NULL,
                plan_name TEXT NOT NULL,
                trigger_conditions TEXT DEFAULT '',
                actions TEXT NOT NULL DEFAULT '[]',
                remote_work_capable INTEGER DEFAULT 0,
                backup_facility TEXT DEFAULT '',
                critical_functions TEXT DEFAULT '[]',
                recovery_time_objective_hours INTEGER DEFAULT 0,
                notes TEXT DEFAULT ''
            );

            CREATE INDEX IF NOT EXISTS idx_rooms_zone ON rooms(zone_id);
            CREATE INDEX IF NOT EXISTS idx_rooms_floor ON rooms(floor);
            CREATE INDEX IF NOT EXISTS idx_personnel_location ON personnel(default_location);
            CREATE INDEX IF NOT EXISTS idx_resources_type ON emergency_resources(resource_type);
            CREATE INDEX IF NOT EXISTS idx_assets_type ON network_assets(asset_type);
            CREATE INDEX IF NOT EXISTS idx_utility_type ON utility_controls(utility_type);
            CREATE INDEX IF NOT EXISTS idx_hazmat_zone ON hazmat_locations(zone_id);
            CREATE INDEX IF NOT EXISTS idx_data_class ON data_inventory(data_classification);
            CREATE INDEX IF NOT EXISTS idx_runbooks_scenario ON runbooks(scenario_type);
            CREATE INDEX IF NOT EXISTS idx_oncall_service ON on_call_schedules(service);
            CREATE INDEX IF NOT EXISTS idx_continuity_scenario ON continuity_plans(scenario_type);
        """)
        self._conn.commit()

    # --- Facility & Zone Management ---

    def add_facility(self, facility_id: str, name: str, address: str = "",
                     floors: int = 1, capacity: int = 0):
        self._conn.execute(
            "INSERT OR REPLACE INTO facilities (id, name, address, floors, total_capacity) VALUES (?, ?, ?, ?, ?)",
            (facility_id, name, address, floors, capacity),
        )
        self._conn.commit()

    def add_zone(self, zone_id: str, facility_id: str, name: str, floor: int = 1,
                 zone_type: str = "general", primary_exit: str = "", alternate_exit: str = "",
                 shelter_location: str = "", capacity: int = 0, notes: str = ""):
        self._conn.execute(
            """INSERT OR REPLACE INTO zones
               (id, facility_id, name, floor, zone_type, primary_exit, alternate_exit,
                shelter_location, capacity, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (zone_id, facility_id, name, floor, zone_type, primary_exit, alternate_exit,
             shelter_location, capacity, notes),
        )
        self._conn.commit()

    def add_room(self, room_id: str, facility_id: str, name: str, floor: int = 1,
                 zone_id: str = None, room_type: str = "general", capacity: int = 0,
                 assigned_personnel: list[str] = None, notes: str = ""):
        self._conn.execute(
            """INSERT OR REPLACE INTO rooms
               (id, facility_id, name, floor, zone_id, room_type, capacity, assigned_personnel, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (room_id, facility_id, name, floor, zone_id, room_type, capacity,
             json.dumps(assigned_personnel or []), notes),
        )
        self._conn.commit()

    # --- Personnel ---

    def add_person(self, person_id: str, name: str, slack_user_id: str = None,
                   role: str = "", department: str = "", default_location: str = "",
                   floor: int = 1, phone: str = "",
                   emergency_contact_name: str = "", emergency_contact_phone: str = "",
                   medical_notes: str = "", mobility_limitations: bool = False,
                   trained_first_aid: bool = False, trained_cpr: bool = False,
                   is_floor_warden: bool = False, evacuation_role: str = ""):
        self._conn.execute(
            """INSERT OR REPLACE INTO personnel
               (id, name, slack_user_id, role, department, default_location, floor, phone,
                emergency_contact_name, emergency_contact_phone, medical_notes,
                mobility_limitations, trained_first_aid, trained_cpr, is_floor_warden, evacuation_role)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (person_id, name, slack_user_id, role, department, default_location, floor, phone,
             emergency_contact_name, emergency_contact_phone, medical_notes,
             int(mobility_limitations), int(trained_first_aid), int(trained_cpr),
             int(is_floor_warden), evacuation_role),
        )
        self._conn.commit()

    # --- Emergency Resources ---

    def add_emergency_resource(self, facility_id: str, resource_type: str,
                               location_description: str, floor: int = 1,
                               zone_id: str = None, notes: str = ""):
        self._conn.execute(
            """INSERT INTO emergency_resources
               (facility_id, resource_type, location_description, floor, zone_id, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (facility_id, resource_type, location_description, floor, zone_id, notes),
        )
        self._conn.commit()

    # --- Network Assets ---

    def add_network_asset(self, asset_id: str, name: str, asset_type: str,
                          ip_address: str = "", location: str = "", criticality: str = "medium",
                          dependencies: list[str] = None, owner: str = "", notes: str = ""):
        self._conn.execute(
            """INSERT OR REPLACE INTO network_assets
               (id, name, asset_type, ip_address, location, criticality, dependencies, owner, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (asset_id, name, asset_type, ip_address, location, criticality,
             json.dumps(dependencies or []), owner, notes),
        )
        self._conn.commit()

    # --- Vendor Contacts ---

    def add_vendor_contact(self, vendor_name: str, service: str, contact_name: str = "",
                           contact_phone: str = "", contact_email: str = "",
                           escalation_procedure: str = "", sla_hours: int = 0, notes: str = ""):
        self._conn.execute(
            """INSERT INTO vendor_contacts
               (vendor_name, service, contact_name, contact_phone, contact_email,
                escalation_procedure, sla_hours, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (vendor_name, service, contact_name, contact_phone, contact_email,
             escalation_procedure, sla_hours, notes),
        )
        self._conn.commit()

    # --- Evacuation Routes ---

    def add_evacuation_route(self, facility_id: str, name: str, to_exit: str,
                             route_description: str, from_zone: str = "",
                             accessibility: str = "standard",
                             blocked_by_zones: list[str] = None, notes: str = ""):
        self._conn.execute(
            """INSERT INTO evacuation_routes
               (facility_id, name, from_zone, to_exit, route_description,
                accessibility, blocked_by_zones, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (facility_id, name, from_zone, to_exit, route_description,
             accessibility, json.dumps(blocked_by_zones or []), notes),
        )
        self._conn.commit()

    # --- Drill History ---

    def add_drill(self, drill_type: str, date: str, total_evacuation_seconds: int,
                  full_accountability_seconds: int = 0, participants: int = 0,
                  slowest_zone: str = "", issues_noted: str = "", facility_id: str = None,
                  notes: str = ""):
        self._conn.execute(
            """INSERT INTO drill_history
               (facility_id, drill_type, date, total_evacuation_seconds,
                full_accountability_seconds, participants, slowest_zone, issues_noted, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (facility_id, drill_type, date, total_evacuation_seconds,
             full_accountability_seconds, participants, slowest_zone, issues_noted, notes),
        )
        self._conn.commit()

    # --- Assembly Points ---

    def add_assembly_point(self, point_id: str, facility_id: str, name: str,
                           location_description: str, capacity: int = 0,
                           is_primary: bool = True, alternate_point_id: str = None,
                           accessibility: str = "standard", notes: str = ""):
        self._conn.execute(
            """INSERT OR REPLACE INTO assembly_points
               (id, facility_id, name, location_description, capacity, is_primary,
                alternate_point_id, accessibility, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (point_id, facility_id, name, location_description, capacity,
             int(is_primary), alternate_point_id, accessibility, notes),
        )
        self._conn.commit()

    # --- Query Methods (used by AI agent during crises) ---

    def get_evacuation_guidance(self, threat_location: str = "", floor: int = None) -> dict:
        """Get evacuation guidance based on where the threat is."""
        conn = self._conn

        # Get all zones
        zones = [dict(r) for r in conn.execute("SELECT * FROM zones").fetchall()]

        # Get evacuation routes
        routes = [dict(r) for r in conn.execute("SELECT * FROM evacuation_routes").fetchall()]

        # Filter routes blocked by the threat zone
        safe_routes = []
        blocked_routes = []
        for route in routes:
            blocked_zones = json.loads(route.get("blocked_by_zones", "[]"))
            if threat_location and threat_location in blocked_zones:
                blocked_routes.append(route)
            else:
                safe_routes.append(route)

        # Get people with mobility limitations
        mobility = [dict(r) for r in conn.execute(
            "SELECT name, default_location, floor FROM personnel WHERE mobility_limitations = 1"
        ).fetchall()]

        # Get floor wardens
        wardens = [dict(r) for r in conn.execute(
            "SELECT name, default_location, floor, slack_user_id FROM personnel WHERE is_floor_warden = 1"
        ).fetchall()]

        return {
            "zones": zones,
            "safe_routes": safe_routes,
            "blocked_routes": blocked_routes,
            "mobility_limited_personnel": mobility,
            "floor_wardens": wardens,
        }

    def get_nearby_resources(self, location: str = "", resource_type: str = None,
                             floor: int = None) -> list[dict]:
        """Find emergency resources near a location."""
        query = "SELECT * FROM emergency_resources WHERE 1=1"
        params = []

        if resource_type:
            query += " AND resource_type = ?"
            params.append(resource_type)
        if floor is not None:
            query += " AND floor = ?"
            params.append(floor)

        return [dict(r) for r in self._conn.execute(query, params).fetchall()]

    def get_personnel_in_zone(self, zone_id: str = None, floor: int = None) -> list[dict]:
        """Get personnel assigned to a zone or floor."""
        query = "SELECT * FROM personnel WHERE 1=1"
        params = []

        if zone_id:
            query += " AND default_location = ?"
            params.append(zone_id)
        if floor is not None:
            query += " AND floor = ?"
            params.append(floor)

        return [dict(r) for r in self._conn.execute(query, params).fetchall()]

    def get_personnel_by_slack_id(self, slack_user_id: str) -> dict | None:
        """Look up a person by their Slack user ID."""
        row = self._conn.execute(
            "SELECT * FROM personnel WHERE slack_user_id = ?", (slack_user_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_affected_systems(self, asset_id: str) -> list[dict]:
        """Get systems that depend on a compromised asset (blast radius)."""
        # Direct dependencies
        asset = self._conn.execute(
            "SELECT * FROM network_assets WHERE id = ?", (asset_id,)
        ).fetchone()

        if not asset:
            return []

        # Find all assets that list this one as a dependency
        all_assets = [dict(r) for r in self._conn.execute("SELECT * FROM network_assets").fetchall()]
        affected = []
        for a in all_assets:
            deps = json.loads(a.get("dependencies", "[]"))
            if asset_id in deps:
                affected.append(a)

        return affected

    def get_vendor_for_service(self, service: str) -> list[dict]:
        """Find vendor contacts for a service."""
        return [dict(r) for r in self._conn.execute(
            "SELECT * FROM vendor_contacts WHERE service LIKE ?", (f"%{service}%",)
        ).fetchall()]

    def get_drill_performance(self, drill_type: str = None) -> list[dict]:
        """Get past drill performance data."""
        if drill_type:
            rows = self._conn.execute(
                "SELECT * FROM drill_history WHERE drill_type = ? ORDER BY date DESC LIMIT 10",
                (drill_type,)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM drill_history ORDER BY date DESC LIMIT 10"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_first_aid_trained(self) -> list[dict]:
        """Get all personnel trained in first aid or CPR."""
        return [dict(r) for r in self._conn.execute(
            "SELECT name, slack_user_id, default_location, floor, trained_first_aid, trained_cpr "
            "FROM personnel WHERE trained_first_aid = 1 OR trained_cpr = 1"
        ).fetchall()]

    # --- Physical Safety Queries ---

    def get_utility_controls(self, utility_type: str = None, zone_id: str = None,
                             floor: int = None) -> list[dict]:
        """Find utility shutoff controls (gas, electric, water, HVAC)."""
        query = "SELECT * FROM utility_controls WHERE 1=1"
        params = []
        if utility_type:
            query += " AND utility_type = ?"
            params.append(utility_type)
        if zone_id:
            query += " AND zone_id = ?"
            params.append(zone_id)
        if floor is not None:
            query += " AND floor = ?"
            params.append(floor)
        return [dict(r) for r in self._conn.execute(query, params).fetchall()]

    def get_assembly_points(self, facility_id: str = None) -> list[dict]:
        """Get designated assembly/rally points."""
        if facility_id:
            rows = self._conn.execute(
                "SELECT * FROM assembly_points WHERE facility_id = ? ORDER BY is_primary DESC",
                (facility_id,)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM assembly_points ORDER BY is_primary DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_hazmat_near_threat(self, zone_id: str = None, floor: int = None) -> list[dict]:
        """Find hazardous materials near a threat zone."""
        query = "SELECT * FROM hazmat_locations WHERE 1=1"
        params = []
        if zone_id:
            query += " AND zone_id = ?"
            params.append(zone_id)
        if floor is not None:
            query += " AND floor = ?"
            params.append(floor)
        return [dict(r) for r in self._conn.execute(query, params).fetchall()]

    def get_nearby_emergency_services(self, service_type: str = None) -> list[dict]:
        """Get nearby hospitals, fire stations, police stations."""
        if service_type:
            rows = self._conn.execute(
                "SELECT * FROM nearby_services WHERE service_type = ? ORDER BY eta_minutes ASC",
                (service_type,)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM nearby_services ORDER BY service_type, eta_minutes ASC"
            ).fetchall()
        return [dict(r) for r in rows]

    # --- Cyber / Data Queries ---

    def get_data_at_risk(self, storage_system: str) -> list[dict]:
        """Find what sensitive data lives on a compromised system."""
        return [dict(r) for r in self._conn.execute(
            "SELECT * FROM data_inventory WHERE storage_system LIKE ?",
            (f"%{storage_system}%",)
        ).fetchall()]

    def get_data_by_classification(self, classification: str) -> list[dict]:
        """Get all data assets of a given classification level."""
        return [dict(r) for r in self._conn.execute(
            "SELECT * FROM data_inventory WHERE data_classification = ?",
            (classification,)
        ).fetchall()]

    def get_runbook(self, scenario_type: str = None, system: str = None) -> list[dict]:
        """Find runbooks for a scenario or system."""
        query = "SELECT * FROM runbooks WHERE 1=1"
        params = []
        if scenario_type:
            query += " AND scenario_type = ?"
            params.append(scenario_type)
        if system:
            query += " AND system_or_service LIKE ?"
            params.append(f"%{system}%")
        query += " ORDER BY severity DESC"
        return [dict(r) for r in self._conn.execute(query, params).fetchall()]

    def get_on_call(self, service: str = None) -> list[dict]:
        """Get current on-call rotation for a service."""
        if service:
            rows = self._conn.execute(
                "SELECT * FROM on_call_schedules WHERE service LIKE ?",
                (f"%{service}%",)
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM on_call_schedules").fetchall()
        return [dict(r) for r in rows]

    # --- Continuity Queries ---

    def get_continuity_plan(self, scenario_type: str) -> list[dict]:
        """Get business continuity plan for a scenario type."""
        return [dict(r) for r in self._conn.execute(
            "SELECT * FROM continuity_plans WHERE scenario_type = ?",
            (scenario_type,)
        ).fetchall()]

    # --- Summary ---

    def get_facility_summary(self) -> dict:
        """Get a summary of all organizational knowledge loaded."""
        conn = self._conn

        def _count(table):
            return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

        return {
            "facilities": _count("facilities"),
            "zones": _count("zones"),
            "rooms": _count("rooms"),
            "personnel": _count("personnel"),
            "emergency_resources": _count("emergency_resources"),
            "network_assets": _count("network_assets"),
            "vendor_contacts": _count("vendor_contacts"),
            "evacuation_routes": _count("evacuation_routes"),
            "drills_recorded": _count("drill_history"),
            "utility_controls": _count("utility_controls"),
            "assembly_points": _count("assembly_points"),
            "hazmat_locations": _count("hazmat_locations"),
            "nearby_services": _count("nearby_services"),
            "data_inventory": _count("data_inventory"),
            "runbooks": _count("runbooks"),
            "on_call_schedules": _count("on_call_schedules"),
            "continuity_plans": _count("continuity_plans"),
            "first_aid_trained": conn.execute("SELECT COUNT(*) FROM personnel WHERE trained_first_aid = 1").fetchone()[0],
            "cpr_trained": conn.execute("SELECT COUNT(*) FROM personnel WHERE trained_cpr = 1").fetchone()[0],
            "mobility_limited": conn.execute("SELECT COUNT(*) FROM personnel WHERE mobility_limitations = 1").fetchone()[0],
            "floor_wardens": conn.execute("SELECT COUNT(*) FROM personnel WHERE is_floor_warden = 1").fetchone()[0],
        }


# Singleton
knowledge_base = KnowledgeBase()
