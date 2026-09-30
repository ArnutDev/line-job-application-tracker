from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.repositories import job_application as repository
from app.schemas.job_application import (
    JobApplicationCreate,
    JobApplicationResponse,
    JobApplicationUpdate,
)

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
    db: Session = Depends(get_db),
):
    user_id = UUID("00000000-0000-0000-0000-000000000001")

    return repository.get_applications(
        db=db,
        user_id=user_id,
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