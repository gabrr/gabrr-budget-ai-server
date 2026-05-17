"""Agent HTTP helpers (ADK)."""

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import settings
from app.services.agent_service import AgentJsonRun, AgentService
from app.services.file_storage_service import FileSystemService
from app.utils.files import ensure_not_empty, read_upload_bytes

agents_router = APIRouter(prefix="/agents", tags=["agents"])


@agents_router.post("/process-file", response_model=None)
async def agent_process_file(
    file: UploadFile = File(...),
    user_id: str = Form(default=settings.default_user_id),
) -> AgentJsonRun:
    maximum_bytes = settings.max_file_upload_bytes
    uploaded_bytes = await read_upload_bytes(file, maximum_bytes, settings.max_file_upload_mb)
    ensure_not_empty(uploaded_bytes)

    file_system_service = FileSystemService()

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

    prompt = f"process this file: {absolute_path}"
    timeout = httpx.Timeout(settings.adk_timeout_seconds)

    async with httpx.AsyncClient(timeout=timeout) as client:
        agent_service = AgentService(
            client,
            base_url=settings.adk_base_url,
            app_name=settings.adk_app_name,
            user_id=user_id,
        )

        adk_session_id = await agent_service.create_session()

        return await agent_service.run_json(adk_session_id, prompt)
