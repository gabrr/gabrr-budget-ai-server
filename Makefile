.PHONY: dev serve curl-smoke

PORT ?= 8000

DATABASE_URL_DEVTEST ?= postgresql+psycopg://postgres:postgres@localhost:5432/gabrr_budget_dev

dev:
	uv run uvicorn app.main:app --reload --port $(PORT) --env-file .env

# Run pytest against test DB (DATABASE_URL for app + tests). Exit 5 = no tests → treat as 0.
test-transactions:
	DATABASE_URL=$(DATABASE_URL_DEVTEST) uv run pytest tests/ -v; ret=$$?; if [ $$ret -eq 5 ]; then ret=0; fi; exit $$ret

curl-smoke:
	bash scripts/curl_smoke_transactions.sh
