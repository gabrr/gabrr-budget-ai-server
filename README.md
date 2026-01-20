# Gabrr Budget API

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-green)](https://fastapi.tiangolo.com/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-LLM-7c3aed)](https://openrouter.ai/)

Parse financial documents (CSV/PDF) into normalized transactions using AI agents. Upload a file, choose a model, and receive clean, structured transaction data.

## System Requirements

- Python 3.11+
- `uv` package manager (recommended)
- OpenRouter API key
- PDF parsing uses Docling; if PDF parsing fails due to system libs, see Docling install notes

## Quick Start (UV)

```bash
# Install uv (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Add OPENROUTER_API_KEY in .env

# Run the API
uv run uvicorn app.main:app --reload --port 8000 --env-file .env
```

## How It Works

- FastAPI receives an uploaded CSV or PDF.
- Google ADK runs a parsing agent with tool access.
- Tools extract raw transactions (CSV or PDF).
- Results are validated and returned in a strict schema.

## Why This Stack

- **Google ADK**: agent orchestration with structured tool calls.
- **LiteLLM**: model-agnostic interface.
- **OpenRouter**: access multiple providers with one key.
- **Docling**: reliable PDF table/text extraction.

## Usage

```bash
# Health check
curl http://localhost:8000/health

# Parse CSV (default model)
curl -X POST http://localhost:8000/parse \
  -F "file=@transactions.csv"

# Parse PDF with specific model
curl -X POST "http://localhost:8000/parse?model_id=anthropic:claude-3.5-sonnet" \
  -F "file=@statement.pdf"
```

## Response Shape

```json
[
  {
    "date": "2024-01-15",
    "description": "Coffee Shop Purchase",
    "amount": -4.50,
    "currency": "USD",
    "merchant_raw": "STARBUCKS #1234",
    "source": "csv"
  }
]
```

## Model ID Format

Models are specified as `provider:model`, for example:

- `openai:gpt-4o`
- `anthropic:claude-3.5-sonnet`
- `google:gemini-2.0-flash`

All models are accessed through OpenRouter, so you only need one API key.
