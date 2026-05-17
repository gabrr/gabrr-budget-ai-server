"""Local PDF persistence under data/uploads/{user_id}/."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Literal


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _user_upload_directory(user_id: str) -> Path:
    return _backend_root() / "data" / "uploads" / user_id


PDF_FILE_MAGIC_PREFIX = b"%PDF-"
ALLOWED_PDF_CONTENT_TYPES = frozenset({"application/pdf", "application/x-pdf"})


class FileSystemService:
    """Write uploads to disk; replace with remote storage when needed."""

    def _ensure_pdf_or_raise(
        self,
        original_filename: str,
        content_type: str | None,
        uploaded_bytes: bytes,
        *,
        accepts: Literal["pdf"],
    ) -> None:
        if accepts != "pdf":
            raise ValueError("Only accepts='pdf' is supported for now.")

        filename_lower = original_filename.lower()
        if not filename_lower.endswith(".pdf"):
            raise ValueError("Only PDF uploads are accepted (filename must end with .pdf).")

        normalized_content_type = (content_type or "").lower()
        if normalized_content_type and normalized_content_type not in ALLOWED_PDF_CONTENT_TYPES:
            raise ValueError("Only PDF uploads are accepted (unexpected Content-Type).")

        if not uploaded_bytes.startswith(PDF_FILE_MAGIC_PREFIX):
            raise ValueError("Only PDF uploads are accepted (file does not look like a PDF).")

    async def save(
        self,
        uploaded_bytes: bytes,
        *,
        original_filename: str,
        content_type: str | None,
        user_id: str,
        accepts: Literal["pdf"],
    ) -> str:
        self._ensure_pdf_or_raise(
            original_filename,
            content_type,
            uploaded_bytes,
            accepts=accepts,
        )

        user_upload_directory = _user_upload_directory(user_id)
        user_upload_directory.mkdir(parents=True, exist_ok=True)

        filename_stem = Path(original_filename or "upload").stem
        destination_path = user_upload_directory / f"{uuid.uuid4().hex}_{filename_stem}.pdf"
        destination_path.write_bytes(uploaded_bytes)

        return str(destination_path.resolve())
