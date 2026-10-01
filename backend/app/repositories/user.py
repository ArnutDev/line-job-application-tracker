from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User


def get_user_by_line_id(
    db: Session,
    line_user_id: str,
) -> User | None:
    statement = select(User).where(User.line_user_id == line_user_id)
    return db.scalar(statement)


def get_user_by_id(
    db: Session,
    user_id: UUID,
) -> User | None:
    statement = select(User).where(User.id == user_id)
    return db.scalar(statement)


def create_user(
    db: Session,
    line_user_id: str,
) -> User:
    user = User(line_user_id=line_user_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_user(
    db: Session,
    line_user_id: str,
) -> User:
    user = get_user_by_line_id(db, line_user_id)
    if user is not None:
        return user

    try:
        return create_user(db, line_user_id)
    except IntegrityError:
        db.rollback()
        existing_user = get_user_by_line_id(db, line_user_id)
        if existing_user is not None:
            return existing_user
        raise
