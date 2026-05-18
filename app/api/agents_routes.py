"""Agent upload routes."""

import hashlib

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.import_jobs_routes import import_job_to_public
from app.config import settings
from app.db.models.import_jobs import ImportJobPublic
from app.db.repositories.import_jobs import ImportJobRepository
from app.db.session import get_session
from app.services.file_storage_service import FileSystemService
from app.utils.files import ensure_not_empty, read_upload_bytes

agents_router = APIRouter(prefix="/agents", tags=["agents"])
_import_job_repository = ImportJobRepository()


def _sha256_bytes(uploaded_bytes: bytes) -> str:
    return hashlib.sha256(uploaded_bytes).hexdigest()


@agents_router.post("/process-file", response_model=None, status_code=202)
async def agent_process_file(
    file: UploadFile = File(...),
    user_id: str = Form(default=settings.default_user_id),
    idempotency_key: str = Header(alias="Idempotency-Key"),
    session: Session = Depends(get_session),
) -> ImportJobPublic | JSONResponse:
    maximum_bytes = settings.max_file_upload_bytes
    uploaded_bytes = await read_upload_bytes(file, maximum_bytes, settings.max_file_upload_mb)
    ensure_not_empty(uploaded_bytes)

    file_system_service = FileSystemService()
    file_hash = _sha256_bytes(uploaded_bytes)
    existing_job = _import_job_repository.get_by_idempotency_key(
        session,
        user_id=user_id,
        idempotency_key=idempotency_key,
    )

    if existing_job is not None:
        if existing_job.file_hash != file_hash:
            raise HTTPException(
                status_code=409,
                detail="Idempotency-Key reused with different file content.",
            )

        return JSONResponse(status_code=200, content=import_job_to_public(existing_job).model_dump())

    try:
        absolute_path = await file_system_service.save(
            uploaded_bytes,
            original_filename=file.filename or "upload.pdf",
            content_type=file.content_type,
            user_id=user_id,
            accepts="pdf",
        )

    except ValueError as error:
        raise HTTPException(status_code=415, detail=str(error)) from error

    try:
        job = _import_job_repository.create_pending(
            session,
            user_id=user_id,
            idempotency_key=idempotency_key,
            file_hash=file_hash,
            original_filename=file.filename,
            content_type=file.content_type,
            size_bytes=len(uploaded_bytes),
            storage_path=absolute_path,
        )

    except IntegrityError as error:
        session.rollback()
        file_system_service.delete_if_exists(absolute_path)
        if getattr(error.orig, "sqlstate", None) != "23505":
            raise HTTPException(
                status_code=422,
                detail="Upload user is not configured in the database.",
            ) from error

        existing_job = _import_job_repository.get_by_idempotency_key(
            session,
            user_id=user_id,
            idempotency_key=idempotency_key,
        )

        if existing_job is not None and existing_job.file_hash == file_hash:
            return JSONResponse(status_code=200, content=import_job_to_public(existing_job).model_dump())

        raise HTTPException(
            status_code=409,
            detail="Idempotency-Key reused with different file content.",
        ) from error

    except Exception:
        file_system_service.delete_if_exists(absolute_path)
        raise

    return import_job_to_public(job)
