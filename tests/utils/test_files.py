import asyncio
from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile

from app.utils.files import detect_file_type, ensure_not_empty, read_upload_bytes


def make_upload_file(filename: str, content: bytes) -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(content))


def test_detect_file_type_csv_pdf() -> None:
    assert detect_file_type("statement.csv") == "csv"
    assert detect_file_type("statement.PDF") == "pdf"


def test_detect_file_type_invalid() -> None:
    with pytest.raises(HTTPException) as exc:
        detect_file_type("statement.txt")
    assert exc.value.status_code == 415


def test_read_upload_bytes_limit() -> None:
    file = make_upload_file("statement.csv", b"012345")
    with pytest.raises(HTTPException) as exc:
        asyncio.run(read_upload_bytes(file, max_bytes=2, max_mb=0))
    assert exc.value.status_code == 413


def test_read_upload_bytes_success() -> None:
    file = make_upload_file("statement.csv", b"abc")
    assert asyncio.run(read_upload_bytes(file, max_bytes=10, max_mb=1)) == b"abc"


def test_ensure_not_empty() -> None:
    with pytest.raises(HTTPException) as exc:
        ensure_not_empty(b"")
    assert exc.value.status_code == 400
