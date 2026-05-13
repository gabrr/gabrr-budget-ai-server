# Agentic testing (index)

Entry point for **Cursor / humans** for **agent-related** validation outside normal pytest.

- **Pytest:** [`make test`](../../README.md#testing) — collects `tests/` but **not** `tests/agents/` (agentic docs + run log only there).
- **This folder:** agentic index + run log only (no `test_*.py`). Use **`make test-agent-service`** for live AgentService checks.

## AgentService only (this repo)

| What | Where |
| --- | --- |
| **Implementation** | [`app/services/agent_service.py`](../../app/services/agent_service.py) |
| **HTTP surface** | [`app/api/agents_routes.py`](../../app/api/agents_routes.py) — `POST /agents/run` |
| **Single integration script** | [`scripts/agent_service/test_agent_service.sh`](../../scripts/agent_service/test_agent_service.sh) |
| **SSE digest helper** | [`scripts/agent_service/sse_digest_adk_stream.py`](../../scripts/agent_service/sse_digest_adk_stream.py) (used only by that script) |
| **Human run log** (appended) | [`agent_service_run_log.md`](agent_service_run_log.md) |

### What the AgentService test proves

1. **ADK** reachable (`make api` in **agent-normalizer** if not already up).
2. **Backend** up (`start-api` path in the same script if `/docs` is not 200).
3. **`POST /agents/run`** with **`mode: text`** — `create_session` + `run_text` (HTTP 200, JSON with `"text"`).
4. **`mode: json`** — `run_json` envelope (HTTP 200, `status` + `data`).
5. **`mode: sse`** — `stream_run_sse` opens stream (HTTP 200); digest summarizes each `data:` line.
6. **Validation** — empty `user_id` → **422**.

Up to **3** retries on the HTTP checks. Exit **0** only on full pass.

### Commands (from `backend/`)

```bash
make test                       # pytest: tests/ excluding tests/agents/
make test-agent-service         # live AgentService check (same as: bash scripts/agent_service/test_agent_service.sh run)
bash scripts/agent_service/test_agent_service.sh status
bash scripts/agent_service/test_agent_service.sh start-api
bash scripts/agent_service/test_agent_service.sh probe-adk
```

**Env:** `AGENT_NORMALIZER_ROOT`, `PORT`, `ADK_BASE_URL`, `AGENT_SERVICE_RUN_LOG` (override log path), `AGENT_SERVICE_API_LOG`, `SSE_MAX_TIME_SECS`, `SSE_HDR_LINES`, `SSE_DIGEST_MAX_BYTES`, `SSE_DIGEST_MAX_EVENTS`, `MAX_INTEGRATION_RETRIES`.

Scratch: `$TMPDIR/agent_service_test_scratch.md`.
