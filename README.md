# Gabrr Budget API

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


## Usage

```bash
# Health check
curl http://localhost:8000/health

# Parse CSV (default model)
curl -X POST http://localhost:8000/parse \
  -F "file=@transactions.csv"

# Parse PDF with specific model
curl -X POST "http://localhost:8000/parse" \
  -F "file=@statement.pdf"
```

## Testing

```bash
pytest

# Or via uv
uv run pytest
```