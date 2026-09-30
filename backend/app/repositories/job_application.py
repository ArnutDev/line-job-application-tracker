from datetime import date

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job_application import JobApplication


def create_application(
    db: Session,
    user_id: UUID,
    data: dict,
) -> JobApplication:
    if data.get("date_applied") is None:
        data["date_applied"] = date.today()

    application = JobApplication(
        user_id=user_id,
        **data,
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    return application


def get_application(
    db: Session,
    user_id: UUID,
    application_id: UUID,
) -> JobApplication | None:
    statement = select(JobApplication).where(
        JobApplication.id == application_id,
        JobApplication.user_id == user_id,
    )

    return db.scalar(statement)


def get_applications(
    db: Session,
    user_id: UUID,
) -> list[JobApplication]:
    statement = (
        select(JobApplication)
        .where(JobApplication.user_id == user_id)
        .order_by(JobApplication.created_at.desc())
    )

    return list(db.scalars(statement).all())

def update_application(
    db: Session,
    application: JobApplication,
    data: dict,
) -> JobApplication:

    for field, value in data.items():
        if value is not None:
            setattr(application, field, value)

    db.commit()
    db.refresh(application)

    return application

def delete_application(
    db: Session,
    application: JobApplication,
) -> None:
    db.delete(application)
    db.commit()

