"""Handle CSV file uploads — auto-ingest into the knowledge base."""

from logging import Logger

from slack_bolt.context.async_context import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient

from crisis.ingest import ingest_csv
from crisis.knowledge import knowledge_base


async def handle_file_shared(
    client: AsyncWebClient,
    context: AsyncBoltContext,
    event: dict,
    logger: Logger,
):
    """When a file is shared in a DM with the bot, check if it's a CSV and ingest it."""
    try:
        channel_id = event.get("channel_id", "")
        file_id = event.get("file_id", "")

        if not file_id:
            return

        # Get file info
        file_info = await client.files_info(file=file_id)
        file_data = file_info["file"]

        filename = file_data.get("name", "")
        filetype = file_data.get("filetype", "")
        mimetype = file_data.get("mimetype", "")

        # Only process CSV files
        if filetype != "csv" and not filename.endswith(".csv"):
            return

        # Download the file content
        url = file_data.get("url_private", "")
        if not url:
            return

        import aiohttp
        headers = {"Authorization": f"Bearer {client.token}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    await client.chat_postMessage(
                        channel=channel_id,
                        text=f":warning: Could not download file `{filename}`. Status: {resp.status}",
                    )
                    return
                content = await resp.text()

        # Ingest the CSV
        result = ingest_csv(content, filename)

        if result.success:
            # Get updated summary
            summary = knowledge_base.get_facility_summary()
            non_zero = {k: v for k, v in summary.items() if v > 0}

            await client.chat_postMessage(
                channel=channel_id,
                text=(
                    f":white_check_mark: *File `{filename}` loaded successfully!*\n\n"
                    f"{result.summary()}\n\n"
                    f"*Knowledge Base Summary:*\n"
                    + "\n".join(f"- {k.replace('_', ' ').title()}: {v}" for k, v in non_zero.items())
                ),
            )
        else:
            await client.chat_postMessage(
                channel=channel_id,
                text=(
                    f":warning: *Could not load `{filename}`*\n\n"
                    f"{result.summary()}\n\n"
                    f"Make sure your CSV has the correct column headers. "
                    f"Use `/crisis setup` to download templates."
                ),
            )

    except Exception as e:
        logger.exception(f"Failed to handle file upload: {e}")
