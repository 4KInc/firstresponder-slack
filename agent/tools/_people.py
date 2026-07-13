"""Helpers for rendering knowledge-base personnel in Slack messages.

Directory personnel may carry placeholder ids (e.g. ``U_DAVIS``) rather than
real Slack user ids. Wrapping a placeholder in ``<@…>`` renders as a broken
mention in Slack, so we only emit a real mention for genuine Slack ids and
otherwise fall back to the person's name.
"""

import re

# Real Slack user ids look like U0BE0A0BWGH / W012ABC3DEF - a leading U or W
# followed by uppercase-alphanumeric (no underscores). Placeholder demo ids like
# "U_DAVIS" contain underscores and won't match.
_REAL_SLACK_ID = re.compile(r"[UW][A-Z0-9]{7,}")


def is_real_slack_id(slack_user_id) -> bool:
    return bool(slack_user_id) and _REAL_SLACK_ID.fullmatch(slack_user_id) is not None


def person_label(slack_user_id, name=None) -> str:
    """Render a person: a real @-mention for genuine Slack ids, else their name."""
    if is_real_slack_id(slack_user_id):
        return f"<@{slack_user_id}>"
    return name or slack_user_id or "Unknown"
