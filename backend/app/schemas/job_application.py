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


class JobApplicationFilterParams(BaseModel):
    status: str | None = None
    company: str | None = None
    position: str | None = None
    work_mode: str | None = None
    date_from: date | None = None
    date_to: date | None = None


class JobApplicationSummaryResponse(BaseModel):
    total: int
    by_status: dict[str, int]
    applications: list[JobApplicationResponse]


QUERY_JOB_APPLICATIONS_TOOL = {
    "name": "query_job_applications",
    "description": "ค้นหาและสรุปข้อมูลการสมัครงาน",
    "parameters": {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "กรองตามสถานะ",
            },
            "company": {
                "type": "string",
                "description": "กรองตามบริษัท",
            },
            "position": {
                "type": "string",
                "description": "กรองตามตำแหน่ง",
            },
            "work_mode": {
                "type": "string",
                "enum": ["onsite", "hybrid", "remote", "unknown"],
                "description": "กรองตามรูปแบบการทำงาน",
            },
            "date_from": {
                "type": "string",
                "description": "วันที่เริ่มต้น YYYY-MM-DD",
            },
            "date_to": {
                "type": "string",
                "description": "วันที่สิ้นสุด YYYY-MM-DD",
            },
        },
    },
}