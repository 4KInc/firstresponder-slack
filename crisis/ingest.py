"""CSV ingestion engine - parses uploaded CSV files into the knowledge base.

Supports: facility, zones, rooms, personnel, emergency_resources,
evacuation_routes, assembly_points, nearby_services.

Each CSV type has its own parser that validates required columns
and loads rows into the SQLite knowledge base.
"""

import csv
import json
import io
from dataclasses import dataclass

from crisis.knowledge import knowledge_base as kb


@dataclass
class IngestResult:
    file_type: str
    rows_loaded: int
    rows_skipped: int
    errors: list[str]

    @property
    def success(self) -> bool:
        return self.rows_loaded > 0

    def summary(self) -> str:
        msg = f"*{self.file_type}*: {self.rows_loaded} rows loaded"
        if self.rows_skipped:
            msg += f", {self.rows_skipped} skipped"
        if self.errors:
            msg += f"\nErrors:\n" + "\n".join(f"- {e}" for e in self.errors[:5])
        return msg


# Required columns for each CSV type
SCHEMAS = {
    # Physical
    "facility": ["facility_id", "name"],
    "zones": ["zone_id", "facility_id", "name", "floor", "zone_type"],
    "rooms": ["room_id", "facility_id", "name", "floor"],
    "personnel": ["person_id", "name"],
    "emergency_resources": ["facility_id", "resource_type", "location_description"],
    "evacuation_routes": ["facility_id", "name", "to_exit", "route_description"],
    "assembly_points": ["point_id", "facility_id", "name", "location_description"],
    "nearby_services": ["service_type", "name"],
    "utility_controls": ["facility_id", "utility_type", "location_description"],
    "hazmat_locations": ["facility_id", "material_name", "hazard_class", "location_description"],
    "drills": ["drill_type", "date", "total_evacuation_seconds"],
    "vendor_contacts": ["vendor_name", "service"],
    # Cyber & operations
    "network_assets": ["asset_id", "name", "asset_type"],
    "data_inventory": ["data_id", "name", "data_classification", "storage_system"],
    "runbooks": ["title", "scenario_type", "steps"],
    "on_call_schedules": ["team_name", "service", "primary_name"],
    "continuity_plans": ["scenario_type", "plan_name", "actions"],
}


def _parse_bool(val: str) -> bool:
    return val.strip().lower() in ("true", "1", "yes", "y")


def _parse_int(val: str, default: int = 0) -> int:
    try:
        return int(val.strip())
    except (ValueError, TypeError):
        return default


def _parse_float(val: str, default: float = 0.0) -> float:
    try:
        return float(val.strip())
    except (ValueError, TypeError):
        return default


def _clear_facility_scope(table: str, rows: list[dict]) -> None:
    """Make re-upload idempotent for tables keyed only by an autoincrement id.

    These tables (emergency_resources, evacuation_routes, utility_controls,
    hazmat_locations) have no natural unique key, so a plain re-INSERT would
    duplicate every row. Before loading, we delete the existing rows for the
    facilities present in this upload - so re-uploading a corrected CSV replaces
    that facility's rows instead of appending duplicates. ``table`` is a fixed,
    code-supplied name (never user input), so interpolation here is safe.
    """
    fids = {r.get("facility_id", "").strip() for r in rows if r.get("facility_id", "").strip()}
    for fid in fids:
        kb._conn.execute(f"DELETE FROM {table} WHERE facility_id = ?", (fid,))
    if fids:
        kb._conn.commit()


def detect_csv_type(headers: list[str]) -> str | None:
    """Detect the CSV type based on column headers.

    Matches most-specific schema first (most required columns) to avoid
    false matches on generic columns like 'facility_id' and 'name'.
    """
    headers_set = set(h.strip().lower() for h in headers)

    # Sort by number of required columns descending - most specific first
    sorted_schemas = sorted(SCHEMAS.items(), key=lambda x: len(x[1]), reverse=True)

    for csv_type, required in sorted_schemas:
        if all(col in headers_set for col in required):
            return csv_type

    return None


