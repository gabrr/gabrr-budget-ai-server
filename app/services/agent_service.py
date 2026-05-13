"""HTTP client for Google ADK `adk api_server` (see agent-normalizer `make api`)."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any, Literal

from typing_extensions import TypedDict

import httpx

logger = logging.getLogger(__name__)

Status = Literal["success", "error"]


class AgentJsonRun(TypedDict):
    status: Status
    data: dict[str, Any]


def _text_from_event(event: dict[str, Any]) -> str:
    """Concatenate all plain text parts from one ADK event's content."""
    content = event.get("content") or {}
    parts = content.get("parts") or []
    texts: list[str] = []
    for part in parts:
        if isinstance(part, dict) and part.get("text"):
            texts.append(part["text"])
    return "".join(texts).strip()


def _final_text_from_events(events: list[dict[str, Any]]) -> str:
    """Final assistant text from ADK /run event list (last event, per api-server docs)."""
    if not events:
        return ""
    return _text_from_event(events[-1])


def _parse_agent_json_object(text: str) -> dict[str, Any] | None:
    """Return dict if text is valid JSON object; else None."""
    if not text or not text.strip():
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict):
        return parsed
    return None


def envelope_error() -> AgentJsonRun:
    return {"status": "error", "data": {}}


def envelope_success(data: dict[str, Any]) -> AgentJsonRun:
    return {"status": "success", "data": data}


class AgentService:
    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        base_url: str,
        app_name: str,
        user_id: str,
    ) -> None:
        self._client = client
        self._base = base_url.rstrip("/")
        self._app_name = app_name
        self._user_id = user_id

    async def create_session(self, session_id: str | None = None) -> str:
        url = f"{self._base}/apps/{self._app_name}/users/{self._user_id}/sessions"
        payload: dict[str, Any] | None = (
            None if session_id is None else {"session_id": session_id}
        )
        response = await self._client.post(
            url, json=payload if payload is not None else {}
        )
        response.raise_for_status()
        session_create_body = response.json()
        adk_session_id = session_create_body.get("id")
        if not isinstance(adk_session_id, str) or not adk_session_id:
            raise ValueError("ADK create_session response missing string id")
        return adk_session_id

    def _run_payload(self, session_id: str, prompt: str) -> dict[str, Any]:
        return {
            "app_name": self._app_name,
            "user_id": self._user_id,
            "session_id": session_id,
            "new_message": {"role": "user", "parts": [{"text": prompt}]},
        }

    async def run_text(self, session_id: str, prompt: str) -> str:
        response = await self._client.post(
            f"{self._base}/run", json=self._run_payload(session_id, prompt)
        )
        response.raise_for_status()
        events = response.json()
        if not isinstance(events, list):
            return ""
        return _final_text_from_events(events)

    async def run_json(self, session_id: str, prompt: str) -> AgentJsonRun:
        """Always returns {status, data}. Never raises for bad agent JSON."""
        try:
            text = await self.run_text(session_id, prompt)
        except httpx.HTTPError as http_error:
            logger.warning("AgentService HTTP error: %s", http_error)
            return envelope_error()

        parsed = _parse_agent_json_object(text)
        if parsed is None:
            logger.warning(
                "AgentService run_json: invalid or non-object JSON (truncated): %s",
                text[:500],
            )
            return envelope_error()
        return envelope_success(parsed)

    def _sse_run_payload(self, session_id: str, prompt: str) -> dict[str, Any]:
        return {**self._run_payload(session_id, prompt), "streaming": True}

    async def stream_run_sse(
        self, session_id: str, prompt: str
    ) -> AsyncIterator[str]:
        """Stream ADK `text/event-stream` body as opaque text lines."""
        payload = self._sse_run_payload(session_id, prompt)
        async with self._client.stream(
            "POST", f"{self._base}/run_sse", json=payload
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    yield line
