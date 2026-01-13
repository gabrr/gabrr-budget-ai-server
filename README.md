Gabrr Budget – Backend (MVP)
===========================

Gabrr Budget is a lightweight budgeting backend focused on one core problem:
extracting financial transactions from CSV and PDF statements and returning
clean, structured data that can later be categorised by users.

This repository contains the backend API and AI agents used for document
parsing. It is designed to be simple, vendor-agnostic, and easy to evolve.

---------------------------------------------------------------------------
Project Goals
---------------------------------------------------------------------------

- Accept CSV and text-based PDF financial statements
- Parse and normalise transactions into a consistent JSON format
- Use AI agents (Google ADK) to orchestrate parsing logic
- Keep humans in control of categorisation (no auto-categorisation)
- Provide a clean foundation that can later support workers, databases,
  authentication providers, and additional agents

This MVP intentionally avoids complexity. It proves the parsing pipeline end
to end.

---------------------------------------------------------------------------
What This MVP Does
---------------------------------------------------------------------------

- Exposes a single HTTP endpoint to upload a CSV or PDF
- Uses a Google ADK agent with tools to:
  - Parse CSV files using Python’s csv module
  - Parse text-based PDFs using Docling
  - Normalise extracted data into a strict schema
- Returns a JSON array of transactions

---------------------------------------------------------------------------
What This MVP Does NOT Do
---------------------------------------------------------------------------

- No database or persistence
- No authentication or user accounts
- No background workers or queues
- No OCR (scanned PDFs are not supported)
- No automatic categorisation or budgeting logic

---------------------------------------------------------------------------
Technology Stack
---------------------------------------------------------------------------

Backend:
- Python 3.12+
- FastAPI
- Google Agent Development Kit (ADK)
- Docling (PDF parsing)
- uv (dependency and environment management)

Runtime:
- In-process agents (FastAPI calls agents directly)
- No external agent hosting required

---------------------------------------------------------------------------
Requirements
---------------------------------------------------------------------------

- Python 3.12 or newer
- uv installed (https://github.com/astral-sh/uv)
- A supported LLM provider configured for Google ADK
- Text-based PDF statements (not scanned images)

---------------------------------------------------------------------------
Environment Variables
---------------------------------------------------------------------------

The application is configured using environment variables.

Common variables:

- APP_ENV=local
- MAX_UPLOAD_MB=10
- ADK_MODEL=<model identifier supported by ADK>
- Any additional credentials required by the chosen LLM provider

Create a .env file or export these variables in your shell.

---------------------------------------------------------------------------
Installation
---------------------------------------------------------------------------

1. Clone the repository
2. Initialise the project environment

   uv init
   uv venv --python 3.12
   uv add fastapi uvicorn python-multipart pydantic google-adk docling

3. Activate the environment (if not using uv run)

---------------------------------------------------------------------------
Running the Server
---------------------------------------------------------------------------

Start the API in development mode:

   uv run uvicorn app.main:app --reload

The API will be available at:
http://localhost:8000

---------------------------------------------------------------------------
API Usage
---------------------------------------------------------------------------

POST /parse

- Accepts a multipart file upload
- Supported formats: .csv, .pdf
- Returns a JSON array of normalised transactions

Each transaction includes:
- date
- description
- amount
- currency (optional)
- merchant_raw (optional)
- source (csv or pdf)

---------------------------------------------------------------------------
Error Handling
---------------------------------------------------------------------------

- Unsupported file types return HTTP 400
- Files exceeding MAX_UPLOAD_MB return HTTP 400
- Parsing failures return HTTP 400 with a short error message

---------------------------------------------------------------------------
Design Principles
---------------------------------------------------------------------------

- Vendor neutrality: providers are replaceable
- Human-in-the-loop by default
- Minimal surface area for the MVP
- Clear separation between API logic and agent logic
- Explicit non-goals to avoid accidental scope creep

---------------------------------------------------------------------------
Future Evolution (Out of Scope for MVP)
---------------------------------------------------------------------------

- Background workers for parsing
- Persistent storage (Postgres)
- User authentication and multi-tenancy
- Merchant enrichment and categorisation agents
- OCR support for scanned documents
- Budget summaries and analytics

---------------------------------------------------------------------------
License
---------------------------------------------------------------------------

Internal / private project. Licensing to be defined.
