# Gabrr Budget API

Parse financial documents (CSV/PDF) into normalized transactions using AI agents. Upload a file, choose a model, and receive clean, structured transaction data.

## System Requirements

- Python 3.11+
- `uv` package manager (recommended)
- OpenRouter API key
- PDF parsing uses Docling; if PDF parsing fails due to system libs, see Docling install notes

## Quick Start

```bash
# Install uv (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run the API
make dev
```

## Testing

| Command | What it runs |
| --- | --- |
| **`make test`** | **pytest** on `tests/` with **`--ignore=tests/agents`** (that folder is agentic docs + logs only, not pytest). Uses **`DATABASE_URL_DEVTEST`** from the [Makefile](Makefile) unless you override it. |
| **`make test-agent-service`** | Live **AgentService** / ADK smoke (**not** pytest): [`scripts/test_agent_service/test_agent_service.sh`](scripts/test_agent_service/test_agent_service.sh). See [`tests/agents/AGENTIC_TESTING.md`](tests/agents/AGENTIC_TESTING.md). |

From **`backend/`**, **`make test`** runs:

```text
DATABASE_URL=<DATABASE_URL_DEVTEST> uv run pytest tests/ -v --ignore=tests/agents
```

Override the DB URL for one run:

```bash
make test DATABASE_URL_DEVTEST='postgresql+psycopg://user:pass@host:5432/dbname'
```

**Typical flow:** start Postgres, create DB, **`alembic upgrade head`**, copy **`.env.example`** → **`.env`**, then **`make test`**. Integration tests need data the API expects (e.g. **`accounts`** row for **`DEFAULT_ACCOUNT_ID`** when posting transactions).

```bash
make test
make test-agent-service   # requires agent-normalizer `make api` + API up; see AGENTIC_TESTING.md
```

