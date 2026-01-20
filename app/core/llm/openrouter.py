"""OpenRouter adapter for model-agnostic LLM access.

Routes any provider:model specification through OpenRouter via LiteLlm.
"""

from google.adk.models.lite_llm import LiteLlm

from .interface import LLMProvider, ModelId


class OpenRouterAdapter(LLMProvider):
    """Adapter that routes any provider:model to OpenRouter via LiteLlm.

    OpenRouter provides a unified API for accessing models from multiple
    providers (OpenAI, Anthropic, Google, Meta, etc.) through a single
    API key and endpoint.
    """

    def get_model(self, model_id: ModelId) -> LiteLlm:
        """Create a LiteLlm instance for the given model via OpenRouter.

        Args:
            model_id: The model identifier in provider:model format

        Returns:
            A LiteLlm instance configured for OpenRouter
        """
        # OpenRouter format: openrouter/{provider}/{model}
        openrouter_model = f"openrouter/{model_id.provider}/{model_id.model}"
        return LiteLlm(model=openrouter_model)

    def list_models(self) -> list[ModelId]:
        """List commonly available models.

        Note: This is a static list for MVP. Could be extended to
        fetch dynamically from OpenRouter's API.

        Returns:
            List of popular ModelId instances
        """
        return [
            ModelId.from_string("openai:gpt-4o"),
            ModelId.from_string("openai:gpt-oss-120b:free"),
            ModelId.from_string("anthropic:claude-3.5-sonnet"),
            ModelId.from_string("google:gemini-2.0-flash"),
            ModelId.from_string("meta-llama:llama-3.1-70b-instruct"),
        ]
