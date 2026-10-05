from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.repositories import job_application as repository
from app.schemas.job_application import (
    JobApplicationCreate,
    JobApplicationResponse,
    JobApplicationSummaryResponse,
    JobApplicationUpdate,
)
from app.services import export_service


router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)


@router.post(
    "",
    response_model=JobApplicationResponse,
)
def create_application(
    data: JobApplicationCreate,
    db: Session = Depends(get_db),
):
    # Temporary user ID for testing.
    # We will replace this with LINE user resolution later.
    user_id = UUID("00000000-0000-0000-0000-000000000001")

    application = repository.create_application(
        db=db,
        user_id=user_id,
        data=data.model_dump(),
    )

    return application


@router.get(
    "",
    response_model=list[JobApplicationResponse],
)
def get_applications(
    status: str | None = Query(default=None, description="กรองตามสถานะ"),
    company: str | None = Query(default=None, description="กรองตามบริษัท"),
    position: str | None = Query(default=None, description="กรองตามตำแหน่ง"),
    work_mode: str | None = Query(
        default=None,
        description="กรองตามรูปแบบการทำงาน (onsite, hybrid, remote, unknown)",
    ),
    date_from: date | None = Query(default=None, description="วันที่เริ่มต้น YYYY-MM-DD"),
    date_to: date | None = Query(default=None, description="วันที่สิ้นสุด YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    user_id = UUID("00000000-0000-0000-0000-000000000001")

    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=400,
            detail="date_from must not be greater than date_to",
        )

    return repository.get_applications(
        db=db,
        user_id=user_id,
        status=status,
        company=company,
        position=position,
        work_mode=work_mode,
        date_from=date_from,
        date_to=date_to,
    )


@router.get(
    "/summary",
    response_model=JobApplicationSummaryResponse,
)
def get_application_summary(
    status: str | None = Query(default=None, description="กรองตามสถานะ"),
    company: str | None = Query(default=None, description="กรองตามบริษัท"),
    position: str | None = Query(default=None, description="กรองตามตำแหน่ง"),
    work_mode: str | None = Query(
        default=None,
        description="กรองตามรูปแบบการทำงาน (onsite, hybrid, remote, unknown)",
    ),
    date_from: date | None = Query(default=None, description="วันที่เริ่มต้น YYYY-MM-DD"),
    date_to: date | None = Query(default=None, description="วันที่สิ้นสุด YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    user_id = UUID("00000000-0000-0000-0000-000000000001")

    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=400,
            detail="date_from must not be greater than date_to",
        )

    return repository.get_application_summary(
        db=db,
        user_id=user_id,
        status=status,
        company=company,
        position=position,
        work_mode=work_mode,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/export")
def export_applications(
    status: str | None = Query(default=None, description="กรองตามสถานะ"),
    company: str | None = Query(default=None, description="กรองตามบริษัท"),
    position: str | None = Query(default=None, description="กรองตามตำแหน่ง"),
    work_mode: str | None = Query(
        default=None,
        description="กรองตามรูปแบบการทำงาน (onsite, hybrid, remote, unknown)",
    ),
    date_from: date | None = Query(default=None, description="วันที่เริ่มต้น YYYY-MM-DD"),
    date_to: date | None = Query(default=None, description="วันที่สิ้นสุด YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    user_id = UUID("00000000-0000-0000-0000-000000000001")

    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=400,
            detail="date_from must not be greater than date_to",
        )

    applications = repository.get_applications(
        db=db,
        user_id=user_id,
        status=status,
        company=company,
        position=position,
        work_mode=work_mode,
        date_from=date_from,
        date_to=date_to,
    )

    file_stream = export_service.export_applications_to_xlsx(applications)

    headers = {
        "Content-Disposition": "attachment; filename=job_applications.xlsx",
    }

    return StreamingResponse(
        file_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get(

    "/{application_id}",
    response_model=JobApplicationResponse,
)
def get_application(
    application_id: UUID,
    db: Session = Depends(get_db),
):
    user_id = UUID("00000000-0000-0000-0000-000000000001")

    application = repository.get_application(
        db=db,
        user_id=user_id,
        application_id=application_id,
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return application

@router.patch(
    "/{application_id}",
    response_model=JobApplicationResponse,
)
def update_application(
    application_id: UUID,
    data: JobApplicationUpdate,
    db: Session = Depends(get_db),
):
    user_id = UUID("00000000-0000-0000-0000-000000000001")

    application = repository.get_application(
        db=db,
        user_id=user_id,
        application_id=application_id,
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    update_data = data.model_dump(exclude_unset=True)

    return repository.update_application(
        db=db,
        application=application,
        data=update_data,
    )

@router.delete("/{application_id}")
def delete_application(
    application_id: UUID,
    db: Session = Depends(get_db),
):
    user_id = UUID("00000000-0000-0000-0000-000000000001")

    application = repository.get_application(
        db=db,
        user_id=user_id,
        application_id=application_id,
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    repository.delete_application(
        db=db,
        application=application,
    )

    return {
        "message": "Application deleted successfully"
    }