"""PDF parsing tool using Docling for transaction extraction.

Extracts tables and text from PDF bank statements and financial documents.
"""

import base64
import re
import tempfile
from pathlib import Path

from litellm import token_counter

from docling.document_converter import DocumentConverter

from app.core.llm.interface import ModelId


def _extract_amount_from_text(text: str) -> float | None:
    """Try to extract a numeric amount from text.

    Args:
        text: Text that might contain an amount

    Returns:
        Extracted amount or None
    """
    if not text:
        return None

    # Look for patterns like $1,234.56 or 1.234,56 or (123.45)
    patterns = [
        r"[\$€£R\$¥₹]?\s*\(?([\d,\.]+)\)?",  # Currency symbol with number
        r"([\d,\.]+)",  # Just numbers
    ]

    for pattern in patterns:
        match = re.search(pattern, text.strip())
        if match:
            value = match.group(1)
            # Clean and parse
            cleaned = value.replace(",", "").replace(" ", "")
            try:
                amount = float(cleaned)
                # Check for parentheses indicating negative
                if "(" in text and ")" in text:
                    amount = -abs(amount)
                return amount
            except ValueError:
                continue

    return None


def _looks_like_date(text: str) -> bool:
    """Check if text looks like a date.

    Args:
        text: Text to check

    Returns:
        True if it looks like a date
    """
    if not text:
        return False

    # Common date patterns
    date_patterns = [
        r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
        r"\d{2}/\d{2}/\d{4}",  # DD/MM/YYYY or MM/DD/YYYY
        r"\d{2}-\d{2}-\d{4}",  # DD-MM-YYYY
        r"\d{2}/\d{2}/\d{2}",  # DD/MM/YY
        r"\d{1,2}\s+\w{3}\s+\d{4}",  # 1 Jan 2024
    ]

    for pattern in date_patterns:
        if re.search(pattern, text.strip()):
            return True

    return False


def _process_table(table_data: list[list[str]]) -> list[dict]:
    """Process a table and extract transactions.

    Args:
        table_data: List of rows, each row is a list of cell values

    Returns:
        List of transaction dictionaries
    """
    if not table_data or len(table_data) < 2:
        return []

    transactions = []

    # Try to identify columns from header row
    header = [str(cell).lower().strip() for cell in table_data[0]]

    date_idx = None
    desc_idx = None
    amount_idx = None

    for idx, col in enumerate(header):
        if any(d in col for d in ["date", "data", "posted"]):
            date_idx = idx
        elif any(
            d in col for d in ["description", "desc", "memo", "particular", "detail"]
        ):
            desc_idx = idx
        elif any(d in col for d in ["amount", "value", "total", "debit", "credit"]):
            amount_idx = idx

    # Process data rows
    for row in table_data[1:]:
        if not row or len(row) == 0:
            continue

        # Try to extract based on identified columns or heuristics
        date_val = None
        desc_val = None
        amount_val = None

        for idx, cell in enumerate(row):
            cell_str = str(cell).strip() if cell else ""

            if date_idx is not None and idx == date_idx:
                date_val = cell_str
            elif desc_idx is not None and idx == desc_idx:
                desc_val = cell_str
            elif amount_idx is not None and idx == amount_idx:
                amount_val = _extract_amount_from_text(cell_str)
            elif _looks_like_date(cell_str) and date_val is None:
                date_val = cell_str
            elif amount_val is None and _extract_amount_from_text(cell_str) is not None:
                amount_val = _extract_amount_from_text(cell_str)
            elif (
                desc_val is None
                and len(cell_str) > 5
                and not cell_str.replace(".", "").replace(",", "").isdigit()
            ):
                desc_val = cell_str

        if desc_val or amount_val is not None:
            transactions.append(
                {
                    "date": date_val,
                    "description": desc_val or "",
                    "amount": amount_val,
                    "currency": None,
                    "merchant_raw": desc_val,
                    "source": "pdf",
                }
            )

    return transactions


def _extract_transactions_from_text(text: str) -> list[dict]:
    """Extract transactions from text lines using simple heuristics."""
    if not text:
        return []

    transactions = []
    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        if not line or len(line) < 10:
            continue

        # Look for lines with dates and amounts
        if _looks_like_date(line):
            amount = _extract_amount_from_text(line)
            if amount is not None:
                # Extract date from start of line
                date_match = re.search(r"(\d{2}[/-]\d{2}[/-]\d{2,4})", line)
                date_val = date_match.group(1) if date_match else None

                # Rest of line is description
                desc = re.sub(r"[\$€£]?\s*[\d,\.]+", "", line).strip()
                desc = re.sub(r"\d{2}[/-]\d{2}[/-]\d{2,4}", "", desc).strip()

                transactions.append(
                    {
                        "date": date_val,
                        "description": desc[:100] if desc else "Unknown transaction",
                        "amount": amount,
                        "currency": None,
                        "merchant_raw": desc[:50] if desc else None,
                        "source": "pdf",
                    }
                )

    return transactions


