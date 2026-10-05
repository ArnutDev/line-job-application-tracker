import asyncio
import json
import logging
import urllib.error
import urllib.request

from app.core.config import settings

logger = logging.getLogger(__name__)

LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"


def _send_line_reply_sync(reply_token: str, messages: list[dict], access_token: str) -> bool:
    if not access_token:
        logger.warning("LINE_CHANNEL_ACCESS_TOKEN is not configured. Skipping reply.")
        return False

    payload = {
        "replyToken": reply_token,
        "messages": messages,
    }
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        LINE_REPLY_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                logger.info("Successfully sent reply message to LINE.")
                return True
            logger.error(f"LINE API returned unexpected status {response.status}")
            return False
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        logger.error(f"Failed to send reply to LINE API: {e.code} - {error_body}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while sending reply to LINE: {e}")
        return False


async def reply_messages(reply_token: str, messages: list[dict]) -> bool:
    """Send a list of LINE message objects back to LINE Messaging API."""
    if not reply_token or not messages:
        return False

    return await asyncio.to_thread(
        _send_line_reply_sync,
        reply_token,
        messages,
        settings.line_channel_access_token,
    )


async def reply_text_message(reply_token: str, text: str) -> bool:
    """Send a plain text reply message back to LINE Messaging API."""
    if not reply_token or not text:
        return False

    messages = [
        {
            "type": "text",
            "text": text,
        }
    ]

    return await reply_messages(reply_token, messages)


async def reply_file_message(
    reply_token: str,
    title: str,
    file_size: int,
    download_url: str,
    text: str | None = None,
) -> bool:
    """Send a native downloadable file message (e.g. XLSX) back to LINE chat."""
    if not reply_token or not download_url:
        return False

    messages = []
    if text:
        messages.append({"type": "text", "text": text})

    messages.append({
        "type": "file",
        "title": title,
        "fileSize": file_size,
        "originalContentUrl": download_url,
    })

    return await reply_messages(reply_token, messages)