def ingest_csv(content: str, filename: str = "") -> IngestResult:
    """Parse a CSV string and load it into the knowledge base.

    Auto-detects the CSV type from column headers.
    """
    # Strip a UTF-8 BOM - Excel and Google Sheets prepend one on export, which
    # would otherwise corrupt the first header (e.g. "﻿facility_id") and
    # break type detection.
    content = content.lstrip("﻿")

    reader = csv.DictReader(io.StringIO(content))

    if not reader.fieldnames:
        return IngestResult("unknown", 0, 0, ["Empty CSV or no headers found"])

    # Normalize headers (also strip any stray BOM left on the first field)
    headers = [h.strip().lstrip("﻿").lower() for h in reader.fieldnames]
    csv_type = detect_csv_type(headers)

    if not csv_type:
        return IngestResult(
            "unknown", 0, 0,
            [f"Could not detect CSV type from headers: {', '.join(headers)}",
             f"Supported types: {', '.join(SCHEMAS.keys())}",
             f"Check that your CSV has the required columns for one of these types."]
        )

    # Normalize the reader's fieldnames
    reader.fieldnames = headers

    parsers = {
        "facility": _ingest_facility,
        "zones": _ingest_zones,
        "rooms": _ingest_rooms,
        "personnel": _ingest_personnel,
        "emergency_resources": _ingest_emergency_resources,
        "evacuation_routes": _ingest_evacuation_routes,
        "assembly_points": _ingest_assembly_points,
        "nearby_services": _ingest_nearby_services,
        "utility_controls": _ingest_utility_controls,
        "hazmat_locations": _ingest_hazmat_locations,
        "network_assets": _ingest_network_assets,
        "data_inventory": _ingest_data_inventory,
        "runbooks": _ingest_runbooks,
        "on_call_schedules": _ingest_on_call_schedules,
        "continuity_plans": _ingest_continuity_plans,
        "drills": _ingest_drills,
        "vendor_contacts": _ingest_vendor_contacts,
    }

    return parsers[csv_type](reader, csv_type)


def _ingest_facility(reader, csv_type) -> IngestResult:
    loaded, skipped, errors = 0, 0, []
    for i, row in enumerate(reader, 2):
        try:
            kb.add_facility(
                row["facility_id"].strip(),
                row["name"].strip(),
                row.get("address", "").strip(),
                _parse_int(row.get("floors", "1")),
                _parse_int(row.get("capacity", "0")),
            )
            loaded += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")
            skipped += 1
    return IngestResult(csv_type, loaded, skipped, errors)


def _ingest_zones(reader, csv_type) -> IngestResult:
    loaded, skipped, errors = 0, 0, []
    for i, row in enumerate(reader, 2):
        try:
            kb.add_zone(
                row["zone_id"].strip(),
                row["facility_id"].strip(),
                row["name"].strip(),
                _parse_int(row.get("floor", "1")),
                row.get("zone_type", "general").strip(),
                row.get("primary_exit", "").strip(),
                row.get("alternate_exit", "").strip(),
                row.get("shelter_location", "").strip(),
                _parse_int(row.get("capacity", "0")),
                row.get("notes", "").strip(),
            )
            loaded += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")
            skipped += 1
    return IngestResult(csv_type, loaded, skipped, errors)


def _ingest_rooms(reader, csv_type) -> IngestResult:
    loaded, skipped, errors = 0, 0, []
    for i, row in enumerate(reader, 2):
        try:
            kb.add_room(
                row["room_id"].strip(),
                row["facility_id"].strip(),
                row["name"].strip(),
                _parse_int(row.get("floor", "1")),
                row.get("zone_id", "").strip() or None,
                row.get("room_type", "general").strip(),
                _parse_int(row.get("capacity", "0")),
                notes=row.get("notes", "").strip(),
            )
            loaded += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")
            skipped += 1
    return IngestResult(csv_type, loaded, skipped, errors)


def _ingest_personnel(reader, csv_type) -> IngestResult:
    loaded, skipped, errors = 0, 0, []
    for i, row in enumerate(reader, 2):
        try:
            kb.add_person(
                row["person_id"].strip(),
                row["name"].strip(),
                slack_user_id=row.get("slack_user_id", "").strip() or None,
                role=row.get("role", "").strip(),
                department=row.get("department", "").strip(),
                default_location=row.get("default_location", "").strip(),
                floor=_parse_int(row.get("floor", "1")),
                phone=row.get("phone", "").strip(),
                emergency_contact_name=row.get("emergency_contact_name", "").strip(),
                emergency_contact_phone=row.get("emergency_contact_phone", "").strip(),
                medical_notes=row.get("medical_notes", "").strip(),
                mobility_limitations=_parse_bool(row.get("mobility_limitations", "false")),
                trained_first_aid=_parse_bool(row.get("trained_first_aid", "false")),
                trained_cpr=_parse_bool(row.get("trained_cpr", "false")),
                is_floor_warden=_parse_bool(row.get("is_floor_warden", "false")),
                evacuation_role=row.get("evacuation_role", "").strip(),
            )
            loaded += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")
            skipped += 1
    return IngestResult(csv_type, loaded, skipped, errors)


