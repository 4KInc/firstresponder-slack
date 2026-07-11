"""Shared test fixtures.

Isolate every test to its own empty incident database. The incident store and
crisis manager are module-level singletons that persist to ``data/``; without
this, tests would share (and pollute) the real committed database, and — now
that the manager rehydrates active incidents on construction — would see each
other's incidents. Pointing both module references at a per-test temp DB keeps
each test starting from a clean slate.
"""

import pytest


@pytest.fixture(autouse=True)
def _isolate_incident_store(tmp_path, monkeypatch):
    from crisis.store import IncidentStore
    import crisis.store as store_mod
    import crisis.manager as mgr_mod

    store = IncidentStore(db_path=tmp_path / "incidents.db")
    monkeypatch.setattr(store_mod, "incident_store", store, raising=False)
    monkeypatch.setattr(mgr_mod, "incident_store", store, raising=False)
    yield
