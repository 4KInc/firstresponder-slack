from logging import Logger

from slack_bolt.context.set_suggested_prompts.async_set_suggested_prompts import (
    AsyncSetSuggestedPrompts,
)

SUGGESTED_PROMPTS = [
    {
        "title": ":rotating_light: Start a Crisis",
        "message": "We have an emergency - help me start a crisis response",
    },
    {
        "title": ":clipboard: View Active Incidents",
        "message": "Show me the status of all active incidents",
    },
    {
        "title": ":books: Get a Playbook",
        "message": "Show me the response playbook for a cyberattack",
    },
    {
        "title": ":white_check_mark: Check In Safe",
        "message": "I want to check in as safe for the current incident",
    },
]


async def handle_assistant_thread_started(
    set_suggested_prompts: AsyncSetSuggestedPrompts, logger: Logger
):
    try:
        await set_suggested_prompts(
            prompts=SUGGESTED_PROMPTS,
            title="FirstResponder - Crisis Coordination Agent",
        )
    except Exception as e:
        logger.exception(f"Failed to handle assistant thread started: {e}")