def _ingest_emergency_resources(reader, csv_type) -> IngestResult:
    loaded, skipped, errors = 0, 0, []
    rows = list(reader)
    _clear_facility_scope("emergency_resources", rows)
    for i, row in enumerate(rows, 2):
        try:
            kb.add_emergency_resource(
                row["facility_id"].strip(),
                row["resource_type"].strip(),
                row["location_description"].strip(),
                _parse_int(row.get("floor", "1")),
                row.get("zone_id", "").strip() or None,
                row.get("notes", "").strip(),
            )
            loaded += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")
            skipped += 1
    return IngestResult(csv_type, loaded, skipped, errors)


def _ingest_evacuation_routes(reader, csv_type) -> IngestResult:
    loaded, skipped, errors = 0, 0, []
    rows = list(reader)
    _clear_facility_scope("evacuation_routes", rows)
    for i, row in enumerate(rows, 2):
        try:
            blocked = row.get("blocked_by_zones", "").strip()
            blocked_list = [z.strip() for z in blocked.split(",") if z.strip()] if blocked else []

            kb.add_evacuation_route(
                row["facility_id"].strip(),
                row["name"].strip(),
                row["to_exit"].strip(),
                row["route_description"].strip(),
                row.get("from_zone", "").strip(),
                row.get("accessibility", "standard").strip(),
                blocked_list,
                row.get("notes", "").strip(),
            )
            loaded += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")
            skipped += 1
    return IngestResult(csv_type, loaded, skipped, errors)


def _ingest_assembly_points(reader, csv_type) -> IngestResult:
    loaded, skipped, errors = 0, 0, []
    for i, row in enumerate(reader, 2):
        try:
            kb.add_assembly_point(
                row["point_id"].strip(),
                row["facility_id"].strip(),
                row["name"].strip(),
                row["location_description"].strip(),
                _parse_int(row.get("capacity", "0")),
                _parse_bool(row.get("is_primary", "true")),
                row.get("alternate_point_id", "").strip() or None,
                row.get("accessibility", "standard").strip(),
                row.get("notes", "").strip(),
            )
            loaded += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")
            skipped += 1
    return IngestResult(csv_type, loaded, skipped, errors)


def _ingest_nearby_services(reader, csv_type) -> IngestResult:
    loaded, skipped, errors = 0, 0, []
    for i, row in enumerate(reader, 2):
        try:
            kb._conn.execute(
                "DELETE FROM nearby_services WHERE service_type = ? AND name = ?",
                (row["service_type"].strip(), row["name"].strip()),
            )
            kb._conn.execute(
                """INSERT INTO nearby_services
                   (service_type, name, address, phone, distance_miles, eta_minutes, trauma_level, helipad)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row["service_type"].strip(),
                    row["name"].strip(),
                    row.get("address", "").strip(),
                    row.get("phone", "").strip(),
                    _parse_float(row.get("distance_miles", "0")),
                    _parse_int(row.get("eta_minutes", "0")),
                    row.get("trauma_level", "").strip(),
                    int(_parse_bool(row.get("helipad", "false"))),
                ),
            )
            kb._conn.commit()
            loaded += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")
            skipped += 1
    return IngestResult(csv_type, loaded, skipped, errors)


def _ingest_utility_controls(reader, csv_type) -> IngestResult:
    loaded, skipped, errors = 0, 0, []
    rows = list(reader)
    _clear_facility_scope("utility_controls", rows)
    for i, row in enumerate(rows, 2):
        try:
            kb._conn.execute(
                """INSERT INTO utility_controls
                   (facility_id, utility_type, location_description, floor, zone_id,
                    shutoff_instructions, requires_key, key_location)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row["facility_id"].strip(),
                    row["utility_type"].strip(),
                    row["location_description"].strip(),
                    _parse_int(row.get("floor", "1")),
                    row.get("zone_id", "").strip() or None,
                    row.get("shutoff_instructions", "").strip(),
                    int(_parse_bool(row.get("requires_key", "false"))),
                    row.get("key_location", "").strip(),
                ),
            )
            kb._conn.commit()
            loaded += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")
            skipped += 1
    return IngestResult(csv_type, loaded, skipped, errors)


