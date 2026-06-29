import tempfile
from pathlib import Path

from crisis.store import IncidentStore
from crisis.manager import CrisisManager
from crisis.models import CrisisSeverity


def _make_manager():
    """Create a manager with a temp database for isolated tests."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    store = IncidentStore(db_path=Path(tmp.name))
    mgr = CrisisManager()
    # Monkey-patch the store reference in the manager module
    import crisis.manager
    crisis.manager.incident_store = store
    return mgr, store


def test_incident_persists_to_db():
    mgr, store = _make_manager()
    crisis = mgr.start_crisis("fire", "Kitchen fire", "C001", "U001")

    results = store.search_incidents("Kitchen")
    assert len(results) == 1
    assert results[0]["id"] == crisis.id


def test_checkin_persists():
    mgr, store = _make_manager()
    crisis = mgr.start_crisis("outage", "API down", "C001", "U001")
    mgr.add_to_roster(crisis.id, ["U001", "U002"])
    mgr.check_in(crisis.id, "U001", "safe", "I'm at home")

    rows = store._conn.execute(
        "SELECT * FROM checkins WHERE incident_id = ?", (crisis.id,)
    ).fetchall()
    assert len(rows) == 1
    assert rows[0]["status"] == "safe"


def test_lessons_learned():
    mgr, store = _make_manager()
    crisis = mgr.start_crisis("cyberattack", "Ransomware", "C001", "U001")
    mgr.resolve_crisis(crisis.id, "U001")

    mgr.add_lesson_learned(crisis.id, "Isolate servers within 5 minutes", "technical")
    mgr.add_lesson_learned(crisis.id, "Notify legal immediately", "communication")

    lessons = store.get_lessons_for_type("cyberattack")
    assert len(lessons) == 2
    lesson_texts = [l["lesson"] for l in lessons]
    assert any("Isolate servers" in l for l in lesson_texts)
    assert any("Notify legal" in l for l in lesson_texts)


def test_past_context_with_history():
    mgr, store = _make_manager()

    # Create and resolve 3 fire incidents
    for i in range(3):
        c = mgr.start_crisis("fire", f"Fire incident {i}", f"C{i}", "U001")
        mgr.add_to_roster(c.id, ["U001", "U002"])
        mgr.check_in(c.id, "U001", "safe")
        mgr.resolve_crisis(c.id, "U001")
        mgr.add_lesson_learned(c.id, f"Lesson from fire {i}", "safety")

    context = mgr.get_past_context("fire")
    assert context["has_data"] is True
    assert context["past_incident_count"] == 3
    assert len(context["lessons"]) == 3


def test_past_context_without_history():
    mgr, store = _make_manager()

    context = mgr.get_past_context("earthquake")
    assert context["has_data"] is False


def test_organization_stats():
    mgr, store = _make_manager()

    c1 = mgr.start_crisis("fire", "Fire 1", "C001", "U001")
    mgr.resolve_crisis(c1.id, "U001")

    c2 = mgr.start_crisis("outage", "Outage 1", "C002", "U001")
    mgr.resolve_crisis(c2.id, "U001")

    c3 = mgr.start_crisis("fire", "Fire 2", "C003", "U001")
    # leave active

    stats = mgr.get_stats()
    assert stats["total_incidents"] == 3
    assert stats["resolved"] == 2
    assert stats["active"] == 1
    assert stats["by_type"]["fire"] == 2
    assert stats["by_type"]["outage"] == 1


def test_after_action_report_includes_history():
    mgr, store = _make_manager()

    # First fire — with lesson
    c1 = mgr.start_crisis("fire", "First fire", "C001", "U001")
    mgr.resolve_crisis(c1.id, "U001")
    mgr.add_lesson_learned(c1.id, "Keep fire extinguishers near exits", "safety")

    # Second fire — AAR should reference the first
    c2 = mgr.start_crisis("fire", "Second fire", "C002", "U001")
    mgr.add_to_roster(c2.id, ["U001"])
    mgr.check_in(c2.id, "U001", "safe")
    mgr.resolve_crisis(c2.id, "U001")

    report = mgr.generate_after_action_report(c2.id)
    assert "Comparison to Past Incidents" in report
    assert "fire extinguishers" in report


def test_search_past_incidents():
    mgr, store = _make_manager()

    mgr.start_crisis("cyberattack", "Ransomware on file server", "C001", "U001")
    mgr.start_crisis("outage", "Database connection timeout", "C002", "U001")

    results = mgr.search_past_incidents("ransomware")
    assert len(results) == 1
    assert "Ransomware" in results[0]["description"]

    results = mgr.search_past_incidents("database")
    assert len(results) == 1
