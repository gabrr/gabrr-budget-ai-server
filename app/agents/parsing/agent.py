"""Parsing agent definition using ADK.

Factory function to create a document parsing agent with
configurable model selection via the LLM adapter pattern.
"""

from google.adk.agents import Agent

from app.core.llm.interface import ModelId
from app.core.llm.openrouter import OpenRouterAdapter

from app.agents.tools.parsing import normalise, parse_csv, parse_pdf, parse_pdf_text

# Default model for parsing tasks
DEFAULT_MODEL = "openai:gpt-oss-120b:free"

# Agent instruction - allow tool choice as models improve
PARSING_INSTRUCTION = """You are a financial document parsing agent. Your task is to extract transaction data from uploaded files.

RULES:
1. Decide when to use tools. You have access to:
   - parse_csv(content_b64)
   - parse_pdf(content_b64)
   - parse_pdf_text(content_text)
   - normalise(transactions)

2. Use tools when helpful for extracting transactions instead of manual parsing.
   For example:
   - CSV: parse_csv -> normalise
   - PDF: parse_pdf (or parse_pdf_text if you have text) -> normalise

3. If the input payload includes "content_text", use parse_pdf_text(content_text)
   and do not call parse_pdf.

4. Return the transactions as a JSON object with this exact shape:
   {
     "transactions": [
       {
         "date": "YYYY-MM-DD" or null,
         "description": "string",
         "amount": number,
         "currency": "string" or null,
         "merchant_raw": "string" or null,
         "source": "csv" or "pdf"
       }
     ]
   }

5. Output ONLY the JSON object. No extra text, no commentary, no markdown formatting.

6. If parsing fails or no transactions are found, return:
   {"transactions": []}
"""


def _apply_structured_output(model: object) -> None:
    """Best-effort structured output configuration for JSON responses."""
    response_format = {"type": "json_object"}
    if hasattr(model, "model_params"):
        model_params = getattr(model, "model_params") or {}
        if isinstance(model_params, dict):
            model_params = {**model_params, "response_format": response_format}
            setattr(model, "model_params", model_params)
            return
    try:
        setattr(model, "response_format", response_format)
    except Exception:
        return


def create_parsing_agent(model_id: str = DEFAULT_MODEL) -> Agent:
    """Create a parsing agent with the specified model.

    Uses the OpenRouter adapter to support any provider:model format.

    Args:
        model_id: Model identifier in "provider:model" format.
            Examples: "openai:gpt-4o", "anthropic:claude-3.5-sonnet"

    Returns:
        Configured ADK Agent instance
    """
    adapter = OpenRouterAdapter()
    model = adapter.get_model(ModelId.from_string(model_id))

    _apply_structured_output(model)
    return Agent(
        name="parsing_agent",
        model=model,
        description="Parses financial documents (CSV/PDF) and extracts normalized transactions.",
        instruction=PARSING_INSTRUCTION,
        tools=[parse_csv, parse_pdf, parse_pdf_text, normalise],
    )


# Export for ADK CLI compatibility
root_agent = create_parsing_agent()
