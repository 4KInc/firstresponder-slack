from logging import Logger

from slack_bolt.context.async_context import AsyncBoltContext
from slack_bolt.context.say.async_say import AsyncSay
from slack_bolt.context.say_stream.async_say_stream import AsyncSayStream
from slack_bolt.context.set_status.async_set_status import AsyncSetStatus
from slack_sdk.web.async_client import AsyncWebClient

from agent import AgentDeps, run_agent
from thread_context import session_store
from listeners.views.feedback_builder import build_feedback_blocks


async def handle_message(
    client: AsyncWebClient,
    context: AsyncBoltContext,
    event: dict,
    logger: Logger,
    say: AsyncSay,
    say_stream: AsyncSayStream,
    set_status: AsyncSetStatus,
):
    if event.get("subtype"):
        return
    if event.get("bot_id"):
        return

    # If this message @mentions the bot, the app_mention listener handles it.
    # Skip here to avoid a double agent run + double reply in a live thread.
    bot_user_id = context.bot_user_id
    if bot_user_id and f"<@{bot_user_id}>" in event.get("text", ""):
        return

    is_dm = event.get("channel_type") == "im"
    is_thread_reply = event.get("thread_ts") is not None

    if is_dm:
        pass
    elif is_thread_reply:
        session = session_store.get_session(context.channel_id, event["thread_ts"])
        if session is None:
            return
    else:
        return

    try:
        channel_id = context.channel_id
        text = event.get("text", "")
        thread_ts = event.get("thread_ts") or event["ts"]

        existing_session_id = session_store.get_session(channel_id, thread_ts)

        # set_status is an Assistant-thread API; best-effort so channel/thread
        # replies still get answered.
        try:
            await set_status(
                status="Assessing situation...",
                loading_messages=[
                    "Reviewing incident protocols...",
                    "Checking personnel status...",
                    "Analyzing the situation...",
                    "Preparing response...",
                ],
            )
        except Exception:
            pass

        deps = AgentDeps(
            client=client,
            user_id=context.user_id,
            channel_id=channel_id,
            thread_ts=thread_ts,
            message_ts=event["ts"],
            user_token=context.user_token,
        )
        response_text, new_session_id = await run_agent(
            text, session_id=existing_session_id, deps=deps
        )

        if not response_text.strip():
            response_text = (
                ":warning: I couldn't produce a response. Try rephrasing, or use "
                "`/crisis help` for direct commands."
            )

        # Streaming is Assistant-thread only; fall back to a normal message.
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
        logger.exception(f"Failed to handle message: {e}")
        await say(
            text=f":warning: Something went wrong! ({e})",
            thread_ts=event.get("thread_ts") or event.get("ts"),
        )
