from __future__ import annotations

from typing import Protocol

from app.agents.models import AgentProgressCallback, StatementImportResult


class AgentGateway(Protocol):
    async def extract_statement_transactions(
        self,
        file_path: str,
        *,
        user_id: str,
        on_progress: AgentProgressCallback | None = None,
    ) -> StatementImportResult:
        ...

