import logging
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user_daily_usage import UserDailyUsage

logger = logging.getLogger(__name__)


def get_daily_usage(
    db: Session,
    user_id: UUID,
    usage_date: date,
) -> UserDailyUsage | None:
    """Retrieve the usage record for a specific user and date."""
    stmt = select(UserDailyUsage).where(
        UserDailyUsage.user_id == user_id,
        UserDailyUsage.usage_date == usage_date,
    )
    return db.scalars(stmt).first()


def get_or_create_daily_usage(
    db: Session,
    user_id: UUID,
    usage_date: date,
) -> UserDailyUsage:
    """Retrieve or create a usage record initialized with 0 messages."""
    usage = get_daily_usage(db, user_id, usage_date)
    if usage is None:
        usage = UserDailyUsage(
            user_id=user_id,
            usage_date=usage_date,
            message_count=0,
        )
        db.add(usage)
        db.commit()
        db.refresh(usage)
    return usage


def increment_daily_usage(
    db: Session,
    user_id: UUID,
    usage_date: date,
) -> int:
    """Increment message count for the user on the given date and return the updated count."""
    usage = get_or_create_daily_usage(db, user_id, usage_date)
    usage.message_count += 1
    db.commit()
    db.refresh(usage)
    return usage.message_count


def reset_daily_usage(
    db: Session,
    user_id: UUID,
    usage_date: date,
) -> None:
    """Reset message count to 0 for the user on the given date."""
    usage = get_daily_usage(db, user_id, usage_date)
    if usage:
        usage.message_count = 0
        db.commit()
