import logging
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile
from docling.document_converter import DocumentConverter

from app.utils.files import writeToExternalMd

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
    converter = DocumentConverter()
    suffix = Path(file.filename).suffix if file.filename else ""

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = temp_file.name
            temp_file.write(await file.read())

        result = converter.convert(temp_path)
        markdown = result.document.export_to_markdown()

        writeToExternalMd(markdown, file.filename)

        logger.info("Parsed document to markdown (%s bytes)", len(markdown))

        return {"status": "All good", "markdown": markdown}
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)