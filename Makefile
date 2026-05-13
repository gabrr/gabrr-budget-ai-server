.PHONY: dev serve curl-smoke test test-agent-service lint format

PORT ?= 8000

DATABASE_URL_DEVTEST ?= postgresql+psycopg://postgres:postgres@localhost:5432/gabrr_budget_dev

dev:
	uv run uvicorn app.main:app --reload --port $(PORT) --env-file .env

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix .

# Pytest: all tests under tests/, excluding tests/agents (agent-only docs / live checks — use `make test-agent-service`).
test:
	DATABASE_URL=$(DATABASE_URL_DEVTEST) uv run pytest tests/ -v --ignore=tests/agents; ret=$$?; if [ $$ret -eq 5 ]; then ret=0; fi; exit $$ret

curl-smoke:
	bash scripts/curl_smoke_transactions.sh

test-agent-service:
	bash scripts/test_agent_service/test_agent_service.sh run