def _ingest_hazmat_locations(reader, csv_type) -> IngestResult:
    loaded, skipped, errors = 0, 0, []
    rows = list(reader)
    _clear_facility_scope("hazmat_locations", rows)
    for i, row in enumerate(rows, 2):
        try:
            kb._conn.execute(
                """INSERT INTO hazmat_locations
                   (facility_id, material_name, hazard_class, location_description, floor,
                    zone_id, quantity, sds_location, containment_instructions)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row["facility_id"].strip(),
                    row["material_name"].strip(),
                    row["hazard_class"].strip(),
                    row["location_description"].strip(),
                    _parse_int(row.get("floor", "1")),
                    row.get("zone_id", "").strip() or None,
                    row.get("quantity", "").strip(),
                    row.get("sds_location", "").strip(),
                    row.get("containment_instructions", "").strip(),
                ),
            )
            kb._conn.commit()
            loaded += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")
            skipped += 1
    return IngestResult(csv_type, loaded, skipped, errors)


def _ingest_network_assets(reader, csv_type) -> IngestResult:
    loaded, skipped, errors = 0, 0, []
    for i, row in enumerate(reader, 2):
        try:
            deps = row.get("dependencies", "[]").strip()
            if not deps.startswith("["):
                deps = "[]"
            kb.add_network_asset(
                row["asset_id"].strip(),
                row["name"].strip(),
                row["asset_type"].strip(),
                row.get("ip_address", "").strip(),
                row.get("location", "").strip(),
                row.get("criticality", "medium").strip(),
                json.loads(deps),
                row.get("owner", "").strip(),
                row.get("notes", "").strip(),
            )
            loaded += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")
            skipped += 1
    return IngestResult(csv_type, loaded, skipped, errors)


def _ingest_data_inventory(reader, csv_type) -> IngestResult:
    loaded, skipped, errors = 0, 0, []
    for i, row in enumerate(reader, 2):
        try:
            pii = row.get("pii_fields", "[]").strip()
            if not pii.startswith("["):
                pii = "[]"
            regs = row.get("regulatory_frameworks", "[]").strip()
            if not regs.startswith("["):
                regs = "[]"
            kb._conn.execute(
                """INSERT OR REPLACE INTO data_inventory
                   (id, name, data_classification, storage_system, record_count,
                    pii_fields, regulatory_frameworks, backup_location, backup_frequency,
                    retention_policy, data_owner, notification_requirements, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row["data_id"].strip(),
                    row["name"].strip(),
                    row["data_classification"].strip(),
                    row["storage_system"].strip(),
                    row.get("record_count", "").strip(),
                    pii,
                    regs,
                    row.get("backup_location", "").strip(),
                    row.get("backup_frequency", "").strip(),
                    row.get("retention_policy", "").strip(),
                    row.get("data_owner", "").strip(),
                    row.get("notification_requirements", "").strip(),
                    row.get("notes", "").strip(),
                ),
            )
            kb._conn.commit()
            loaded += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")
            skipped += 1
    return IngestResult(csv_type, loaded, skipped, errors)


def _ingest_runbooks(reader, csv_type) -> IngestResult:
    loaded, skipped, errors = 0, 0, []
    for i, row in enumerate(reader, 2):
        try:
            steps = row.get("steps", "[]").strip()
            if not steps.startswith("["):
                steps = "[]"
            kb._conn.execute(
                "DELETE FROM runbooks WHERE title = ? AND scenario_type = ?",
                (row["title"].strip(), row["scenario_type"].strip()),
            )
            kb._conn.execute(
                """INSERT INTO runbooks
                   (title, scenario_type, system_or_service, severity, steps,
                    estimated_minutes, last_tested, owner, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row["title"].strip(),
                    row["scenario_type"].strip(),
                    row.get("system_or_service", "").strip(),
                    row.get("severity", "medium").strip(),
                    steps,
                    _parse_int(row.get("estimated_minutes", "0")),
                    row.get("last_tested", "").strip(),
                    row.get("owner", "").strip(),
                    row.get("notes", "").strip(),
                ),
            )
            kb._conn.commit()
            loaded += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")
            skipped += 1
    return IngestResult(csv_type, loaded, skipped, errors)


def _ingest_on_call_schedules(reader, csv_type) -> IngestResult:
    loaded, skipped, errors = 0, 0, []
    for i, row in enumerate(reader, 2):
        try:
            kb._conn.execute(
                "DELETE FROM on_call_schedules WHERE team_name = ? AND service = ?",
                (row["team_name"].strip(), row["service"].strip()),
            )
            kb._conn.execute(
                """INSERT INTO on_call_schedules
                   (team_name, service, primary_name, primary_slack_id, primary_phone,
                    secondary_name, secondary_slack_id, secondary_phone,
                    escalation_manager, escalation_phone, schedule_notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row["team_name"].strip(),
                    row["service"].strip(),
                    row["primary_name"].strip(),
                    row.get("primary_slack_id", "").strip(),
                    row.get("primary_phone", "").strip(),
                    row.get("secondary_name", "").strip(),
                    row.get("secondary_slack_id", "").strip(),
                    row.get("secondary_phone", "").strip(),
                    row.get("escalation_manager", "").strip(),
                    row.get("escalation_phone", "").strip(),
                    row.get("schedule_notes", "").strip(),
                ),
            )
            kb._conn.commit()
            loaded += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")
            skipped += 1
    return IngestResult(csv_type, loaded, skipped, errors)


