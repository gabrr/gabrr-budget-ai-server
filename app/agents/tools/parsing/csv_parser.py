"""CSV parsing tool for transaction extraction.

Handles various CSV formats with fuzzy column matching.
"""

import base64
import csv
from io import StringIO


# Column name variations for fuzzy matching
DATE_COLUMNS = [
    "date",
    "data",
    "posted",
    "transaction date",
    "trans date",
    "posting date",
]
DESCRIPTION_COLUMNS = [
    "description",
    "desc",
    "memo",
    "historico",
    "details",
    "merchant",
    "narrative",
    "particulars",
]
AMOUNT_COLUMNS = ["amount", "value", "valor", "total", "sum"]
DEBIT_COLUMNS = ["debit", "debito", "withdrawal", "out"]
CREDIT_COLUMNS = ["credit", "credito", "deposit", "in"]
CURRENCY_COLUMNS = ["currency", "moeda", "ccy"]
MERCHANT_COLUMNS = ["merchant", "payee", "vendor", "recipient"]


def _find_column(headers: list[str], candidates: list[str]) -> str | None:
    """Find a matching column name using fuzzy matching.

    Args:
        headers: List of column headers from the CSV
        candidates: List of candidate column names to match

    Returns:
        The matching header name, or None if not found
    """
    headers_lower = {h.lower().strip(): h for h in headers}
    for candidate in candidates:
        if candidate in headers_lower:
            return headers_lower[candidate]
    return None


def _parse_amount_value(value: str | None) -> float | None:
    """Parse a raw amount string to float.

    Args:
        value: Raw amount string

    Returns:
        Parsed float or None if invalid
    """
    if not value:
        return None

    # Remove currency symbols and whitespace
    cleaned = value.strip()
    for char in ["$", "€", "£", "R$", "¥", "₹", " "]:
        cleaned = cleaned.replace(char, "")

    if not cleaned:
        return None

    # Handle parentheses as negative
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]

    # Detect decimal separator
    # If both , and . exist, the last one is decimal separator
    has_comma = "," in cleaned
    has_dot = "." in cleaned

    if has_comma and has_dot:
        # Find which comes last
        last_comma = cleaned.rfind(",")
        last_dot = cleaned.rfind(".")
        if last_comma > last_dot:
            # European format: 1.234,56
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            # US format: 1,234.56
            cleaned = cleaned.replace(",", "")
    elif has_comma:
        # Could be thousands separator or decimal
        # If exactly 3 digits after comma, it's thousands
        parts = cleaned.split(",")
        if len(parts) == 2 and len(parts[1]) == 3:
            cleaned = cleaned.replace(",", "")
        else:
            cleaned = cleaned.replace(",", ".")
    # If only dot, assume it's decimal (default)

    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_csv(content_b64: str) -> list[dict]:
    """Parse CSV content and extract transactions.

    Args:
        content_b64: Base64-encoded CSV content

    Returns:
        List of raw transaction dictionaries with keys:
        - date, description, amount, currency, merchant_raw, source
    """
    print("--- Tool: parse_csv called ---")

    # Decode base64 content
    try:
        content_bytes = base64.b64decode(content_b64)
        content = content_bytes.decode("utf-8")
    except Exception as e:
        print(f"--- Tool: Failed to decode CSV: {e} ---")
        return []

    # Parse CSV
    reader = csv.DictReader(StringIO(content))
    headers = reader.fieldnames or []

    # Find column mappings
    date_col = _find_column(headers, DATE_COLUMNS)
    desc_col = _find_column(headers, DESCRIPTION_COLUMNS)
    amount_col = _find_column(headers, AMOUNT_COLUMNS)
    debit_col = _find_column(headers, DEBIT_COLUMNS)
    credit_col = _find_column(headers, CREDIT_COLUMNS)
    currency_col = _find_column(headers, CURRENCY_COLUMNS)
    merchant_col = _find_column(headers, MERCHANT_COLUMNS)

    print(
        f"--- Tool: Column mappings - date:{date_col}, desc:{desc_col}, amount:{amount_col} ---"
    )

    transactions = []
    for row in reader:
        # Extract date
        date_value = row.get(date_col) if date_col else None

        # Extract description (try multiple columns)
        description = None
        if desc_col:
            description = row.get(desc_col)
        if not description and merchant_col:
            description = row.get(merchant_col)
        if not description:
            # Use first non-empty text field
            for key, val in row.items():
                if val and key not in [
                    date_col,
                    amount_col,
                    debit_col,
                    credit_col,
                    currency_col,
                ]:
                    description = val
                    break
        description = (description or "").strip()

        # Extract amount
        amount = None
        if amount_col:
            amount = _parse_amount_value(row.get(amount_col))
        elif debit_col or credit_col:
            # Combine debit/credit columns
            debit = _parse_amount_value(row.get(debit_col)) if debit_col else None
            credit = _parse_amount_value(row.get(credit_col)) if credit_col else None
            if debit and credit:
                amount = credit - debit
            elif debit:
                amount = -abs(debit)
            elif credit:
                amount = abs(credit)

        # Extract currency
        currency = row.get(currency_col) if currency_col else None

        # Extract merchant
        merchant_raw = row.get(merchant_col) if merchant_col else description

        # Only add if we have meaningful data
        if description or amount is not None:
            transactions.append(
                {
                    "date": date_value,
                    "description": description,
                    "amount": amount,
                    "currency": currency,
                    "merchant_raw": merchant_raw,
                    "source": "csv",
                }
            )

    print(f"--- Tool: Extracted {len(transactions)} transactions from CSV ---")
    return transactions
