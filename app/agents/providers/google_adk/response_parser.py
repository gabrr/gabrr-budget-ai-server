from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def google_adk_event_from_sse_line(line: str) -> dict[str, Any] | None:
    if not line.startswith("data:"):
        return None

    raw_data = line.removeprefix("data:").strip()
    if not raw_data or raw_data == "[DONE]":
        return None

    try:
        parsed = json.loads(raw_data)
    except json.JSONDecodeError:
        logger.warning("Google ADK SSE: invalid JSON line (truncated): %s", raw_data[:500])
        return None

    return parsed if isinstance(parsed, dict) else None


def google_adk_text_from_event(event: dict[str, Any]) -> str:
    content = event.get("content") or {}
    parts = content.get("parts") or []
    texts: list[str] = []

    if not isinstance(parts, list):
        return ""

    for part in parts:
        if isinstance(part, dict) and part.get("text"):
            texts.append(str(part["text"]))

    return "".join(texts).strip()


def final_text_from_google_adk_events(events: list[dict[str, Any]]) -> str:
    if not events:
        return ""

    return google_adk_text_from_event(events[-1])


def parse_json_object(text: str) -> dict[str, Any] | None:
    if not text or not text.strip():
        return None

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None

    return parsed if isinstance(parsed, dict) else None


def parse_last_json_object(text: str) -> dict[str, Any] | None:
    parsed = parse_json_object(text)
    if parsed is not None:
        return parsed

    decoder = json.JSONDecoder()
    last_object: dict[str, Any] | None = None
    last_end = -1
    for index, character in enumerate(text):
        if character != "{":
            continue
        try:
            candidate, end = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue

        absolute_end = index + end
        if isinstance(candidate, dict) and absolute_end > last_end:
            last_object = candidate
            last_end = absolute_end

    return last_object

