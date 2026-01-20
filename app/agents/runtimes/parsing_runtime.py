"""Agent runtime for executing parsing tasks.

Provides async functions to run ADK agents in-process with
InMemorySessionService for stateless request handling.
"""

import base64
import json
import logging
import uuid

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agents.parsing.agent import create_parsing_agent
from app.agents.tools.parsing.pdf_docling import (
    chunk_text_by_tokens,
    extract_pdf_text,
    parse_pdf,
)

APP_NAME = "gabrr_budget"
logger = logging.getLogger(__name__)


async def _run_agent_with_payload(
    *,
    runner: Runner,
    session_service: InMemorySessionService,
    payload: dict,
    file_type: str,
    filename: str,
    model_id: str,
) -> list[dict]:
    # Generate unique session identifiers
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=json.dumps(payload))],
    )

    final_response = None
    last_content_text = None
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message,
    ):
        if event.content and event.content.parts:
            last_content_text = event.content.parts[0].text
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text
            break

    if not final_response:
        logger.error(
            "Agent returned no response",
            extra={
                "file_type": file_type,
                "upload_filename": filename,
                "model_id": model_id,
                "user_id": user_id,
                "session_id": session_id,
                "last_content_text": last_content_text,
            },
        )
        raise ValueError("Agent did not return a response")

    try:
        response_text = final_response.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])

        payload = json.loads(response_text)
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and isinstance(
            payload.get("transactions"), list
        ):
            return payload["transactions"]

        raise ValueError(
            "Expected list or object with 'transactions' list, "
            f"got {type(payload)}"
        )
    except json.JSONDecodeError as e:
        logger.exception(
            "Failed to parse agent response as JSON",
            extra={
                "file_type": file_type,
                "upload_filename": filename,
                "model_id": model_id,
                "user_id": user_id,
                "session_id": session_id,
                "response_text": response_text,
            },
        )
        raise ValueError(f"Failed to parse agent response as JSON: {e}")


async def run_parsing_agent_raw(
    file_type: str,
    filename: str,
    file_bytes: bytes,
    model_id: str = "openai:gpt-oss-120b:free",
) -> list[dict]:
    """Run the parsing agent on a file and return raw transactions.

    Args:
        file_type: Type of file ("csv" or "pdf")
        filename: Original filename
        file_bytes: Raw file content bytes
        model_id: Model identifier in "provider:model" format

    Returns:
        List of raw transaction dictionaries

    Raises:
        ValueError: If parsing fails or agent returns invalid response
    """
    agent = create_parsing_agent(model_id=model_id)
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    content_b64 = base64.b64encode(file_bytes).decode("utf-8")
    payload = {
        "file_type": file_type,
        "filename": filename,
        "content_b64": content_b64,
    }
    return await _run_agent_with_payload(
        runner=runner,
        session_service=session_service,
        payload=payload,
        file_type=file_type,
        filename=filename,
        model_id=model_id,
    )


async def run_parsing_agent_pdf_chunks(
    filename: str,
    file_bytes: bytes,
    model_id: str = "openai:gpt-oss-120b:free",
    chunk_tokens: int = 30000,
    overlap_tokens: int = 800,
) -> list[dict]:
    """Run the parsing agent on PDF text in chunks."""
    text = extract_pdf_text(file_bytes)
    if not text.strip():
        logger.warning(
            "PDF text extraction returned empty content; falling back to direct parsing",
            extra={
                "upload_filename": filename,
                "model_id": model_id,
            },
        )
        content_b64 = base64.b64encode(file_bytes).decode("utf-8")
        return parse_pdf(content_b64)

    chunks = chunk_text_by_tokens(
        text,
        model_id=model_id,
        chunk_tokens=chunk_tokens,
        overlap_tokens=overlap_tokens,
    )
    logger.info(
        "Running PDF parsing in chunks",
        extra={
            "upload_filename": filename,
            "model_id": model_id,
            "chunk_count": len(chunks),
            "chunk_tokens": chunk_tokens,
            "overlap_tokens": overlap_tokens,
            "text_char_count": len(text),
        },
    )

    agent = create_parsing_agent(model_id=model_id)
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    transactions: list[dict] = []
    for idx, chunk in enumerate(chunks):
        payload = {
            "file_type": "pdf",
            "filename": filename,
            "content_text": chunk,
            "chunk_index": idx,
            "chunk_count": len(chunks),
        }
        chunk_transactions = await _run_agent_with_payload(
            runner=runner,
            session_service=session_service,
            payload=payload,
            file_type="pdf",
            filename=filename,
            model_id=model_id,
        )
        transactions.extend(chunk_transactions)

    return transactions
