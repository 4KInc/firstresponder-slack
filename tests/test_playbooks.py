from crisis.models import CRISIS_TYPES
from crisis.playbooks import get_playbook, format_playbook_message, PLAYBOOKS


def test_all_crisis_types_have_playbooks():
    for key, info in CRISIS_TYPES.items():
        playbook = get_playbook(info["playbook"])
        assert "title" in playbook
        assert "immediate_actions" in playbook
        assert "roles" in playbook
        assert "resources_needed" in playbook
        assert len(playbook["immediate_actions"]) >= 3
        assert len(playbook["roles"]) >= 3


def test_format_playbook_message():
    for key in CRISIS_TYPES:
        msg = format_playbook_message(key)
        assert "Immediate Actions" in msg
        assert "Roles Needed" in msg
        assert "Resources" in msg


def test_unknown_type_falls_back_to_generic():
    playbook = get_playbook("nonexistent")
    assert playbook["title"] == "General Incident Response Playbook"
