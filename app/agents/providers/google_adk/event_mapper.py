from __future__ import annotations

from typing import Any

from app.agents.models import AgentProgressEvent


def map_google_adk_event_to_progress(event: dict[str, Any]) -> AgentProgressEvent | None:
    content = event.get("content") or {}
    parts = content.get("parts") or []

    if not isinstance(parts, list) or not parts:
        return None

    for part in parts:
        if not isinstance(part, dict):
            continue

        function_call = _get_function_call(part)
        if function_call is not None:
            return _function_call_to_progress(function_call)

        function_response = _get_function_response(part)
        if function_response is not None:
            return _function_response_to_progress(function_response)

        text = part.get("text")
        if isinstance(text, str) and text.strip():
            return _text_to_progress(text, event.get("author"))

    return None


def _get_function_call(part: dict[str, Any]) -> dict[str, Any] | None:
    function_call = part.get("function_call") or part.get("functionCall")
    return function_call if isinstance(function_call, dict) else None


def _get_function_response(part: dict[str, Any]) -> dict[str, Any] | None:
    function_response = part.get("function_response") or part.get("functionResponse")
    return function_response if isinstance(function_response, dict) else None


def _function_call_to_progress(function_call: dict[str, Any]) -> AgentProgressEvent | None:
    name = function_call.get("name")
    args = function_call.get("args") or {}

    if name == "transfer_to_agent":
        agent_name = args.get("agent_name")
        if agent_name == "statement_ingestion":
            return AgentProgressEvent(
                code="statement_ingestion.started",
                message="Starting statement ingestion",
            )
        return AgentProgressEvent(
            code="agent.pipeline_selecting",
            message="Choosing processing pipeline",
        )

    if name == "convert_statement_document_to_markdown":
        return AgentProgressEvent(code="pdf.converting", message="Converting PDF to Markdown")

    if name == "get_markdown_chunk":
        return None

    return None


def _function_response_to_progress(
    function_response: dict[str, Any],
) -> AgentProgressEvent | None:
    name = function_response.get("name")
    response = function_response.get("response") or {}
    if not isinstance(response, dict):
        return None

    status = response.get("status")

    if name == "convert_statement_document_to_markdown":
        if status == "success":
            return AgentProgressEvent(code="pdf.converted", message="PDF converted to Markdown")
        if status == "error":
            return AgentProgressEvent(code="pdf.conversion_failed", message="PDF conversion failed")

    if name == "get_markdown_chunk":
        if status != "success":
            return AgentProgressEvent(
                code="statement.chunk_failed",
                message="Reading statement chunk failed",
            )

        index = response.get("index")
        chunk_count = response.get("chunk_count")
        if isinstance(index, int) and isinstance(chunk_count, int):
            return AgentProgressEvent(
                code="statement.chunk_read",
                message=f"Reading statement chunk {index + 1} of {chunk_count}",
            )

        return AgentProgressEvent(
            code="statement.chunks_reading",
            message="Reading statement chunks",
        )

    return None


def _text_to_progress(text: str, author: object) -> AgentProgressEvent | None:
    stripped = text.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        return AgentProgressEvent(
            code="transactions.generating_json",
            message="Generating transaction JSON",
        )

    if author == "statement_converter":
        return AgentProgressEvent(
            code="statement.preparing",
            message="Preparing converted statement",
        )

    if author == "statement_normalizer":
        return AgentProgressEvent(
            code="transactions.normalizing",
            message="Normalizing transactions",
        )

    return None

