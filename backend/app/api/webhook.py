import base64
import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.config import settings
from app.services import intent_dispatcher, line_messaging, user_resolver

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/webhook",
    tags=["LINE Webhook"],
)


def verify_line_signature(body: bytes, signature: str | None, channel_secret: str) -> bool:
    if not signature or not channel_secret:
        return False
    hash_digest = hmac.new(
        channel_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).digest()
    expected_signature = base64.b64encode(hash_digest).decode("utf-8")
    return hmac.compare_digest(expected_signature, signature)


@router.post("")
async def line_webhook(
    request: Request,
    x_line_signature: str | None = Header(default=None, alias="X-Line-Signature"),
    db: Session = Depends(get_db),
):
    body = await request.body()

    # Validate LINE signature if channel secret is configured
    if settings.line_channel_secret:
        if not verify_line_signature(body, x_line_signature, settings.line_channel_secret):
            raise HTTPException(
                status_code=400,
                detail="Invalid LINE signature",
            )

    try:
        payload = json.loads(body.decode("utf-8")) if body else {}
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload",
        )

    events = payload.get("events", [])
    for event in events:
        source = event.get("source", {})
        line_user_id = source.get("userId")

        # Process user events only
        if not line_user_id:
            continue

        # Resolve LINE user to internal user_id
        user = user_resolver.resolve_line_user(db=db, line_user_id=line_user_id)
        user_id = user.id

        event_type = event.get("type")
        if event_type == "message":
            message = event.get("message", {})
            message_type = message.get("type")

            if message_type == "text":
                user_text = message.get("text", "")
                reply_token = event.get("replyToken")
                logger.info(
                    f"Received message from resolved user {user_id} (LINE {line_user_id}): {user_text}"
                )

                if reply_token:
                    # Detect public base URL (handling ngrok and reverse proxies)
                    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
                    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
                    base_url = f"{proto}://{host}"

                    # Process user message with LLM and dispatch intent
                    dispatch_result = await intent_dispatcher.dispatch_user_message(
                        db=db,
                        user_id=user_id,
                        user_message=user_text,
                        base_url=base_url,
                    )

                    if dispatch_result.get("type") == "file":
                        await line_messaging.reply_file_message(
                            reply_token=reply_token,
                            title=dispatch_result["title"],
                            file_size=dispatch_result["file_size"],
                            download_url=dispatch_result["download_url"],
                            text=dispatch_result.get("text"),
                        )
                    else:
                        await line_messaging.reply_text_message(
                            reply_token=reply_token,
                            text=dispatch_result.get("text", ""),
                        )

    return {"status": "ok"}



