from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.job_application import ApplicationStatus, WorkMode


class JobApplicationCreate(BaseModel):
    company: str
    position: str
    job_url: str | None = None
    source: str | None = None
    location: str | None = None
    work_mode: WorkMode | None = None
    date_applied: date | None = None
    status: ApplicationStatus = ApplicationStatus.APPLIED
    salary: str | None = None
    note: str | None = None


class JobApplicationUpdate(BaseModel):
    company: str | None = None
    position: str | None = None
    job_url: str | None = None
    source: str | None = None
    location: str | None = None
    work_mode: WorkMode | None = None
    date_applied: date | None = None
    status: ApplicationStatus | None = None
    salary: str | None = None
    note: str | None = None


class JobApplicationResponse(BaseModel):
    id: UUID
    user_id: UUID
    company: str
    position: str
    job_url: str | None
    source: str | None
    location: str | None
    work_mode: WorkMode | None
    date_applied: date | None
    status: ApplicationStatus
    salary: str | None
    note: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }