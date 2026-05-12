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

# Run the API
make dev
```
