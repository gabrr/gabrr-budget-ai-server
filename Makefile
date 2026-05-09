.PHONY: dev

PORT ?= 8000

dev:
	uv run uvicorn app.main:app --reload --port $(PORT) --env-file .env
