from logging import Logger

from slack_bolt import Ack
from slack_bolt.context.async_context import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient


async def handle_feedback_button(
    ack: Ack,
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()

    try:
        channel_id = context.channel_id
        user_id = context.user_id
        message_ts = body["message"]["ts"]
        feedback_value = body["actions"][0]["value"]

        if feedback_value == "good-feedback":
            await client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                thread_ts=message_ts,
                text="Glad the response was helpful. Stay safe.",
            )
        else:
            await client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                thread_ts=message_ts,
                text="Sorry that wasn't helpful. Try providing more context about the situation.",
            )

        logger.debug(f"Feedback: value={feedback_value}, message_ts={message_ts}")
    except Exception as e:
        logger.exception(f"Failed to handle feedback: {e}")