def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract markdown text from a PDF using Docling."""
    if not file_bytes:
        return ""

    # Write to temp file for Docling
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_file.write(file_bytes)
        tmp_path = Path(tmp_file.name)

    try:
        converter = DocumentConverter()
        result = converter.convert(tmp_path)
        if hasattr(result, "document") and hasattr(result.document, "export_to_markdown"):
            return result.document.export_to_markdown()
        return ""
    finally:
        try:
            tmp_path.unlink()
        except Exception:
            pass


def _tokenizer_model(model_id: str) -> str:
    try:
        parsed = ModelId.from_string(model_id)
        return parsed.model
    except ValueError:
        return model_id


def _find_max_end(
    text: str,
    start: int,
    max_tokens: int,
    model_name: str,
) -> int:
    low = start + 1
    high = len(text)
    best = start

    while low <= high:
        mid = (low + high) // 2
        tokens = token_counter(model=model_name, text=text[start:mid])
        if tokens <= max_tokens:
            best = mid
            low = mid + 1
        else:
            high = mid - 1

    return best


def _find_overlap_start(
    text: str,
    start_bound: int,
    end: int,
    overlap_tokens: int,
    model_name: str,
) -> int:
    if overlap_tokens <= 0:
        return end

    low = start_bound
    high = end
    best = end

    while low <= high:
        mid = (low + high) // 2
        tokens = token_counter(model=model_name, text=text[mid:end])
        if tokens > overlap_tokens:
            low = mid + 1
        else:
            best = mid
            high = mid - 1

    return best


def chunk_text_by_tokens(
    text: str,
    model_id: str,
    chunk_tokens: int = 60000,
    overlap_tokens: int = 1000,
) -> list[str]:
    """Split text into token-sized chunks with overlap."""
    if not text or not text.strip():
        return []
    if chunk_tokens <= 0:
        raise ValueError("chunk_tokens must be greater than 0")
    if overlap_tokens < 0:
        raise ValueError("overlap_tokens must be >= 0")
    if overlap_tokens >= chunk_tokens:
        raise ValueError("overlap_tokens must be smaller than chunk_tokens")

    model_name = _tokenizer_model(model_id)
    total_tokens = token_counter(model=model_name, text=text)
    if total_tokens <= chunk_tokens:
        return [text]

    chunks: list[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = _find_max_end(text, start, chunk_tokens, model_name)
        if end <= start:
            end = min(text_len, start + 1000)

        chunks.append(text[start:end])
        if end >= text_len:
            break

        next_start = _find_overlap_start(text, start, end, overlap_tokens, model_name)
        if next_start <= start:
            next_start = min(text_len, end - 1)
        start = next_start

    return chunks


def parse_pdf_text(content_text: str) -> list[dict]:
    """Parse PDF text content and extract transactions."""
    print("--- Tool: parse_pdf_text called ---")
    transactions = _extract_transactions_from_text(content_text or "")
    print(f"--- Tool: Extracted {len(transactions)} transactions from PDF text ---")
    return transactions


def parse_pdf(content_b64: str) -> list[dict]:
    """Parse PDF content and extract transactions.

    Uses Docling for PDF processing, prioritizing table extraction
    when available.

    Args:
        content_b64: Base64-encoded PDF content

    Returns:
        List of raw transaction dictionaries with keys:
        - date, description, amount, currency, merchant_raw, source
    """
    print("--- Tool: parse_pdf called ---")

    if not content_b64:
        print("--- Tool: Empty PDF content received ---")
        return []

    # Decode base64 content
    try:
        content_bytes = base64.b64decode(content_b64)
    except Exception as e:
        print(f"--- Tool: Failed to decode PDF: {e} ---")
        return []

    # Write to temp file for Docling
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_file.write(content_bytes)
        tmp_path = Path(tmp_file.name)

    transactions = []

    try:
        # Use Docling to convert PDF
        converter = DocumentConverter()
        result = converter.convert(tmp_path)

        # Try to extract tables first
        if hasattr(result, "document") and hasattr(result.document, "tables"):
            for table in result.document.tables:
                if hasattr(table, "data"):
                    table_transactions = _process_table(table.data.grid)
                    transactions.extend(table_transactions)

        # If no tables found, try text extraction
        if not transactions:
            text = (
                result.document.export_to_markdown()
                if hasattr(result.document, "export_to_markdown")
                else ""
            )
            transactions = _extract_transactions_from_text(text)

    except Exception as e:
        print(f"--- Tool: Error processing PDF: {e} ---")
    finally:
        # Clean up temp file
        try:
            tmp_path.unlink()
        except Exception:
            pass

    print(f"--- Tool: Extracted {len(transactions)} transactions from PDF ---")
    return transactions
