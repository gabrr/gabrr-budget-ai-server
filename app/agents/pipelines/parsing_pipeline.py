"""Parsing pipeline orchestrating runtime and validation."""

from app.agents.runtimes.parsing_runtime import (
    run_parsing_agent_pdf_chunks,
    run_parsing_agent_raw,
)
from app.agents.schemas.transactions import Transaction
from app.agents.tools.parsing.normalise import normalise


def _validate_transactions(transactions: list[dict]) -> list[dict]:
    """Validate transactions against the strict schema."""
    validated: list[dict] = []
    for idx, txn in enumerate(transactions):
        try:
            model = Transaction.model_validate(txn)
        except Exception as e:
            raise ValueError(f"Transaction #{idx} failed validation: {e}")
        validated.append(model.model_dump())
    return validated


async def run_parsing_agent(
    file_type: str,
    filename: str,
    file_bytes: bytes,
    model_id: str = "openai:gpt-oss-120b:free",
) -> list[dict]:
    """Run the parsing agent and return normalized transactions.

    Args:
        file_type: Type of file ("csv" or "pdf")
        filename: Original filename
        file_bytes: Raw file content bytes
        model_id: Model identifier in "provider:model" format

    Returns:
        List of normalized transaction dictionaries

    Raises:
        ValueError: If parsing fails or agent returns invalid response
    """
    if file_type == "pdf":
        transactions = await run_parsing_agent_pdf_chunks(
            filename=filename,
            file_bytes=file_bytes,
            model_id=model_id,
        )
        transactions = normalise(transactions)
    else:
        transactions = await run_parsing_agent_raw(
            file_type=file_type,
            filename=filename,
            file_bytes=file_bytes,
            model_id=model_id,
        )
    return _validate_transactions(transactions)