def _ingest_continuity_plans(reader, csv_type) -> IngestResult:
    loaded, skipped, errors = 0, 0, []
    for i, row in enumerate(reader, 2):
        try:
            actions = row.get("actions", "[]").strip()
            if not actions.startswith("["):
                actions = "[]"
            critical = row.get("critical_functions", "[]").strip()
            if not critical.startswith("["):
                critical = "[]"
            kb._conn.execute(
                "DELETE FROM continuity_plans WHERE scenario_type = ? AND plan_name = ?",
                (row["scenario_type"].strip(), row["plan_name"].strip()),
            )
            kb._conn.execute(
                """INSERT INTO continuity_plans
                   (scenario_type, plan_name, trigger_conditions, actions,
                    remote_work_capable, backup_facility, critical_functions,
                    recovery_time_objective_hours, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row["scenario_type"].strip(),
                    row["plan_name"].strip(),
                    row.get("trigger_conditions", "").strip(),
                    actions,
                    int(_parse_bool(row.get("remote_work_capable", "false"))),
                    row.get("backup_facility", "").strip(),
                    critical,
                    _parse_int(row.get("recovery_time_objective_hours", "0")),
                    row.get("notes", "").strip(),
                ),
            )
            kb._conn.commit()
            loaded += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")
            skipped += 1
    return IngestResult(csv_type, loaded, skipped, errors)


def _ingest_drills(reader, csv_type) -> IngestResult:
    loaded, skipped, errors = 0, 0, []
    for i, row in enumerate(reader, 2):
        try:
            fid = row.get("facility_id", "").strip() or None
            # upsert on (facility_id, drill_type, date) so re-uploading a drill
            # log doesn't duplicate entries
            kb._conn.execute(
                "DELETE FROM drill_history WHERE facility_id IS ? AND drill_type = ? AND date = ?",
                (fid, row["drill_type"].strip(), row["date"].strip()),
            )
            kb._conn.execute(
                """INSERT INTO drill_history
                   (facility_id, drill_type, date, total_evacuation_seconds,
                    full_accountability_seconds, participants, slowest_zone, issues_noted, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    fid,
                    row["drill_type"].strip(),
                    row["date"].strip(),
                    _parse_int(row.get("total_evacuation_seconds", "0")),
                    _parse_int(row.get("full_accountability_seconds", "0")),
                    _parse_int(row.get("participants", "0")),
                    row.get("slowest_zone", "").strip(),
                    row.get("issues_noted", "").strip(),
                    row.get("notes", "").strip(),
                ),
            )
            kb._conn.commit()
            loaded += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")
            skipped += 1
    return IngestResult(csv_type, loaded, skipped, errors)


def _ingest_vendor_contacts(reader, csv_type) -> IngestResult:
    loaded, skipped, errors = 0, 0, []
    for i, row in enumerate(reader, 2):
        try:
            # upsert on (vendor_name, service)
            kb._conn.execute(
                "DELETE FROM vendor_contacts WHERE vendor_name = ? AND service = ?",
                (row["vendor_name"].strip(), row["service"].strip()),
            )
            kb._conn.execute(
                """INSERT INTO vendor_contacts
                   (vendor_name, service, contact_name, contact_phone, contact_email,
                    escalation_procedure, sla_hours, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row["vendor_name"].strip(),
                    row["service"].strip(),
                    row.get("contact_name", "").strip(),
                    row.get("contact_phone", "").strip(),
                    row.get("contact_email", "").strip(),
                    row.get("escalation_procedure", "").strip(),
                    _parse_int(row.get("sla_hours", "0")),
                    row.get("notes", "").strip(),
                ),
            )
            kb._conn.commit()
            loaded += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")
            skipped += 1
    return IngestResult(csv_type, loaded, skipped, errors)
