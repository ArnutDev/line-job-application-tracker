import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WorkMode(str, enum.Enum):
    REMOTE = "Remote"
    HYBRID = "Hybrid"
    ON_SITE = "On-site"
    UNKNOWN = "Unknown"


class ApplicationStatus(str, enum.Enum):
    NOT_APPLIED = "ยังไม่ได้สมัคร"
    APPLIED = "สมัครแล้ว"
    SCREENING = "กำลังคัดกรอง"
    INTERVIEW_SCHEDULED = "นัดสัมภาษณ์"
    INTERVIEWED = "สัมภาษณ์แล้ว"
    ACCEPTED = "ผ่านการคัดเลือก"
    REJECTED = "ปฏิเสธแล้ว"
    NO_RESPONSE = "ไม่มีการตอบกลับ"


class JobApplication(Base):
    __tablename__ = "job_applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    company: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    position: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    job_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    location: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    work_mode: Mapped[WorkMode | None] = mapped_column(
        Enum(WorkMode, name="work_mode"),
        nullable=True,
    )

    date_applied: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status"),
        nullable=False,
    )

    salary: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )