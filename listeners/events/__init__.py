from slack_bolt.async_app import AsyncApp

from .app_home_opened import handle_app_home_opened
from .app_mentioned import handle_app_mentioned
from .assistant_thread_started import handle_assistant_thread_started
from .message import handle_message
from .reaction_added import handle_reaction_added
from .file_shared import handle_file_shared
from .slash_crisis import handle_crisis_command


def register(app: AsyncApp):
    app.event("app_home_opened")(handle_app_home_opened)
    app.event("app_mention")(handle_app_mentioned)
    app.event("assistant_thread_started")(handle_assistant_thread_started)
    app.event("message")(handle_message)
    app.event("reaction_added")(handle_reaction_added)
    app.event("file_shared")(handle_file_shared)
    app.command("/crisis")(handle_crisis_command)
