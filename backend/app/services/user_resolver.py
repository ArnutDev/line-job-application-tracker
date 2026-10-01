from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import user as user_repository


def resolve_line_user(
    db: Session,
    line_user_id: str,
) -> User:
    """Resolve an external LINE user ID to an internal User model.
    Creates a new user record automatically if one does not exist.
    """
    if not line_user_id or not isinstance(line_user_id, str) or not line_user_id.strip():
        raise ValueError("line_user_id must be a non-empty string")

    cleaned_line_id = line_user_id.strip()
    return user_repository.get_or_create_user(db, cleaned_line_id)


def resolve_line_user_id(
    db: Session,
    line_user_id: str,
) -> UUID:
    """Convenience helper returning only the internal UUID user_id."""
    user = resolve_line_user(db, line_user_id)
    return user.id
