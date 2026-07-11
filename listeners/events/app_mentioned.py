import os
import re
from logging import Logger

from slack_bolt.context.async_context import AsyncBoltContext
from slack_bolt.context.say.async_say import AsyncSay
from slack_bolt.context.say_stream.async_say_stream import AsyncSayStream
from slack_bolt.context.set_status.async_set_status import AsyncSetStatus
from slack_sdk.web.async_client import AsyncWebClient

from agent import AgentDeps, run_agent
from thread_context import session_store
from listeners.views.feedback_builder import build_feedback_blocks


async def handle_app_mentioned(
    client: AsyncWebClient,
    context: AsyncBoltContext,
    event: dict,
    logger: Logger,
    say: AsyncSay,
    say_stream: AsyncSayStream,
    set_status: AsyncSetStatus,
):
    try:
        channel_id = context.channel_id
        text = event.get("text", "")
        thread_ts = event.get("thread_ts") or event["ts"]

        cleaned_text = re.sub(r"<@[A-Z0-9]+>", "", text).strip()

        if not cleaned_text:
            await say(
                text=":rotating_light: *FirstResponder standing by.* Tell me what's happening and I'll coordinate the response.",
                thread_ts=thread_ts,
            )
            return

        # set_status is an Assistant-thread API; it fails on a normal channel
        # @mention. Best-effort so the mention still gets answered anywhere.
        try:
            await set_status(
                status="Assessing situation...",
                loading_messages=[
                    "Reviewing incident protocols...",
                    "Checking personnel status...",
                    "Analyzing the situation...",
                ],
            )
        except Exception:
            pass

        existing_session_id = session_store.get_session(channel_id, thread_ts)

        deps = AgentDeps(
            client=client,
            user_id=context.user_id,
            channel_id=channel_id,
            thread_ts=thread_ts,
            message_ts=event["ts"],
            user_token=context.user_token or os.environ.get("SLACK_USER_TOKEN"),
        )
        response_text, new_session_id = await run_agent(
            cleaned_text, session_id=existing_session_id, deps=deps
        )

        if not response_text.strip():
            response_text = (
                ":warning: I couldn't produce a response. Try rephrasing, or use "
                "`/crisis help` for direct commands."
            )

        # Streaming (chat.startStream) is Assistant-thread only; fall back to a
        # normal threaded message on a regular channel @mention.
        try:
            streamer = await say_stream()
            await streamer.append(markdown_text=response_text)
            feedback_blocks = build_feedback_blocks()
            await streamer.stop(blocks=feedback_blocks)
        except Exception:
            await say(text=response_text, thread_ts=thread_ts)

        if new_session_id:
            session_store.set_session(channel_id, thread_ts, new_session_id)

    except Exception as e:
        logger.exception(f"Failed to handle app mention: {e}")
        await say(
            text=f":warning: Something went wrong! ({e})",
            thread_ts=event.get("thread_ts") or event["ts"],
        )
