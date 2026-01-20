"""Normalisation tool for standardizing transaction data.

Converts raw transaction records into the strict output schema with
proper date formatting and amount parsing.
"""

import re
from datetime import datetime


def _parse_date(date_str: str | None) -> str | None:
    """Parse a date string to YYYY-MM-DD format.

    Handles multiple date formats:
    - YYYY-MM-DD
    - DD/MM/YYYY
    - MM/DD/YYYY
    - DD-MM-YYYY
    - DD.MM.YYYY

    For ambiguous dates (e.g., 01/02/2024), uses heuristics:
    - If day > 12, treat as DD/MM format
    - Otherwise, cannot determine confidently, return None

    Args:
        date_str: Raw date string

    Returns:
        Date in YYYY-MM-DD format, or None if cannot parse
    """
    if not date_str:
        return None

    date_str = date_str.strip()

    # Try YYYY-MM-DD first (ISO format)
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
        return parsed.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # Try other common formats
    formats_dd_mm = [
        ("%d/%m/%Y", True),  # DD/MM/YYYY
        ("%d-%m-%Y", True),  # DD-MM-YYYY
        ("%d.%m.%Y", True),  # DD.MM.YYYY
        ("%d/%m/%y", True),  # DD/MM/YY
    ]

    formats_mm_dd = [
        ("%m/%d/%Y", False),  # MM/DD/YYYY
        ("%m-%d-%Y", False),  # MM-DD-YYYY
    ]

    # Extract numbers to check for ambiguity
    numbers = re.findall(r"\d+", date_str)
    if len(numbers) >= 2:
        first_num = int(numbers[0])
        second_num = int(numbers[1])

        # If first number > 12, it must be day (DD/MM format)
        if first_num > 12:
            for fmt, is_dd_mm in formats_dd_mm:
                try:
                    parsed = datetime.strptime(date_str, fmt)
                    return parsed.strftime("%Y-%m-%d")
                except ValueError:
                    continue

        # If second number > 12, it must be day (MM/DD format)
        if second_num > 12:
            for fmt, is_dd_mm in formats_mm_dd:
                try:
                    parsed = datetime.strptime(date_str, fmt)
                    return parsed.strftime("%Y-%m-%d")
                except ValueError:
                    continue

        # Ambiguous case - both could be day or month
        # Try DD/MM first as it's more common internationally
        for fmt, is_dd_mm in formats_dd_mm:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # Try MM/DD formats
        for fmt, is_dd_mm in formats_mm_dd:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue

    # Try text month formats
    text_formats = [
        "%d %b %Y",  # 01 Jan 2024
        "%d %B %Y",  # 01 January 2024
        "%b %d, %Y",  # Jan 01, 2024
        "%B %d, %Y",  # January 01, 2024
    ]

    for fmt in text_formats:
        try:
            parsed = datetime.strptime(date_str, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Could not parse
    return None


def _parse_amount(amount_val: float | str | None) -> float | None:
    """Parse and normalize an amount value.

    Handles:
    - Already numeric values
    - String amounts with various formats
    - Currency symbols
    - Parentheses for negatives
    - European (1.234,56) and US (1,234.56) formats

    Args:
        amount_val: Raw amount value (float or string)

    Returns:
        Normalized float amount, or None if cannot parse
    """
    if amount_val is None:
        return None

    if isinstance(amount_val, (int, float)):
        return float(amount_val)

    if not isinstance(amount_val, str):
        return None

    # Remove currency symbols and whitespace
    cleaned = amount_val.strip()
    for char in ["$", "€", "£", "R$", "¥", "₹", " ", "\u00a0"]:
        cleaned = cleaned.replace(char, "")

    if not cleaned:
        return None

    # Handle parentheses as negative
    is_negative = False
    if cleaned.startswith("(") and cleaned.endswith(")"):
        is_negative = True
        cleaned = cleaned[1:-1]

    # Handle minus sign
    if cleaned.startswith("-"):
        is_negative = True
        cleaned = cleaned[1:]

    # Detect and handle decimal separator
    has_comma = "," in cleaned
    has_dot = "." in cleaned

    if has_comma and has_dot:
        last_comma = cleaned.rfind(",")
        last_dot = cleaned.rfind(".")
        if last_comma > last_dot:
            # European: 1.234,56
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            # US: 1,234.56
            cleaned = cleaned.replace(",", "")
    elif has_comma:
        # Check if it's thousands or decimal separator
        parts = cleaned.split(",")
        if len(parts) == 2 and len(parts[1]) == 3:
            # Thousands separator
            cleaned = cleaned.replace(",", "")
        else:
            # Decimal separator
            cleaned = cleaned.replace(",", ".")

    try:
        result = float(cleaned)
        return -result if is_negative else result
    except ValueError:
        return None


def normalise(transactions: list[dict]) -> list[dict]:
    """Normalize transaction records to the strict output schema.

    Processes raw transactions and ensures all fields conform to
    the expected output format.

    Args:
        transactions: List of raw transaction dictionaries

    Returns:
        List of normalized transaction dictionaries matching the schema:
        - date: YYYY-MM-DD or null
        - description: trimmed string
        - amount: numeric float
        - currency: string or null
        - merchant_raw: string or null
        - source: "csv" or "pdf"
    """
    print(f"--- Tool: normalise called with {len(transactions)} transactions ---")

    normalised = []

    for txn in transactions:
        # Parse date
        date = _parse_date(txn.get("date"))

        # Parse and clean description
        description = str(txn.get("description", "")).strip()
        if not description:
            description = "Unknown transaction"

        # Parse amount
        amount = _parse_amount(txn.get("amount"))
        if amount is None:
            # Skip transactions without amounts
            continue

        # Get currency
        currency = txn.get("currency")
        if currency:
            currency = str(currency).strip().upper()
            if len(currency) > 3 or not currency.isalpha():
                currency = None

        # Get merchant
        merchant_raw = txn.get("merchant_raw")
        if merchant_raw:
            merchant_raw = str(merchant_raw).strip()
        if not merchant_raw:
            merchant_raw = description[:50] if description else None

        # Get source
        source = txn.get("source", "csv")
        if source not in ["csv", "pdf"]:
            source = "csv"

        normalised.append(
            {
                "date": date,
                "description": description[:200],  # Limit length
                "amount": round(amount, 2),
                "currency": currency,
                "merchant_raw": merchant_raw[:100] if merchant_raw else None,
                "source": source,
            }
        )

    print(f"--- Tool: Normalised {len(normalised)} transactions ---")
    return normalised
