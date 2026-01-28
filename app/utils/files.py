from pathlib import Path
from typing import Literal

from fastapi import HTTPException, UploadFile


def detect_file_type(filename: str) -> Literal["csv", "pdf"]:
    filename_lower = filename.lower()

    if filename_lower.endswith(".csv"):
        return "csv"
    if filename_lower.endswith(".pdf"):
        return "pdf"

    raise HTTPException(
        status_code=415,
        detail=(
            "Unsupported file type. Only .csv and .pdf files are accepted. "
            f"Got: {filename}"
        ),
    )


async def read_upload_bytes(
    file: UploadFile,
    max_bytes: int,
    max_mb: int,
) -> bytes:
    file_bytes = b""
    try:
        while True:
            chunk = await file.read(1024 * 1024)  # Read 1MB at a time
            if not chunk:
                break
            file_bytes += chunk

            if len(file_bytes) > max_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size is {max_mb}MB",
                )
    finally:
        await file.close()

    return file_bytes


def ensure_not_empty(file_bytes: bytes) -> None:
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file uploaded",
        )


def writeToExternalMd(file_bytes: bytes, filename: str | None) -> Path:
    base_dir = Path(__file__).resolve().parents[2]
    md_dir = base_dir / "md_files"
    md_dir.mkdir(parents=True, exist_ok=True)

    stem = Path(filename).stem if filename else "upload"
    target_path = md_dir / f"{stem}.md"

    with target_path.open("ab") as output_file:
        output_file.write(file_bytes)

    return target_path
