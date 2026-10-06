import logging
from datetime import date, datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories import usage as usage_repo

logger = logging.getLogger(__name__)

QUOTA_INQUIRY_KEYWORDS = {
    "เช็คโควต้า",
    "ดูโควต้า",
    "โควต้า",
    "เช็คสิทธิ์",
    "สิทธิ์การใช้งาน",
    "quota",
    "check quota",
}


def get_current_usage_date() -> date:
    """Return the current date in Asia/Bangkok (UTC+7) timezone so quotas reset at midnight local time."""
    try:
        tz = ZoneInfo("Asia/Bangkok")
        return datetime.now(tz).date()
    except Exception:
        return datetime.now(timezone.utc).date()


def is_quota_inquiry(message_text: str) -> bool:
    """Check if the user message is an inquiry about daily message quota."""
    cleaned = message_text.strip().lower()
    return cleaned in QUOTA_INQUIRY_KEYWORDS


def check_user_quota(
    db: Session,
    user_id: UUID,
    line_user_id: str,
) -> dict:
    """Retrieve detailed quota information for the given user."""
    is_unlimited = settings.is_unlimited_user(line_user_id)
    today = get_current_usage_date()
    usage = usage_repo.get_daily_usage(db, user_id, today)
    current_count = usage.message_count if usage else 0
    limit = settings.daily_message_limit

    if is_unlimited:
        return {
            "is_unlimited": True,
            "allowed": True,
            "used": current_count,
            "limit": None,
            "remaining": None,
            "date": today,
        }

    allowed = current_count < limit
    remaining = max(0, limit - current_count)
    return {
        "is_unlimited": False,
        "allowed": allowed,
        "used": current_count,
        "limit": limit,
        "remaining": remaining,
        "date": today,
    }


def format_quota_status(quota_info: dict) -> str:
    """Format human-readable quota status message."""
    if quota_info.get("is_unlimited"):
        used = quota_info.get("used", 0)
        return (
            "👑 สิทธิ์การใช้งานของคุณ: ไม่จำกัด (Unlimited)\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"💬 วันนี้คุณส่งข้อความไปแล้ว: {used} ข้อความ\n"
            "คุณสามารถพูดคุยและจัดการงานได้ไม่จำกัดจำนวนครั้งครับ 🚀"
        )

    used = quota_info.get("used", 0)
    limit = quota_info.get("limit", settings.daily_message_limit)
    remaining = quota_info.get("remaining", 0)

    return (
        "📊 โควต้าการใช้งานของคุณวันนี้\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"💬 ใช้งานไปแล้ว: {used}/{limit} ข้อความ\n"
        f"⏳ คงเหลือ: {remaining} ข้อความ\n"
        "🔄 รีเซ็ตโควต้าใหม่: ทุกวันเวลา 00:00 น. ครับ 😊"
    )


def consume_quota(
    db: Session,
    user_id: UUID,
    line_user_id: str,
) -> tuple[bool, str | None]:
    """Check if the user is allowed to send a message.
    If allowed, increment message count and return (True, None).
    If limit is exceeded, return (False, quota_exceeded_message).
    Unlimited users always pass and have their usage tracked.
    """
    today = get_current_usage_date()
    is_unlimited = settings.is_unlimited_user(line_user_id)
    limit = settings.daily_message_limit

    if is_unlimited:
        usage_repo.increment_daily_usage(db, user_id, today)
        return True, None

    usage = usage_repo.get_daily_usage(db, user_id, today)
    current_count = usage.message_count if usage else 0

    if current_count >= limit:
        logger.warning(
            f"User {user_id} (LINE: {line_user_id}) exceeded daily limit ({current_count}/{limit})"
        )
        msg = (
            f"⏳ ขออภัยครับ คุณใช้งานครบโควต้า {limit} ข้อความสำหรับวันนี้แล้ว\n"
            "ระบบจะรีเซ็ตโควต้าใหม่ในวันพรุ่งนี้เวลา 00:00 น. ครับ ขอบคุณครับ 😊"
        )
        return False, msg

    usage_repo.increment_daily_usage(db, user_id, today)
    return True, None
