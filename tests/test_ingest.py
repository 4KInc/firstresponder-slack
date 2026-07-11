"""Tests for the CSV ingestion engine (the org data-upload workflow).

Each test uses an isolated temp knowledge base so nothing touches real data.
"""

import pathlib

import pytest

import crisis.ingest as ing
from crisis.knowledge import KnowledgeBase

TEMPLATES = pathlib.Path(__file__).parent.parent / "templates"

# Synthetic CSVs for the types that don't ship a template (cyber / ops).
SYNTHETIC = {
    "utility_controls": "facility_id,utility_type,location_description,requires_key\nZZ,gas,Boiler room,true\n",
    "hazmat_locations": "facility_id,material_name,hazard_class,location_description\nZZ,Bleach,8,Custodial closet\n",
    "network_assets": 'asset_id,name,asset_type,dependencies\nsrv1,Primary DB,database,[]\n',
    "data_inventory": 'data_id,name,data_classification,storage_system\nd1,Student records,confidential,srv1\n',
    "runbooks": 'title,scenario_type,steps\nRestore DB,ransomware,["isolate","restore"]\n',
    "on_call_schedules": "team_name,service,primary_name\nIT,Network,Alex Kim\n",
    "continuity_plans": 'scenario_type,plan_name,actions\noutage,Remote fallback,["switch to cloud"]\n',
}

TEMPLATE_TYPES = [
    "facility", "zones", "rooms", "personnel", "emergency_resources",
    "evacuation_routes", "assembly_points", "nearby_services",
    "drills", "vendor_contacts",
]


@pytest.fixture(autouse=True)
def _isolated_kb(tmp_path, monkeypatch):
    monkeypatch.setattr(ing, "kb", KnowledgeBase(db_path=tmp_path / "kb.db"))


def _csv(name: str) -> str:
    if name in SYNTHETIC:
        return SYNTHETIC[name]
    return (TEMPLATES / f"{name}.csv").read_text()


def _all_types():
    return TEMPLATE_TYPES + list(SYNTHETIC.keys())


def test_detects_every_csv_type_from_headers():
    for name in _all_types():
        headers = _csv(name).splitlines()[0].split(",")
        assert ing.detect_csv_type(headers) == name, name


def test_each_template_ingests_successfully():
    for name in TEMPLATE_TYPES:
        result = ing.ingest_csv(_csv(name), f"{name}.csv")
        assert result.file_type == name
        assert result.success, f"{name}: {result.errors}"
        assert result.rows_loaded > 0


def test_reupload_is_idempotent_no_duplicates():
    # Load everything once, then twice more; row counts must not grow.
    for name in _all_types():
        ing.ingest_csv(_csv(name), f"{name}.csv")
    first = {k: v for k, v in ing.kb.get_facility_summary().items() if v}

    for _ in range(2):
        for name in _all_types():
            ing.ingest_csv(_csv(name), f"{name}.csv")
    second = {k: v for k, v in ing.kb.get_facility_summary().items() if v}

    assert first == second, f"re-upload changed counts: {first} -> {second}"


def test_unknown_headers_fail_gracefully():
    result = ing.ingest_csv("foo,bar,baz\n1,2,3\n", "mystery.csv")
    assert result.file_type == "unknown"
    assert not result.success
    assert "Could not detect" in result.errors[0]


def test_empty_file_fails_gracefully():
    result = ing.ingest_csv("", "empty.csv")
    assert not result.success


def test_partial_load_counts_rows():
    # A well-formed personnel CSV loads all its rows.
    result = ing.ingest_csv("person_id,name\np1,Alice\np2,Bob\n", "personnel.csv")
    assert result.rows_loaded == 2
    assert result.file_type == "personnel"
