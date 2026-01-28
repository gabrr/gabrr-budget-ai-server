import logging

from fastapi import APIRouter, UploadFile


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        Status object indicating the service is healthy
    """
    return {"status": "ok"}


@router.post("/parse")
async def parse_file(file: UploadFile) -> dict:



    return {"status": "All good"}