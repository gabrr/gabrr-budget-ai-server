"""Agent HTTP helpers (ADK). Optional routes are gated in settings."""

from collections.abc import AsyncIterator
from typing import Literal

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.services.agent_service import AgentJsonRun, AgentService

agents_router = APIRouter(tags=["agents"])


class AgentRunIn(BaseModel):
    """One agent invocation: ADK user namespace, prompt, and response mode."""

    user_id: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    mode: Literal["text", "json", "sse"] = "text"


@agents_router.post("/run", response_model=None)
async def agent_run(
    payload: AgentRunIn,
) -> dict[str, str] | AgentJsonRun | StreamingResponse:
    timeout = httpx.Timeout(settings.adk_timeout_seconds)

    if payload.mode == "sse":

        async def sse_bytes() -> AsyncIterator[bytes]:
            async with httpx.AsyncClient(timeout=timeout) as client:
                agent_service = AgentService(
                    client,
                    base_url=settings.adk_base_url,
                    app_name=settings.adk_app_name,
                    user_id=payload.user_id,
                )
                adk_session_id = await agent_service.create_session()
                async for line in agent_service.stream_run_sse(
                    adk_session_id, payload.prompt
                ):
                    yield (line + "\n").encode("utf-8")

        return StreamingResponse(
            sse_bytes(),
            media_type="text/event-stream",
        )

    async with httpx.AsyncClient(timeout=timeout) as client:
        agent_service = AgentService(
            client,
            base_url=settings.adk_base_url,
            app_name=settings.adk_app_name,
            user_id=payload.user_id,
        )
        adk_session_id = await agent_service.create_session()

        if payload.mode == "text":
            text = await agent_service.run_text(adk_session_id, payload.prompt)
            return {"text": text}

        return await agent_service.run_json(adk_session_id, payload.prompt)
