"""FastAPI application for Gabrr Budget transaction parsing.

Exposes endpoints for parsing CSV and PDF financial documents
into normalized transaction records using an AI agent.
"""

import logging

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.agents.pipelines.parsing_pipeline import run_parsing_agent
from app.agents.schemas.transactions import ParseError
from app.core.config import settings

app = FastAPI(
    title="Gabrr Budget API",
    description="Parse financial documents (CSV/PDF) into normalized transactions",
    version="0.1.0",
)
logger = logging.getLogger(__name__)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        Status object indicating the service is healthy
    """
    return {"status": "ok"}


@app.post("/parse")
async def parse_file(
    file: UploadFile,
    model_id: str = "openai:gpt-oss-120b:free",
) -> list[dict]:
    """Parse a financial document and extract transactions.

    Accepts CSV or PDF files and returns a list of normalized
    transaction records.

    Args:
        file: Uploaded file (multipart/form-data, field name = "file")
        model_id: Optional model identifier in "provider:model" format.
            Defaults to "openai:gpt-oss-120b:free".
            Examples: "openai:gpt-4o", "anthropic:claude-3.5-sonnet"

    Returns:
        List of transaction objects with:
        - date: YYYY-MM-DD or null
        - description: string
        - amount: number
        - currency: string or null
        - merchant_raw: string or null
        - source: "csv" or "pdf"

    Raises:
        HTTPException 415: Unsupported file type (not .csv or .pdf)
        HTTPException 413: File too large (exceeds MAX_UPLOAD_MB)
        HTTPException 400: Parse failed
    """
    # Validate filename exists
    if not file.filename:
        raise HTTPException(
            status_code=415,
            detail="No filename provided",
        )

    # Validate file extension
    filename_lower = file.filename.lower()
    if filename_lower.endswith(".csv"):
        file_type = "csv"
    elif filename_lower.endswith(".pdf"):
        file_type = "pdf"
    else:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type. Only .csv and .pdf files are accepted. Got: {file.filename}",
        )

    # Read file content with size validation
    file_bytes = b""
    try:
        while True:
            chunk = await file.read(1024 * 1024)  # Read 1MB at a time
            if not chunk:
                break
            file_bytes += chunk

            # Check size limit
            if len(file_bytes) > settings.max_upload_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size is {settings.max_upload_mb}MB",
                )
    finally:
        await file.close()

    # Validate file is not empty
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file uploaded",
        )

    # Run parsing agent
    try:
        transactions = await run_parsing_agent(
            file_type=file_type,
            filename=file.filename,
            file_bytes=file_bytes,
            model_id=model_id,
        )
        return transactions

    except ValueError as e:
        # Parsing or validation error
        logger.exception(
            "Parsing failed",
            extra={
                "upload_filename": file.filename,
                "file_type": file_type,
                "model_id": model_id,
                "file_size_bytes": len(file_bytes),
            },
        )
        error = ParseError(error="PARSE_FAILED", detail=str(e))
        return JSONResponse(
            status_code=400,
            content=error.model_dump(),
        )
    except Exception as e:
        # Unexpected error
        logger.exception(
            "Unexpected parsing error",
            extra={
                "upload_filename": file.filename,
                "file_type": file_type,
                "model_id": model_id,
                "file_size_bytes": len(file_bytes),
            },
        )
        error = ParseError(error="PARSE_FAILED", detail=f"Unexpected error: {str(e)}")
        return JSONResponse(
            status_code=400,
            content=error.model_dump(),
        )
