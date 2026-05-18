from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal

AgentRunStatus = Literal["success", "error"]
AgentProgressCallback = Callable[["AgentProgressEvent"], Awaitable[None]]


@dataclass(frozen=True)
class AgentProgressEvent:
    code: str
    message: str


@dataclass(frozen=True)
class StatementImportResult:
    status: AgentRunStatus
    data: dict[str, Any]


def agent_error_result() -> StatementImportResult:
    return StatementImportResult(status="error", data={})


def agent_success_result(data: dict[str, Any]) -> StatementImportResult:
    return StatementImportResult(status="success", data=data)

