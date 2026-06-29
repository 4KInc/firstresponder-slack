"""CSV ingestion engine — parses uploaded CSV files into the knowledge base.

Supports: facility, zones, rooms, personnel, emergency_resources,
evacuation_routes, assembly_points, nearby_services.

Each CSV type has its own parser that validates required columns
and loads rows into the SQLite knowledge base.
"""

import csv
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
    "facility": ["facility_id", "name"],
    "zones": ["zone_id", "facility_id", "name", "floor"],
    "rooms": ["room_id", "facility_id", "name", "floor"],
    "personnel": ["person_id", "name"],
    "emergency_resources": ["facility_id", "resource_type", "location_description"],
    "evacuation_routes": ["facility_id", "name", "to_exit", "route_description"],
    "assembly_points": ["point_id", "facility_id", "name", "location_description"],
    "nearby_services": ["service_type", "name"],
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


def detect_csv_type(headers: list[str]) -> str | None:
    """Detect the CSV type based on column headers."""
    headers_set = set(h.strip().lower() for h in headers)

    for csv_type, required in SCHEMAS.items():
        if all(col in headers_set for col in required):
            return csv_type

    return None


def ingest_csv(content: str, filename: str = "") -> IngestResult:
    """Parse a CSV string and load it into the knowledge base.

    Auto-detects the CSV type from column headers.
    """
    reader = csv.DictReader(io.StringIO(content))

    if not reader.fieldnames:
        return IngestResult("unknown", 0, 0, ["Empty CSV or no headers found"])

    # Normalize headers
    headers = [h.strip().lower() for h in reader.fieldnames]
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
    for i, row in enumerate(reader, 2):
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
    for i, row in enumerate(reader, 2):
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
