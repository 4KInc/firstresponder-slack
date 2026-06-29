from crisis.manager import CrisisManager
from crisis.models import CrisisStatus, CrisisSeverity


def test_start_crisis():
    mgr = CrisisManager()
    crisis = mgr.start_crisis(
        crisis_type="fire",
        description="Building A fire alarm triggered",
        channel_id="C123",
        created_by="U001",
    )
    assert crisis.id.startswith("INC-")
    assert crisis.crisis_type == "fire"
    assert crisis.severity == CrisisSeverity.CRITICAL
    assert crisis.status == CrisisStatus.ACTIVE
    assert len(crisis.timeline) == 1


def test_check_in():
    mgr = CrisisManager()
    crisis = mgr.start_crisis("earthquake", "Shaking felt", "C123", "U001")
    mgr.add_to_roster(crisis.id, ["U001", "U002", "U003"])

    mgr.check_in(crisis.id, "U001", "safe")
    assert "U001" in crisis.check_ins
    assert crisis.check_ins["U001"].status == "safe"
    assert crisis.missing_checkins == ["U002", "U003"]


def test_all_checked_in():
    mgr = CrisisManager()
    crisis = mgr.start_crisis("outage", "API down", "C123", "U001")
    mgr.add_to_roster(crisis.id, ["U001", "U002"])

    mgr.check_in(crisis.id, "U001", "safe")
    mgr.check_in(crisis.id, "U002", "safe")
    assert crisis.missing_checkins == []


def test_resolve_crisis():
    mgr = CrisisManager()
    crisis = mgr.start_crisis("cyberattack", "Ransomware detected", "C123", "U001")

    resolved = mgr.resolve_crisis(crisis.id, "U001")
    assert resolved.status == CrisisStatus.RESOLVED
    assert resolved.resolved_at is not None


def test_sitrep():
    mgr = CrisisManager()
    crisis = mgr.start_crisis("flood", "Rising water levels", "C123", "U001")
    mgr.add_to_roster(crisis.id, ["U001", "U002"])
    mgr.check_in(crisis.id, "U001", "safe")

    sitrep = mgr.add_sitrep(crisis.id, "Water at 3ft", ["Sandbagged entrance"])
    assert sitrep.number == 1
    assert len(sitrep.checked_in) == 1
    assert len(sitrep.missing) == 1


def test_get_crisis_by_channel():
    mgr = CrisisManager()
    crisis = mgr.start_crisis("medical", "Employee collapsed", "C456", "U001")

    found = mgr.get_crisis_by_channel("C456")
    assert found.id == crisis.id

    assert mgr.get_crisis_by_channel("C999") is None


def test_after_action_report():
    mgr = CrisisManager()
    crisis = mgr.start_crisis("outage", "Database down", "C123", "U001")
    mgr.add_to_roster(crisis.id, ["U001", "U002"])
    mgr.check_in(crisis.id, "U001", "safe")
    mgr.set_incident_commander(crisis.id, "U001")
    mgr.add_sitrep(crisis.id, "DB recovering", ["Restarted primary"])
    mgr.resolve_crisis(crisis.id, "U001")

    report = mgr.generate_after_action_report(crisis.id)
    assert "After-Action Report" in report
    assert "RESOLVED" in report
    assert "U001" in report


def test_multiple_crises():
    mgr = CrisisManager()
    c1 = mgr.start_crisis("fire", "Kitchen fire", "C001", "U001")
    c2 = mgr.start_crisis("outage", "Network down", "C002", "U002")

    active = mgr.get_active_crises()
    assert len(active) == 2

    mgr.resolve_crisis(c1.id, "U001")
    active = mgr.get_active_crises()
    assert len(active) == 1
    assert active[0].id == c2.id
