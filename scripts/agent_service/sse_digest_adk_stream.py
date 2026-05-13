"""Summarize ADK-style SSE lines (prefix `data: ` + JSON) for human-readable run logs."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _text_preview(parts: object, *, per_part: int = 120, total: int = 240) -> str:
    if not isinstance(parts, list):
        return ""
    chunks: list[str] = []
    thought_only = False
    for part in parts:
        if not isinstance(part, dict):
            continue
        if part.get("thoughtSignature") and not (part.get("text") or "").strip():
            thought_only = True
            continue
        text = part.get("text")
        if not isinstance(text, str) or not text.strip():
            continue
        t = text.strip().replace("\n", " ")
        if len(t) > per_part:
            t = t[: per_part - 1] + "…"
        chunks.append(t)
    if chunks:
        out = " ".join(chunks)
        if len(out) > total:
            return out[: total - 1] + "…"
        return out
    if thought_only:
        return "(thoughtSignature only, no text)"
    return ""


def digest_sse_body(path: Path, *, max_events: int = 30) -> None:
    if not path.is_file():
        print("(no body file)")
        return
    raw = path.read_bytes().decode("utf-8", errors="replace")
    event_index = 0
    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].lstrip()
        if not payload or payload == "[DONE]":
            continue
        event_index += 1
        if event_index > max_events:
            print(f"… ({max_events} events shown; rest omitted)")
            break
        try:
            obj = json.loads(payload)
        except json.JSONDecodeError:
            preview = payload[:100] + ("…" if len(payload) > 100 else "")
            print(f"event {event_index} | (invalid JSON) | {preview!r}")
            continue
        model_version = obj.get("modelVersion")
        mv = model_version if isinstance(model_version, str) else "?"
        partial = obj.get("partial")
        finish = obj.get("finishReason")
        fr = finish if isinstance(finish, str) else ("" if finish is None else str(finish))
        content = obj.get("content")
        parts = content.get("parts") if isinstance(content, dict) else None
        text_preview = _text_preview(parts)
        if not text_preview:
            text_preview = "(no text in parts)"
        print(
            f"event {event_index} | modelVersion={mv!r} | partial={partial!r} | "
            f"finishReason={fr!r} | text={text_preview!r}"
        )


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/e2e_sse_body.txt")
    max_events = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    digest_sse_body(path, max_events=max_events)


if __name__ == "__main__":
    main()
