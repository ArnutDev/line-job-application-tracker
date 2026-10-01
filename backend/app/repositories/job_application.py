from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.job_application import ApplicationStatus, JobApplication, WorkMode


WORK_MODE_MAPPING: dict[str, WorkMode] = {
    "onsite": WorkMode.ON_SITE,
    "on-site": WorkMode.ON_SITE,
    "hybrid": WorkMode.HYBRID,
    "remote": WorkMode.REMOTE,
    "unknown": WorkMode.UNKNOWN,
}

STATUS_MAPPING: dict[str, ApplicationStatus] = {
    # Thai status names
    "ยังไม่ได้สมัคร": ApplicationStatus.NOT_APPLIED,
    "สมัครแล้ว": ApplicationStatus.APPLIED,
    "กำลังคัดกรอง": ApplicationStatus.SCREENING,
    "นัดสัมภาษณ์": ApplicationStatus.INTERVIEW_SCHEDULED,
    "สัมภาษณ์แล้ว": ApplicationStatus.INTERVIEWED,
    "ผ่านการคัดเลือก": ApplicationStatus.ACCEPTED,
    "ปฏิเสธแล้ว": ApplicationStatus.REJECTED,
    "ไม่มีการตอบกลับ": ApplicationStatus.NO_RESPONSE,
    # English names
    "not_applied": ApplicationStatus.NOT_APPLIED,
    "applied": ApplicationStatus.APPLIED,
    "screening": ApplicationStatus.SCREENING,
    "interview_scheduled": ApplicationStatus.INTERVIEW_SCHEDULED,
    "interviewed": ApplicationStatus.INTERVIEWED,
    "accepted": ApplicationStatus.ACCEPTED,
    "rejected": ApplicationStatus.REJECTED,
    "no_response": ApplicationStatus.NO_RESPONSE,
}


def normalize_work_mode(value: str | None) -> WorkMode | None:
    if not value:
        return None
    cleaned = value.strip().lower()
    if cleaned in WORK_MODE_MAPPING:
        return WORK_MODE_MAPPING[cleaned]
    for mode in WorkMode:
        if mode.value.lower() == cleaned or mode.name.lower() == cleaned:
            return mode
    return None


def normalize_status(value: str | None) -> ApplicationStatus | None:
    if not value:
        return None
    cleaned = value.strip()
    if cleaned in STATUS_MAPPING:
        return STATUS_MAPPING[cleaned]
    cleaned_lower = cleaned.lower()
    if cleaned_lower in STATUS_MAPPING:
        return STATUS_MAPPING[cleaned_lower]
    for status in ApplicationStatus:
        if status.value == cleaned or status.name.lower() == cleaned_lower:
            return status
    return None


def build_filter_conditions(
    user_id: UUID,
    status: str | None = None,
    company: str | None = None,
    position: str | None = None,
    work_mode: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list:
    conditions = [JobApplication.user_id == user_id]

    if status:
        normalized_status = normalize_status(status)
        if normalized_status:
            conditions.append(JobApplication.status == normalized_status)
        else:
            # If status string doesn't match any enum, match against string value directly
            conditions.append(JobApplication.status == status)

    if company:
        conditions.append(JobApplication.company.ilike(f"%{company.strip()}%"))

    if position:
        conditions.append(JobApplication.position.ilike(f"%{position.strip()}%"))

    if work_mode:
        normalized_work_mode = normalize_work_mode(work_mode)
        if normalized_work_mode:
            conditions.append(JobApplication.work_mode == normalized_work_mode)

    if date_from:
        conditions.append(JobApplication.date_applied >= date_from)

    if date_to:
        conditions.append(JobApplication.date_applied <= date_to)

    return conditions



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
    status: str | None = None,
    company: str | None = None,
    position: str | None = None,
    work_mode: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[JobApplication]:
    conditions = build_filter_conditions(
        user_id=user_id,
        status=status,
        company=company,
        position=position,
        work_mode=work_mode,
        date_from=date_from,
        date_to=date_to,
    )

    statement = (
        select(JobApplication)
        .where(*conditions)
        .order_by(JobApplication.created_at.desc())
    )

    return list(db.scalars(statement).all())


def get_application_summary(
    db: Session,
    user_id: UUID,
    status: str | None = None,
    company: str | None = None,
    position: str | None = None,
    work_mode: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> dict:
    conditions = build_filter_conditions(
        user_id=user_id,
        status=status,
        company=company,
        position=position,
        work_mode=work_mode,
        date_from=date_from,
        date_to=date_to,
    )

    # Database-side aggregation for status counts
    status_counts_stmt = (
        select(JobApplication.status, func.count(JobApplication.id))
        .where(*conditions)
        .group_by(JobApplication.status)
    )
    status_results = db.execute(status_counts_stmt).all()

    # Initialize all 8 statuses with 0
    by_status: dict[str, int] = {
        app_status.value: 0 for app_status in ApplicationStatus
    }
    for app_status, count in status_results:
        key = app_status.value if hasattr(app_status, "value") else str(app_status)
        by_status[key] = count

    total = sum(by_status.values())

    # Matching applications list
    applications_stmt = (
        select(JobApplication)
        .where(*conditions)
        .order_by(
            JobApplication.date_applied.desc().nulls_last(),
            JobApplication.created_at.desc(),
        )
    )
    applications = list(db.scalars(applications_stmt).all())

    return {
        "total": total,
        "by_status": by_status,
        "applications": applications,
    }


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

